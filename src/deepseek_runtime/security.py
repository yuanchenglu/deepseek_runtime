"""
安全层（Security Layer）—— 本地 Agent 怎么保护自己？

❓ 问：AI Agent 在本地运行，它可能做什么危险的事？
💡 答：Agent 能读文件、写文件、执行命令。如果没有任何限制，它可能：
   - 读取你的密码文件（/etc/passwd）
   - 删除重要数据（rm -rf /）
   - 执行危险的 Git 操作（git push --force）
   - 访问外部网络（curl 恶意网站）

❓ 问：那 security.py 做了什么来防止这些？
💡 答：它定义了三个安全机制——
   1. WorkspaceSandbox（工作区沙箱）：把 Agent 限制在指定的目录内
   2. PermissionPolicy（权限策略）：对每种操作决定"允许/拒绝/询问"
   3. ChangeManager（变更管理器）：追踪文件修改，支持回滚

参考 llm-harness-agent 论文 A1（Agent Harness Survey）中 Harness 六组件的
"安全/沙箱"层：Agent 不能随意操作文件系统，必须经过权限检查。
"""

from __future__ import annotations

import base64
import difflib  # 生成文件差异对比（diff）
import fnmatch  # 文件名模式匹配（类似于 *.txt 的 glob 模式）
import hashlib  # 哈希计算
import os
import stat
import subprocess  # 执行系统命令
import tempfile  # 临时文件
import time
import uuid  # 唯一 ID
from dataclasses import dataclass, field
from enum import Enum  # 枚举类型（有限个选项）
from pathlib import Path
from typing import Callable, Sequence

from .change_journal import ChangeJournalStore, workspace_identity
from .contracts import (
    ChangeJournalEntry,
    ContractViolation,
    ErrorCode,
    JournalFileRecord,
    RollbackHandle,
    RuntimeErrorInfo,
)
from .workspace import WorkspaceResolver, WorkspaceViolation


# ===== Risk（风险等级）=====

# ❓ 问：为什么要把操作分类成不同风险？
# 💡 答：就像过马路要看红绿灯一样——
#   绿灯（READ）= 安全，可以直接走
#   黄灯（SHELL_SAFE）= 需要注意
#   红灯（DELETE/SHELL_DANGEROUS）= 必须停下来检查
#   分类的目的是让 Agent 和安全策略能快速判断每个操作的危险程度。

class Risk(str, Enum):
    """操作的风险分类——决定了安全策略该如何应对"""
    READ = "read"  # 只读操作（读文件）。最安全
    WRITE = "write"  # 写操作（修改文件）。中等风险
    DELETE = "delete"  # 删除操作。高风险——数据可能丢失
    SHELL_SAFE = "shell-safe"  # 相对安全的 shell 命令
    SHELL_DANGEROUS = "shell-dangerous"  # 危险 shell 命令（rm、sudo 等）
    NETWORK = "network"  # 网络操作（curl、wget 等）
    GIT_MUTATING = "git-mutating"  # 修改 Git 仓库（commit、push 等）


# ===== Decision（权限决策结果）=====

class Decision(str, Enum):
    """权限策略的三种决策结果"""
    ALLOW = "allow"  # 绿灯：允许执行
    ASK = "ask"  # 黄灯：询问用户意见
    DENY = "deny"  # 红灯：拒绝执行


# ===== PermissionRequest（权限请求）=====

@dataclass(frozen=True)
class PermissionRequest:
    """一次权限请求——包含了"谁想做什么"的信息"""
    risk: Risk  # 操作的风险等级
    path: str | None = None  # 操作涉及的文件路径
    command: tuple[str, ...] = ()  # 要执行的命令


# ===== PermissionRule（权限规则）=====

# ❓ 问：一条权限规则是怎么工作的？
# 💡 答：它把"什么条件下允许/拒绝/询问"编码成一条规则。
#   比如："对所有 WRITE 操作，如果是 docs/* 目录就 ASK，
#   其他目录就 DENY"。规则按顺序检查，第一条匹配的生效。

