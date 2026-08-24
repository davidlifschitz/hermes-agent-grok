import json

import pytest
import pytest_asyncio
from aiohttp import web
from aiohttp.test_utils import TestServer
from gateway.config import PlatformConfig
from gateway.platforms.api_server import APIServerAdapter

from hermes_control_plane.runtime import (
    Capability,
    CapabilityError,
    HermesHttpRuntimeAdapter,
    HermesRuntimeError,
    RunHandle,
    RunRequest,
)


@pytest_asyncio.fixture
async def runtime_url():
    async def health(request):
        return web.json_response({"status": "ok", "platform": "hermes-agent"})

    async def start(request):
        assert request.headers["Authorization"] == "Bearer runtime-secret"
        body = await request.json()
        assert body == {"input": "do work", "instructions": "be concise", "session_id": "ses_1"}
        return web.json_response({"run_id": "run_1", "status": "started"}, status=202)

    async def events(request):
        assert request.match_info["run_id"] == "run_1"
        response = web.StreamResponse(headers={"Content-Type": "text/event-stream"})
        await response.prepare(request)
        payloads = [
            {"event": "tool.started", "run_id": "run_1", "tool": "search"},
            {"event": "message.delta", "run_id": "run_1", "delta": "done"},
            {
                "event": "run.completed",
                "run_id": "run_1",
                "output": "done",
                "usage": {"total_tokens": 3},
            },
        ]
        for payload in payloads:
            await response.write(f"data: {json.dumps(payload)}\n\n".encode())
        await response.write_eof()
        return response

    app = web.Application()
    app.router.add_get("/health", health)
    app.router.add_post("/v1/runs", start)
    app.router.add_get("/v1/runs/{run_id}/events", events)
    server = TestServer(app)
    await server.start_server()
    yield str(server.make_url("/")).rstrip("/")
    await server.close()


@pytest.mark.asyncio
async def test_programmatic_start_observe_result_lifecycle(runtime_url):
    adapter = HermesHttpRuntimeAdapter(runtime_url, api_key="runtime-secret")

    health = await adapter.probe()
    handle = await adapter.start_run(
        RunRequest(input="do work", instructions="be concise", session_id="ses_1")
    )
    result = await adapter.observe_run(handle)

    assert health["healthy"] is True
    assert handle.run_id == "run_1"
    assert handle.session_id == "ses_1"
    assert result.state == "completed"
    assert result.output == "done"
    assert result.usage == {"total_tokens": 3}
    assert [event.kind for event in result.events] == [
        "tool.started",
        "message.delta",
        "run.completed",
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("method", "capability", "args"),
    [
        ("get_run", Capability.DURABLE_STATUS, ("run_1",)),
        ("get_result", Capability.DURABLE_RESULT, ("run_1",)),
        ("continue_session", Capability.CONTINUE_SESSION, ("ses_1", "more")),
        ("cancel_run", Capability.CANCEL_RUN, ("run_1",)),
        ("respond_to_approval", Capability.APPROVALS, ("run_1", {"allow": True})),
    ],
)
async def test_unsupported_operations_fail_explicitly(runtime_url, method, capability, args):
    adapter = HermesHttpRuntimeAdapter(runtime_url)

    with pytest.raises(CapabilityError) as exc_info:
        await getattr(adapter, method)(*args)

    assert exc_info.value.code == "UNSUPPORTED_CAPABILITY"
    assert exc_info.value.capability is capability
    assert adapter.capabilities()[capability.value] is False


@pytest.mark.asyncio
async def test_terminal_failure_is_returned_as_failed_result():
    async def start(request):
        return web.json_response({"run_id": "run_failed", "status": "started"}, status=202)

    async def events(request):
        return web.Response(
            text='data: {"event":"run.failed","error":"provider unavailable"}\n\n',
            headers={"Content-Type": "text/event-stream"},
        )

    app = web.Application()
    app.router.add_post("/v1/runs", start)
    app.router.add_get("/v1/runs/{run_id}/events", events)
    server = TestServer(app)
    await server.start_server()
    try:
        adapter = HermesHttpRuntimeAdapter(str(server.make_url("/")).rstrip("/"))
        handle = await adapter.start_run(RunRequest(input="fail"))
        result = await adapter.observe_run(handle)
        assert result.state == "failed"
        assert result.error == "provider unavailable"
    finally:
        await server.close()


def test_remote_runtime_requires_secure_authenticated_transport():
    with pytest.raises(ValueError, match="Cleartext"):
        HermesHttpRuntimeAdapter("http://runtime.example")
    with pytest.raises(ValueError, match="API key"):
        HermesHttpRuntimeAdapter("https://runtime.example")


@pytest.mark.asyncio
async def test_non_object_sse_is_a_normalized_error():
    async def events(request):
        return web.Response(text="data: []\n\n", headers={"Content-Type": "text/event-stream"})

    app = web.Application()
    app.router.add_get("/v1/runs/{run_id}/events", events)
    server = TestServer(app)
    await server.start_server()
    try:
        adapter = HermesHttpRuntimeAdapter(str(server.make_url("/")).rstrip("/"))
        with pytest.raises(HermesRuntimeError, match="malformed SSE"):
            await adapter.observe_run(RunHandle("run_bad", "ses_bad", "started"))
    finally:
        await server.close()


@pytest.mark.asyncio
async def test_adapter_consumes_actual_gateway_run_handlers(monkeypatch, tmp_path):
    gateway = APIServerAdapter(
        PlatformConfig(extra={"key": "runtime-secret", "db_path": str(tmp_path / "responses.db")})
    )

    captured = {}

    class FakeAgent:
        session_prompt_tokens = 1
        session_completion_tokens = 2
        session_total_tokens = 3

        def __init__(self, stream_delta_callback, tool_progress_callback):
            self.stream_delta_callback = stream_delta_callback
            self.tool_progress_callback = tool_progress_callback

        def run_conversation(self, **kwargs):
            captured["conversation"] = kwargs
            self.tool_progress_callback("tool.started", tool_name="search", preview="query")
            self.stream_delta_callback("actual wire")
            self.tool_progress_callback("tool.completed", tool_name="search", duration=0.1)
            return {"final_response": "actual wire"}

    def create_agent(**kwargs):
        captured["agent"] = kwargs
        return FakeAgent(kwargs["stream_delta_callback"], kwargs["tool_progress_callback"])

    monkeypatch.setattr(gateway, "_create_agent", create_agent)
    app = web.Application()
    app.router.add_get("/health", gateway._handle_health)
    app.router.add_post("/v1/runs", gateway._handle_runs)
    app.router.add_get("/v1/runs/{run_id}/events", gateway._handle_run_events)
    server = TestServer(app)
    await server.start_server()
    try:
        adapter = HermesHttpRuntimeAdapter(
            str(server.make_url("/")).rstrip("/"), api_key="runtime-secret"
        )
        assert (await adapter.probe())["healthy"] is True
        handle = await adapter.start_run(
            RunRequest(input="exercise gateway", instructions="stay focused", session_id="ses_real")
        )
        result = await adapter.observe_run(handle)
        assert result.state == "completed"
        assert result.output == "actual wire"
        assert result.usage["total_tokens"] == 3
        assert "tool.started" in [event.kind for event in result.events]
        assert captured["agent"]["session_id"] == "ses_real"
        assert captured["agent"]["ephemeral_system_prompt"] == "stay focused"
        assert captured["conversation"] == {
            "user_message": "exercise gateway",
            "conversation_history": [],
        }
    finally:
        await gateway.cancel_background_tasks()
        gateway._response_store.close()
        await server.close()
