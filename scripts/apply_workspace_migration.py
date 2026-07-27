from __future__ import annotations

from pathlib import Path


SECURITY_IMPORT = "from typing import Callable, Sequence\n"
SECURITY_IMPORT_REPLACEMENT = (
    "from typing import Callable, Sequence\n\n"
    "from .workspace import WorkspaceResolver, WorkspaceViolation\n"
)

SECURITY_EXCEPTION = '''class SandboxViolation(ValueError):
    """路径越过了工作区边界"""
    pass
'''
SECURITY_EXCEPTION_REPLACEMENT = '''class SandboxViolation(WorkspaceViolation):
    """路径越过了工作区边界"""
    pass
'''

SECURITY_RESOLVER = '''    def __init__(self, root: Path, policy: PermissionPolicy | None = None):
        """初始化沙箱：指定工作区根目录和权限策略"""
        self.root = root.resolve()
        self.policy = policy or PermissionPolicy()

    def resolve(self, raw: str | Path) -> Path:
        """将路径解析为绝对路径，并检查是否在沙箱内。越界则抛出异常。"""
        candidate = Path(raw)
        if not candidate.is_absolute():
            candidate = self.root / candidate
        if candidate.exists() or candidate.is_symlink():
            resolved = candidate.resolve()
        else:
            resolved = candidate.parent.resolve() / candidate.name
        if resolved != self.root and self.root not in resolved.parents:
            raise SandboxViolation(f"path escapes workspace: {raw}")
        return resolved

    def relative(self, path: Path) -> str:
        """返回相对于工作区的路径（用于审计日志，避免暴露绝对路径）"""
        return str(path.relative_to(self.root))
'''
SECURITY_RESOLVER_REPLACEMENT = '''    def __init__(self, root: Path, policy: PermissionPolicy | None = None):
        """初始化沙箱：指定工作区根目录和权限策略"""
        try:
            self._resolver = WorkspaceResolver(root)
        except WorkspaceViolation as exc:
            raise SandboxViolation(str(exc)) from exc
        self.root = self._resolver.root
        self.policy = policy or PermissionPolicy()

    def resolve(self, raw: str | Path) -> Path:
        """使用唯一 WorkspaceResolver 解析路径并拒绝链接/重解析点。"""
        try:
            return self._resolver.resolve(raw)
        except WorkspaceViolation as exc:
            raise SandboxViolation(str(exc)) from exc

    def relative(self, path: Path) -> str:
        """返回相对于工作区的 POSIX 路径，用于内容最小化审计。"""
        try:
            return self._resolver.relative(path)
        except WorkspaceViolation as exc:
            raise SandboxViolation(str(exc)) from exc
'''

RUNTIME_IMPORT = "from .evidence import redact, request_evidence, response_evidence, sha256_bytes, wire_json\n"
RUNTIME_IMPORT_REPLACEMENT = (
    "from .evidence import redact, request_evidence, response_evidence, sha256_bytes, wire_json\n"
    "from .workspace import WorkspaceResolver, WorkspaceViolation\n"
)

RUNTIME_TOOLS = '''@dataclass
class WorkspaceTools:
    """内置的工作区工具集——提供基本的文件读写和搜索能力"""
    root: str | Path

    def __post_init__(self) -> None:
        self.root = Path(self.root)

    def _path(self, raw: str) -> Path:
        """
        ❓ 问：_path() 做了哪些安全检查？
        💡 答：和 security.py 的 resolve() 类似——
           检查路径是否在工作区内，防止越界读取。
           这叫"路径遍历防护"（Path Traversal Prevention），
           是 Agent 安全的基础要求。
        """
        root = Path(self.root).resolve()
        candidate = (root / raw).resolve()
        if candidate != root and root not in candidate.parents:
            raise ValueError("path escapes workspace")
        return candidate

    def read_file(self, args: dict[str, Any]) -> str:
        """
        读取文件内容（最多 20000 字符）。
        工具名称叫 read_file，供 AI 调用。
        """
        # 从参数中提取 input 作为文件路径
        path = self._path(str(args.get("input", "")))
        return path.read_text(encoding="utf-8")[:20_000]

    def search(self, args: dict[str, Any]) -> str:
        """
        在工作区内搜索关键字（最多返回 100 条结果）。
        工具名称叫 search，供 AI 调用。
        """
        needle = str(args.get("input", ""))
        if not needle:
            raise ValueError("search input must not be empty")
        matches = []
        root = Path(self.root)
        for path in root.rglob("*"):
            if path.is_file() and ".git" not in path.parts and path.stat().st_size < 1_000_000:
                try:
                    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                        if needle in line:
                            matches.append(f"{path.relative_to(root)}:{number}:{line[:200]}")
                            if len(matches) >= 100:
                                return "\\n".join(matches)
                except (UnicodeDecodeError, OSError):
                    pass
        return "\\n".join(matches) or "No matches"

    def catalog(self) -> dict[str, ToolHandler]:
        """返回工具名称到处理函数的映射字典"""
        return {"read_file": self.read_file, "search": self.search}
'''
RUNTIME_TOOLS_REPLACEMENT = '''@dataclass
class WorkspaceTools:
    """内置工作区工具；所有路径和遍历均经过唯一 WorkspaceResolver。"""
    root: str | Path
    _resolver: WorkspaceResolver = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._resolver = WorkspaceResolver(self.root)
        self.root = self._resolver.root

    def _path(self, raw: str) -> Path:
        return self._resolver.resolve(raw)

    def read_file(self, args: dict[str, Any]) -> str:
        """读取普通工作区文件，最多返回 20000 个字符。"""
        return self._resolver.read_text(str(args.get("input", "")), max_chars=20_000)

    def search(self, args: dict[str, Any]) -> str:
        """不跟随 symlink/reparse-point 搜索普通文件，最多返回 100 条。"""
        needle = str(args.get("input", ""))
        if not needle:
            raise ValueError("search input must not be empty")
        matches: list[str] = []
        for path in self._resolver.iter_files():
            try:
                if path.stat(follow_symlinks=False).st_size >= 1_000_000:
                    continue
                content = self._resolver.read_text(path)
                for number, line in enumerate(content.splitlines(), 1):
                    if needle in line:
                        matches.append(f"{self._resolver.relative(path)}:{number}:{line[:200]}")
                        if len(matches) >= 100:
                            return "\\n".join(matches)
            except (UnicodeDecodeError, OSError, WorkspaceViolation):
                continue
        return "\\n".join(matches) or "No matches"

    def catalog(self) -> dict[str, ToolHandler]:
        """返回工具名称到处理函数的映射字典"""
        return {"read_file": self.read_file, "search": self.search}
'''