@dataclass(frozen=True)
class PermissionRule:
    """一条权限规则——定义了在什么条件下采取什么决策"""
    risk: Risk  # 匹配的风险类型
    decision: Decision  # 匹配后的决策
    path_glob: str = "*"  # 文件路径通配符（默认匹配所有）
    command_prefix: tuple[str, ...] = ()  # 命令前缀匹配

    def matches(self, request: PermissionRequest) -> bool:
        """判断这条规则是否匹配给定的请求"""
        if request.risk != self.risk:
            return False
        if request.path is not None and not fnmatch.fnmatch(request.path, self.path_glob):
            return False
        if self.command_prefix and request.command[:len(self.command_prefix)] != self.command_prefix:
            return False
        return True


# ===== 命令脱敏 =====

def _sanitize_command(command: Sequence[str]) -> list[str]:
    """
    脱敏命令中的敏感参数（如 API Key、密码等）
    例：curl --token sk-123 → curl --token [REDACTED]
    """
    sanitized: list[str] = []
    hide_next = False
    for argument in command:
        lower = argument.lower()
        if hide_next:
            sanitized.append("[REDACTED]")
            hide_next = False
        elif lower in {"--token", "--api-key", "--password", "-p"}:
            sanitized.append(argument)
            hide_next = True
        elif any(marker in lower for marker in ("api_key=", "token=", "password=", "authorization=")):
            sanitized.append("[REDACTED]")
        else:
            sanitized.append(argument)
    return sanitized


# ===== PermissionPolicy（权限策略）=====

@dataclass
class PermissionPolicy:
    """
    权限策略的执行者。默认拒绝所有非只读操作，
    通过 rules 列表逐个覆盖默认行为。
    参考 llm-harness-agent 论文 A5 中关于 Agent 治理（Governance）的讨论。
    """
    rules: list[PermissionRule] = field(default_factory=list)
    audit_events: list[dict[str, object]] = field(default_factory=list)

    def decide(self, request: PermissionRequest) -> Decision:
        """对一次权限请求做出决策，并记录审计日志"""
        decision = Decision.ALLOW if request.risk is Risk.READ else Decision.DENY
        for rule in self.rules:
            if rule.matches(request):
                decision = rule.decision
        self.audit_events.append({
            "event": "permission_decision",
            "timestamp_unix": int(time.time()),
            "risk": request.risk.value,
            "path": request.path,
            "command": _sanitize_command(request.command),
            "decision": decision.value,
        })
        return decision


# ===== 自定义异常 =====

class SandboxViolation(WorkspaceViolation):
    """路径越过了工作区边界"""
    pass

class PermissionDenied(PermissionError):
    """权限策略拒绝了操作"""
    pass


# ===== CommandResult（命令执行结果）=====

@dataclass(frozen=True)
class CommandResult:
    """命令执行的结果封装"""
    returncode: int  # 退出码（0=成功）
    stdout: str  # 标准输出
    stderr: str  # 错误输出
    truncated: bool  # 是否被截断


# ===== WorkspaceSandbox（工作区沙箱）=====

# ❓ 问：沙箱（Sandbox）在计算机里是什么意思？
# 💡 答：就像儿童玩的沙箱——你可以在沙箱里尽情玩，
#   但你不能跑出沙箱的范围。沙箱是一种隔离机制，
#   限制 Agent 能做什么、能去哪里。

