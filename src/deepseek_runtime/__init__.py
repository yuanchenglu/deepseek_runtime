"""Public package exports for DeepSeek Runtime."""

from .client import DeepSeekClient, ProviderResult, RuntimeSettings
from .contracts import (
    ChangeJournalEntry,
    ContractViolation,
    ErrorCode,
    JournalFileRecord,
    OperatorAction,
    PublishableEvidence,
    ReceiptRequirement,
    RecoverableCheckpoint,
    RecoveryPolicy,
    RollbackHandle,
    RuntimeErrorInfo,
    RuntimeState,
    ToolArgumentError,
    ToolCallCheckpoint,
    ToolSpec,
    TransitionRule,
    transition_manifest,
    validate_transition,
)
from .diagnostics import build_diagnostics
from .observability import summarize_observability
from .runtime import DeepSeekRuntime, RuntimeResult, WorkspaceTools
from .security import (
    ChangeManager,
    ChangeSet,
    Decision,
    FileChange,
    PermissionPolicy,
    PermissionRequest,
    PermissionRule,
    Risk,
    RollbackToken,
    WorkspaceSandbox,
    content_sha256,
)
from .session import SessionState, resume_tool_calls
from .workspace import WorkspaceResolver, WorkspaceViolation

__version__ = "0.1.1a1"

__all__ = [
    "__version__",
    "ChangeJournalEntry",
    "ChangeManager",
    "ChangeSet",
    "ContractViolation",
    "DeepSeekClient",
    "DeepSeekRuntime",
    "Decision",
    "ErrorCode",
    "FileChange",
    "JournalFileRecord",
    "OperatorAction",
    "PermissionPolicy",
    "PermissionRequest",
    "PermissionRule",
    "ProviderResult",
    "PublishableEvidence",
    "ReceiptRequirement",
    "RecoverableCheckpoint",
    "RecoveryPolicy",
    "Risk",
    "RollbackHandle",
    "RollbackToken",
    "RuntimeErrorInfo",
    "RuntimeResult",
    "RuntimeSettings",
    "RuntimeState",
    "SessionState",
    "ToolArgumentError",
    "ToolCallCheckpoint",
    "ToolSpec",
    "TransitionRule",
    "WorkspaceResolver",
    "WorkspaceSandbox",
    "WorkspaceViolation",
    "WorkspaceTools",
    "build_diagnostics",
    "content_sha256",
    "resume_tool_calls",
    "summarize_observability",
    "transition_manifest",
    "validate_transition",
]
