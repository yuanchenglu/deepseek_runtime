"""
CLI 层（Command Line Interface）-- 怎么在终端中使用 Runtime？

❓ 问：普通用户怎么使用 DeepSeek Runtime？
💡 答：通过两个 CLI 命令--
   1. deepseek-runtime doctor --json
      检查本地环境是否正常（相当于"体检"）
   2. deepseek-runtime run "你的问题"
      运行一个 AI Agent 任务

M2-F CLI 输出协议：
- stdout：最终回答（纯文本）
- stderr：进度/警告（可关闭）
- --report path.json：安全证据写入文件
- --json：机器可读结果（安全模式）
- --unsafe-debug-content：明文调试，需要显式确认
- exit code：0=成功，1=运行失败，2=工作区错误，3=配置错误
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .client import DeepSeekClient, RuntimeSettings
from .contracts import ErrorCode, RuntimeErrorInfo
from .diagnostics import build_diagnostics
from .runtime import DeepSeekRuntime, RuntimeResult, WorkspaceTools

# 退出码常量
EXIT_OK = 0
EXIT_RUN_FAILED = 1
EXIT_WORKSPACE_INVALID = 2
EXIT_CONFIG_INVALID = 3


def _doctor(argv: list[str]) -> int:
    """
    "体检"命令：生成本地诊断报告。

    用法：deepseek-runtime doctor --json [--out path] [--evidence path] [--workspace path]
    """
    parser = argparse.ArgumentParser(
        prog="deepseek-runtime doctor",
        description="生成脱敏后的本地诊断报告",
    )
    parser.add_argument("--json", action="store_true", dest="json_output", help="以 JSON 格式输出诊断信息")
    parser.add_argument("--out", type=Path, help="把诊断结果写入指定文件")
    parser.add_argument("--evidence", type=Path, help="对指定 JSON/JSONL 文件中的路由/缓存/用量/成本证据做摘要")
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)

    if not args.json_output:
        parser.error("当前 doctor 只支持 --json 输出模式")

    bundle = build_diagnostics(args.workspace, args.evidence)
    text = json.dumps(bundle, ensure_ascii=False, indent=2) + "\n"

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")

    print(text, end="")
    return 0 if bundle["ok"] else 1


def _validate_workspace(workspace: Path) -> RuntimeErrorInfo | None:
    """检查工作区路径是否有效，返回错误或 None。"""
    if not workspace.exists():
        return RuntimeErrorInfo(
            code=ErrorCode.WORKSPACE_INVALID,
            message=f"workspace does not exist: {workspace}",
        )
    if workspace.is_file():
        return RuntimeErrorInfo(
            code=ErrorCode.WORKSPACE_INVALID,
            message=f"workspace path is a file, not a directory: {workspace}",
        )
    return None


def _run(argv: list[str]) -> int:
    """
    "运行"命令：执行一个 AI Agent 任务。

    M2-F 输出协议：
    - 默认：stdout 输出最终回答文本
    - --json：stdout 输出机器可读 JSON（安全模式，不含 prompt/response 原文）
    - --report path.json：安全证据写入指定文件
    - --unsafe-debug-content：包含 prompt/response 原文（危险，仅本地调试）
    """
    parser = argparse.ArgumentParser(
        prog="deepseek-runtime run",
        description="通过 DeepSeek 运行时执行一个 prompt",
    )
    parser.add_argument("prompt")
    parser.add_argument("--workspace", type=Path, default=Path.cwd())
    parser.add_argument("--no-tools", action="store_true")
    parser.add_argument("--json", action="store_true", dest="json_output", help="输出机器可读 JSON 结果")
    parser.add_argument("--report", type=Path, help="把安全证据写入指定文件")
    parser.add_argument(
        "--unsafe-debug-content",
        action="store_true",
        help="包含 prompt 和 response 原文（不安全，不适合日志或分享）",
    )
    args = parser.parse_args(argv)

    # CLI-006：workspace 不存在或为文件时友好失败
    ws_error = _validate_workspace(args.workspace)
    if ws_error is not None:
        print(f"error: {ws_error.message}", file=sys.stderr)
        if args.report:
            _write_report(args.report, RuntimeResult(
                ok=False,
                error=ws_error.message,
                error_class=ws_error.code.value,
            ))
        return EXIT_WORKSPACE_INVALID

    # CLI-004：--unsafe-debug-content 需要显式确认
    include_content = args.unsafe_debug_content
    if include_content:
        print("warning: --unsafe-debug-content is enabled; output will contain prompt and response text.", file=sys.stderr)

    try:
        settings = RuntimeSettings.from_env()
    except Exception as exc:
        # CLI-005：配置错误
        err = RuntimeErrorInfo(
            code=ErrorCode.CONFIG_INVALID,
            message=str(exc)[:512],
        )
        print(f"error: {err.message}", file=sys.stderr)
        if args.report:
            _write_report(args.report, RuntimeResult(
                ok=False,
                error=err.message,
                error_class=err.code.value,
            ))
        return EXIT_CONFIG_INVALID

    tools = None if args.no_tools else WorkspaceTools(args.workspace).catalog()

    try:
        runtime = DeepSeekRuntime(DeepSeekClient(settings))
        result = runtime.run(
            [{"role": "user", "content": args.prompt}],
            workspace=args.workspace,
            tools=tools,
        )
    except Exception as exc:
        result = RuntimeResult(
            ok=False,
            error=str(exc)[:512],
            error_class=type(exc).__name__,
        )

    # CLI-003：--report 写入安全证据文件
    if args.report:
        _write_report(args.report, result)

    # CLI-002：默认 stdout 输出最终回答；--json 输出机器可读结果
    if args.json_output:
        print(json.dumps(result.to_dict(include_content=include_content), ensure_ascii=False, indent=2))
    else:
        if result.ok and getattr(result, "final_text", ""):
            print(result.final_text)
        elif result.ok:
            print("(completed with no output)")
        else:
            # 失败时 stdout 不输出回答，错误信息到 stderr
            print(f"error: {result.error or 'unknown failure'}", file=sys.stderr)
            if result.error_class:
                print(f"error_code: {result.error_class}", file=sys.stderr)

    # CLI-005：exit code 与 error code 对应
    if result.ok:
        return EXIT_OK
    return EXIT_RUN_FAILED


def _write_report(path: Path, result: RuntimeResult) -> None:
    """把安全证据写入文件（不含 prompt/response 原文）。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(result.to_safe_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> None:
    """主入口：解析命令行参数，分发到对应的子命令。"""
    args_list = list(sys.argv[1:] if argv is None else argv)

    if args_list and args_list[0] == "doctor":
        raise SystemExit(_doctor(args_list[1:]))
    if args_list and args_list[0] == "run":
        raise SystemExit(_run(args_list[1:]))

    parser = argparse.ArgumentParser(description="DeepSeek-native Python runtime kernel")
    subcommands = parser.add_subparsers(dest="command")
    subcommands.add_parser("doctor", help="生成诊断报告")
    subcommands.add_parser("run", help="执行 prompt")
    parser.print_help()
    raise SystemExit(0)


if __name__ == "__main__":
    main()