MINIMUM_CI = '''name: Minimum CI

on:
  push:
    branches: [develop]
  pull_request:
    branches: [develop, master]

permissions:
  contents: read

concurrency:
  group: minimum-ci-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  quality:
    name: Python 3.11 baseline
    runs-on: ubuntu-latest
    timeout-minutes: 15

    steps:
      - name: Check out repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
          show-progress: false

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: pip

      - name: Install package and M0 quality tools
        run: |
          python -m pip install --quiet --upgrade pip
          python -m pip install --quiet -e .
          python -m pip install --quiet ruff pyright

      - name: Critical lint
        run: python -m ruff check src tests scripts --select E9,F63,F7,F82

      - name: Collect basic type-check diagnostics
        id: pyright
        shell: bash
        run: |
          set +e
          pyright src/deepseek_runtime --pythonversion 3.11 --level error --outputjson > pyright.json
          status=$?
          echo "status=${status}" >> "$GITHUB_OUTPUT"
          cat pyright.json
          exit 0

      - name: Upload Pyright diagnostics
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: pyright-diagnostics
          path: pyright.json
          if-no-files-found: error
          retention-days: 7

      - name: Enforce basic type check
        if: steps.pyright.outputs.status != '0'
        run: exit 1

      - name: Existing unit tests
        run: python -m unittest discover -s tests -v

      - name: Package import smoke
        run: python -c "import deepseek_runtime; print(deepseek_runtime.__name__)"

      - name: Tracked secret scan
        run: python scripts/check_tracked_secrets.py

      - name: Documentation traceability and links
        run: python scripts/check_docs_traceability.py
'''


def replace_exact(path: str, before: str, after: str) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    if before not in text:
        raise RuntimeError(f"migration source block not found: {path}")
    target.write_text(text.replace(before, after, 1), encoding="utf-8")


def main() -> None:
    replace_exact("src/deepseek_runtime/security.py", SECURITY_IMPORT, SECURITY_IMPORT_REPLACEMENT)
    replace_exact("src/deepseek_runtime/security.py", SECURITY_EXCEPTION, SECURITY_EXCEPTION_REPLACEMENT)
    replace_exact("src/deepseek_runtime/security.py", SECURITY_RESOLVER, SECURITY_RESOLVER_REPLACEMENT)
    replace_exact("src/deepseek_runtime/runtime.py", RUNTIME_IMPORT, RUNTIME_IMPORT_REPLACEMENT)
    replace_exact("src/deepseek_runtime/runtime.py", RUNTIME_TOOLS, RUNTIME_TOOLS_REPLACEMENT)

    init_path = Path("src/deepseek_runtime/__init__.py")
    init_text = init_path.read_text(encoding="utf-8")
    init_text = init_text.replace(
        "from .session import SessionState, resume_tool_calls\n",
        "from .session import SessionState, resume_tool_calls\nfrom .workspace import WorkspaceResolver, WorkspaceViolation\n",
        1,
    )
    init_text = init_text.replace(
        '    "WorkspaceSandbox",\n',
        '    "WorkspaceResolver",\n    "WorkspaceSandbox",\n    "WorkspaceViolation",\n',
        1,
    )
    init_path.write_text(init_text, encoding="utf-8")

    Path(".github/workflows/minimum-ci.yml").write_text(MINIMUM_CI, encoding="utf-8")
    Path(".github/workflows/workspace-source-snapshot.yml").unlink(missing_ok=True)
    Path(__file__).unlink()


if __name__ == "__main__":
    main()
