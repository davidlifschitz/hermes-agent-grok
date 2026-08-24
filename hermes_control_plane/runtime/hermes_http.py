"""Adapter for Hermes gateway's evidence-backed HTTP/SSE run surface."""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from typing import Any
from urllib.parse import urlparse

import aiohttp

from .base import Capability, CapabilityError, RunEvent, RunHandle, RunRequest, RunResult


class HermesRuntimeError(RuntimeError):
    """Normalized failure while communicating with a Hermes runtime."""


class HermesHttpRuntimeAdapter:
    """Consume ``POST /v1/runs`` and its one-shot SSE event stream.

    This adapter deliberately does not pretend that the current Hermes gateway
    has durable run lookup, cancellation, approvals, or HTTP continuation.
    A control plane must consume and persist ``stream_events``; ``observe_run``
    is only a convenience collector for the protocol proof.
    """

    _CAPABILITIES = {
        Capability.START_RUN: True,
        Capability.OBSERVE_RUN: True,
        Capability.DURABLE_STATUS: False,
        Capability.DURABLE_RESULT: False,
        Capability.CONTINUE_SESSION: False,
        Capability.CANCEL_RUN: False,
        Capability.APPROVALS: False,
    }
    _MAX_EVENTS = 10_000
    _MAX_EVENT_BYTES = 1_000_000
    _MAX_RESPONSE_BYTES = 1_000_000

    def __init__(
        self,
        base_url: str,
        *,
        api_key: str | None = None,
        timeout_seconds: float = 300.0,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        parsed = urlparse(self._base_url)
        is_loopback = parsed.hostname in {"127.0.0.1", "::1", "localhost"}
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("Hermes runtime URL must be an absolute HTTP(S) URL")
        if parsed.scheme == "http" and not is_loopback:
            raise ValueError("Cleartext Hermes runtime URLs are allowed only on loopback")
        if not api_key and not is_loopback:
            raise ValueError("Remote Hermes runtimes require an API key")
        self._api_key = api_key
        self._timeout = aiohttp.ClientTimeout(total=timeout_seconds)
        self._session = session

    def capabilities(self) -> dict[str, bool]:
        return {capability.value: supported for capability, supported in self._CAPABILITIES.items()}

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._api_key}"} if self._api_key else {}

    async def probe(self) -> dict[str, Any]:
        """Verify reachability; capability flags remain adapter-version facts."""
        async for session in self._request_session():
            try:
                async with session.get(f"{self._base_url}/health") as response:
                    body = await self._json_or_text(response)
            except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
                raise HermesRuntimeError("Hermes runtime is unavailable") from exc
            if response.status != 200 or not isinstance(body, dict) or body.get("status") != "ok":
                raise HermesRuntimeError(f"Hermes health check failed ({response.status})")
            return {"healthy": True, "capabilities": self.capabilities()}
        raise AssertionError("unreachable")

    async def _request_session(self) -> AsyncIterator[aiohttp.ClientSession]:
        if self._session is not None:
            yield self._session
            return
        async with aiohttp.ClientSession(timeout=self._timeout) as session:
            yield session

    async def start_run(self, request: RunRequest) -> RunHandle:
        if not request.input.strip():
            raise ValueError("Run input must not be empty")
        payload: dict[str, Any] = {"input": request.input}
        if request.instructions is not None:
            payload["instructions"] = request.instructions
        if request.session_id is not None:
            payload["session_id"] = request.session_id

        try:
            async for session in self._request_session():
                async with session.post(
                    f"{self._base_url}/v1/runs", json=payload, headers=self._headers()
                ) as response:
                    body = await self._json_or_text(response)
                    if response.status != 202 or not isinstance(body, dict) or not body.get("run_id"):
                        raise HermesRuntimeError(f"start_run failed ({response.status}): {body}")
                    run_id = str(body["run_id"])
                    return RunHandle(
                        run_id=run_id,
                        session_id=request.session_id or run_id,
                        state=str(body.get("status", "started")),
                    )
        except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
            raise HermesRuntimeError("Hermes start request failed") from exc
        raise AssertionError("unreachable")

    async def observe_run(self, handle: RunHandle) -> RunResult:
        events: list[RunEvent] = []
        stream = self.stream_events(handle)
        try:
            async for event in stream:
                events.append(event)
                if event.kind == "run.completed":
                    return RunResult(
                        run_id=handle.run_id,
                        session_id=handle.session_id,
                        state="completed",
                        output=event.data.get("output"),
                        usage=event.data.get("usage") or {},
                        events=tuple(events),
                    )
                if event.kind == "run.failed":
                    return RunResult(
                        run_id=handle.run_id,
                        session_id=handle.session_id,
                        state="failed",
                        events=tuple(events),
                        error=str(event.data.get("error", "Hermes run failed")),
                    )
        finally:
            await stream.aclose()
        raise HermesRuntimeError("Hermes event stream ended without a terminal event")

    async def stream_events(self, handle: RunHandle) -> AsyncIterator[RunEvent]:
        """Yield the runtime's single-consumer SSE stream incrementally."""
        total_bytes = 0
        event_count = 0
        try:
            async for session in self._request_session():
                async with session.get(
                    f"{self._base_url}/v1/runs/{handle.run_id}/events", headers=self._headers()
                ) as response:
                    if response.status != 200:
                        body = await self._json_or_text(response)
                        raise HermesRuntimeError(f"observe_run failed ({response.status}): {body}")
                    async for raw_line in response.content:
                        total_bytes += len(raw_line)
                        if len(raw_line) > self._MAX_EVENT_BYTES or total_bytes > self._MAX_EVENT_BYTES:
                            raise HermesRuntimeError("Hermes event stream exceeded the size limit")
                        try:
                            line = raw_line.decode("utf-8").strip()
                            if not line.startswith("data:"):
                                continue
                            data = json.loads(line[5:].strip())
                            if not isinstance(data, dict):
                                raise ValueError("SSE payload is not an object")
                        except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
                            raise HermesRuntimeError("Hermes returned malformed SSE data") from exc
                        kind = str(data.get("event", "unknown"))
                        event_run_id = data.get("run_id")
                        if event_run_id is not None and event_run_id != handle.run_id:
                            raise HermesRuntimeError("Hermes event referenced a different run")
                        if kind == "run.completed":
                            if data.get("output") is not None and not isinstance(data["output"], str):
                                raise HermesRuntimeError("Hermes terminal output has an invalid type")
                            if data.get("usage") is not None and not isinstance(data["usage"], dict):
                                raise HermesRuntimeError("Hermes terminal usage has an invalid type")
                        event = RunEvent(kind=kind, data=data)
                        event_count += 1
                        if event_count > self._MAX_EVENTS:
                            raise HermesRuntimeError("Hermes event stream exceeded the event limit")
                        yield event
                        if kind in {"run.completed", "run.failed"}:
                            return
        except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
            raise HermesRuntimeError("Hermes event stream failed") from exc

    async def get_run(self, run_id: str) -> RunHandle:
        self._unsupported(Capability.DURABLE_STATUS, "Hermes exposes no GET run endpoint")

    async def get_result(self, run_id: str) -> RunResult:
        self._unsupported(Capability.DURABLE_RESULT, "result exists only in the terminal SSE event")

    async def continue_session(self, session_id: str, instruction: str) -> None:
        self._unsupported(Capability.CONTINUE_SESSION, "the run API has no verified continuation contract")

    async def cancel_run(self, run_id: str) -> None:
        self._unsupported(Capability.CANCEL_RUN, "the run API has no cancellation endpoint")

    async def respond_to_approval(self, run_id: str, approval: dict[str, Any]) -> None:
        self._unsupported(Capability.APPROVALS, "the HTTP runtime has no approval protocol")

    @staticmethod
    def _unsupported(capability: Capability, detail: str) -> None:
        raise CapabilityError(capability, detail)

    @classmethod
    async def _json_or_text(cls, response: aiohttp.ClientResponse) -> Any:
        raw = await response.content.read(cls._MAX_RESPONSE_BYTES + 1)
        if len(raw) > cls._MAX_RESPONSE_BYTES:
            raise HermesRuntimeError("Hermes response exceeded the size limit")
        text = raw.decode(response.charset or "utf-8", errors="replace")
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text