class WorkspaceSandbox:
    """
    ❓ 问：WorkspaceSandbox 提供了哪些保护？
    💡 答：三个保护——
       1. 路径隔离（resolve()）：确保文件路径不会越界
       2. 命令分类（classify_command()）：判断命令的危险等级
       3. 命令执行（run()）：在沙箱内安全执行命令

    参考 llm-harness-agent 论文 C3: OpenHands ——
    沙箱化执行环境是 Harness 安全层的参考实现。
    """
    NETWORK_COMMANDS = {"curl", "wget", "nc", "ncat", "ssh", "scp", "sftp", "ftp", "telnet"}
    DANGEROUS_COMMANDS = {"rm", "dd", "mkfs", "mount", "umount", "shutdown", "reboot", "sudo", "su"}
    GIT_MUTATING = {
        "add", "am", "apply", "branch", "checkout", "cherry-pick",
        "clean", "commit", "merge", "mv", "rebase", "reset",
        "restore", "rm", "stash", "switch", "tag",
    }

    def __init__(self, root: Path, policy: PermissionPolicy | None = None):
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

    def classify_command(self, command: Sequence[str]) -> Risk:
        """根据可执行文件名判断命令的风险等级"""
        if not command:
            raise SandboxViolation("command must not be empty")
        executable = Path(command[0]).name
        if executable in self.NETWORK_COMMANDS:
            return Risk.NETWORK
        if executable in self.DANGEROUS_COMMANDS:
            return Risk.SHELL_DANGEROUS
        if executable == "git" and len(command) > 1 and command[1] in self.GIT_MUTATING:
            return Risk.GIT_MUTATING
        return Risk.SHELL_SAFE

    def run(
        self,
        command: Sequence[str],
        *,
        cwd: str | Path = ".",
        timeout: float = 30.0,
        max_output: int = 100_000,
    ) -> CommandResult:
        """在沙箱内安全执行命令（禁止字符串命令防注入）"""
        if isinstance(command, (str, bytes)):
            raise SandboxViolation("shell commands must be an argument array")
        normalized = tuple(str(item) for item in command)
        risk = self.classify_command(normalized)
        resolved_cwd = self.resolve(cwd)
        decision = self.policy.decide(
            PermissionRequest(risk=risk, path=self.relative(resolved_cwd), command=normalized)
        )
        if decision is not Decision.ALLOW:
            raise PermissionDenied(f"{risk.value} command requires {decision.value}")
        completed = subprocess.run(
            normalized, cwd=resolved_cwd, shell=False,
            capture_output=True, text=True, timeout=timeout, check=False,
        )
        stdout = completed.stdout
        stderr = completed.stderr
        truncated = len(stdout) + len(stderr) > max_output
        if truncated:
            remaining = max_output
            stdout = stdout[:remaining]
            remaining -= len(stdout)
            stderr = stderr[:max(0, remaining)]
        return CommandResult(completed.returncode, stdout, stderr, truncated)


# ===== content_sha256（文件内容哈希）=====

def content_sha256(content: bytes) -> str:
    """计算文件内容的 SHA-256 指纹，用于验证文件在修改前未被其他操作改动"""
    return hashlib.sha256(content).hexdigest()


# ===== FileChange / ChangeSet / RollbackToken =====

@dataclass(frozen=True)
class FileChange:
    """一次文件修改的描述：路径、修改前的哈希（验证用）、新内容"""
    path: str
    original_sha256: str | None  # None = 创建新文件
    new_content: str

@dataclass(frozen=True)
class ChangeSet:
    """一组原子化的文件修改。要么全部成功，要么全部回滚。"""
    changes: tuple[FileChange, ...]
    change_set_id: str = field(default_factory=lambda: uuid.uuid4().hex)

# Backward-compatible name only. The production authority is the opaque handle ID;
# callers cannot supply paths or original bytes.
RollbackToken = RollbackHandle


# ===== ChangeManager（变更管理器）=====

