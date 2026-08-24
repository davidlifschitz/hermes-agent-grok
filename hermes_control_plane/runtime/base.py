"""Transport-neutral runtime types for the shared control plane."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from collections.abc import AsyncIterator
from typing import Any, Protocol


class Capability(StrEnum):
    START_RUN = "start_run"
    OBSERVE_RUN = "observe_run"
    DURABLE_STATUS = "durable_status"
    DURABLE_RESULT = "durable_result"
    CONTINUE_SESSION = "continue_session"
    CANCEL_RUN = "cancel_run"
    APPROVALS = "approvals"


class CapabilityError(RuntimeError):
    """Raised when a runtime cannot perform an advertised domain operation."""

    def __init__(self, capability: Capability, detail: str):
        self.capability = capability
        self.code = "UNSUPPORTED_CAPABILITY"
        super().__init__(f"{self.code}: {capability.value}: {detail}")


@dataclass(frozen=True)
class RunRequest:
    input: str
    instructions: str | None = None
    session_id: str | None = None


@dataclass(frozen=True)
class RunHandle:
    run_id: str
    session_id: str
    state: str


@dataclass(frozen=True)
class RunEvent:
    kind: str
    data: dict[str, Any]


@dataclass(frozen=True)
class RunResult:
    run_id: str
    session_id: str
    state: str
    output: str | None = None
    usage: dict[str, Any] = field(default_factory=dict)
    events: tuple[RunEvent, ...] = ()
    error: str | None = None


class RuntimeAdapter(Protocol):
    """Transport-neutral execution boundary consumed by the task service."""

    def capabilities(self) -> dict[str, bool]: ...
    async def probe(self) -> dict[str, Any]: ...
    async def start_run(self, request: RunRequest) -> RunHandle: ...
    def stream_events(self, handle: RunHandle) -> AsyncIterator[RunEvent]: ...
    async def get_run(self, run_id: str) -> RunHandle: ...
    async def get_result(self, run_id: str) -> RunResult: ...
    async def continue_session(self, session_id: str, instruction: str) -> None: ...
    async def cancel_run(self, run_id: str) -> None: ...
    async def respond_to_approval(self, run_id: str, approval: dict[str, Any]) -> None: ...