class ChangeManager:
    """文件变更管理器：预览 → 持久化 Journal → 应用 → 受约束回滚。"""

    def __init__(
        self,
        sandbox: WorkspaceSandbox,
        policy: PermissionPolicy | None = None,
        replace: Callable[[str | os.PathLike[str], str | os.PathLike[str]], None] = os.replace,
        journal_store: ChangeJournalStore | None = None,
        clock: Callable[[], float] = time.time,
        journal_ttl_seconds: int = 7 * 24 * 60 * 60,
    ):
        if journal_ttl_seconds <= 0:
            raise ValueError("journal_ttl_seconds must be positive")
        self.sandbox = sandbox
        self.policy = policy or sandbox.policy
        self.replace = replace
        self.clock = clock
        self.journal_ttl_seconds = journal_ttl_seconds
        self.workspace_id = workspace_identity(sandbox.root)
        self.journal_store = journal_store or ChangeJournalStore(clock=clock)
        self.journal_store.cleanup_expired()
        self.audit_events: list[dict[str, object]] = []

    @staticmethod
    def _contract_error(code: ErrorCode, message: str, **details: object) -> ContractViolation:
        return ContractViolation(RuntimeErrorInfo(code, message, details=details))

    def _current(self, path: Path) -> bytes | None:
        return path.read_bytes() if path.exists() else None

    @staticmethod
    def _mode(path: Path) -> int | None:
        try:
            return stat.S_IMODE(path.stat(follow_symlinks=False).st_mode)
        except FileNotFoundError:
            return None

    def _validate(self, change: FileChange) -> tuple[Path, bytes | None, int | None]:
        path = self.sandbox.resolve(change.path)
        current = self._current(path)
        if change.original_sha256 is None:
            if current is not None:
                raise ValueError(f"expected new file but path exists: {change.path}")
        elif current is None or content_sha256(current) != change.original_sha256:
            raise ValueError(f"stale original hash: {change.path}")
        decision = self.policy.decide(PermissionRequest(Risk.WRITE, self.sandbox.relative(path)))
        if decision is not Decision.ALLOW:
            raise PermissionDenied(f"write requires {decision.value}: {change.path}")
        return path, current, self._mode(path)

    def preview(self, change_set: ChangeSet) -> str:
        chunks: list[str] = []
        for change in change_set.changes:
            path = self.sandbox.resolve(change.path)
            current = self._current(path)
            before = (current or b"").decode("utf-8", errors="replace").splitlines(keepends=True)
            after = change.new_content.splitlines(keepends=True)
            chunks.extend(
                difflib.unified_diff(
                    before,
                    after,
                    fromfile=f"a/{change.path}",
                    tofile=f"b/{change.path}",
                )
            )
        return "".join(chunks)

    def _write_bytes(self, path: Path, content: bytes, mode: int | None = None, *, suffix: str = "") -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.{suffix}", dir=path.parent)
        temp = Path(temp_name)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            self.replace(temp, path)
            if mode is not None:
                try:
                    path.chmod(mode)
                except OSError:
                    pass
        finally:
            temp.unlink(missing_ok=True)

    def _restore_originals(self, originals: dict[Path, tuple[bytes | None, int | None]]) -> None:
        for path, (content, mode) in originals.items():
            if content is None:
                path.unlink(missing_ok=True)
            else:
                self._write_bytes(path, content, mode, suffix="rollback.")

    def apply(self, change_set: ChangeSet) -> RollbackHandle:
        """Persist private recovery state before applying a validated change set."""
        validated = [(*self._validate(change), change) for change in change_set.changes]
        handle = RollbackHandle.issue()
        now = int(self.clock())
        records = [
            JournalFileRecord(
                relative_path=self.sandbox.relative(path),
                original_sha256=content_sha256(current) if current is not None else None,
                post_sha256=content_sha256(change.new_content.encode("utf-8")),
                original_content_b64=(base64.b64encode(current).decode("ascii") if current is not None else None),
                original_mode=mode,
            )
            for path, current, mode, change in validated
        ]
        entry = ChangeJournalEntry(
            handle_id=handle.handle_id,
            workspace_id=self.workspace_id,
            change_set_id=change_set.change_set_id,
            files=records,
            created_at_unix=now,
            expires_at_unix=now + self.journal_ttl_seconds,
        )
        self.journal_store.save(entry)

        originals = {path: (current, mode) for path, current, mode, _ in validated}
        applied: list[Path] = []
        try:
            for path, _, mode, change in validated:
                self._write_bytes(path, change.new_content.encode("utf-8"), mode)
                applied.append(path)
            self.audit_events.append(
                {
                    "event": "changeset_applied",
                    "change_set_id": change_set.change_set_id,
                    "handle_id": handle.handle_id,
                    "paths": [self.sandbox.relative(path) for path in applied],
                }
            )
            return handle
        except Exception:
            self._restore_originals({path: originals[path] for path in applied})
            self.journal_store.delete(handle)
            self.audit_events.append(
                {
                    "event": "changeset_apply_failed_rolled_back",
                    "change_set_id": change_set.change_set_id,
                    "paths": [self.sandbox.relative(path) for path in applied],
                }
            )
            raise

    @staticmethod
    def _decode_original(record: JournalFileRecord) -> bytes | None:
        if record.original_sha256 is None:
            if record.original_content_b64 is not None:
                raise ValueError("new-file journal record contains original content")
            return None
        if record.original_content_b64 is None:
            raise ValueError("existing-file journal record lacks original content")
        value = base64.b64decode(record.original_content_b64.encode("ascii"), validate=True)
        if content_sha256(value) != record.original_sha256:
            raise ValueError("journal original content hash mismatch")
        return value

    def rollback(self, handle: RollbackHandle) -> None:
        """Resolve an opaque handle and restore only its protected journal entry."""
        try:
            entry = self.journal_store.load(handle)
        except ContractViolation:
            raise
        except Exception as exc:
            raise self._contract_error(
                ErrorCode.ROLLBACK_HANDLE_INVALID,
                "rollback handle cannot be resolved",
                cause_class=type(exc).__name__,
            ) from exc

        now = int(self.clock())
        if entry.consumed:
            raise self._contract_error(ErrorCode.ROLLBACK_HANDLE_INVALID, "rollback handle already consumed")
        if entry.expires_at_unix <= now:
            raise self._contract_error(ErrorCode.ROLLBACK_HANDLE_EXPIRED, "rollback handle expired")
        if entry.workspace_id != self.workspace_id:
            raise self._contract_error(
                ErrorCode.ROLLBACK_WORKSPACE_MISMATCH,
                "rollback handle belongs to a different workspace",
            )

        prepared: list[tuple[Path, bytes | None, int | None, str]] = []
        try:
            for record in entry.files:
                path = self.sandbox.resolve(record.relative_path)
                current = self._current(path)
                if current is None or content_sha256(current) != record.post_sha256:
                    raise self._contract_error(
                        ErrorCode.ROLLBACK_CONFLICT,
                        "workspace content changed after apply",
                        path=record.relative_path,
                    )
                decision = self.policy.decide(PermissionRequest(Risk.WRITE, record.relative_path))
                if decision is not Decision.ALLOW:
                    raise PermissionDenied(f"rollback write requires {decision.value}: {record.relative_path}")
                prepared.append((path, self._decode_original(record), record.original_mode, record.relative_path))
        except ContractViolation:
            raise
        except (ValueError, OSError) as exc:
            raise self._contract_error(
                ErrorCode.ROLLBACK_HANDLE_INVALID,
                "rollback journal entry is invalid",
                cause_class=type(exc).__name__,
            ) from exc

        restored: list[str] = []
        for path, original, mode, relative_path in prepared:
            if original is None:
                path.unlink(missing_ok=True)
            else:
                self._write_bytes(path, original, mode, suffix="rollback.")
            restored.append(relative_path)

        self.journal_store.mark_consumed(entry)
        object.__setattr__(handle, "consumed", True)
        self.audit_events.append(
            {
                "event": "changeset_rolled_back",
                "change_set_id": entry.change_set_id,
                "handle_id": handle.handle_id,
                "paths": restored,
            }
        )
