"""Local stub-proxy attempt census (Sprint 6, Task 1).

Proves the relationship between SabiRoute execution attempts and HTTP
requests observed at a controlled local stub standing in for the LiteLLM
proxy: the REAL LiteLLMClient (not a double) is pointed at a localhost
HTTP server that counts every inbound request.

Safety: loopback only, ephemeral ports, no credentials, no external
network. The stub shuts down reliably via fixture teardown.

Explicitly NOT proven here: what a production LiteLLM proxy does
internally (its own retries/fallback are invisible to this boundary).
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

import pytest
from conftest import InMemoryApiKeyStore, make_config, provision_test_key
from fastapi.testclient import TestClient

from sabiroute.gateway import build_gateway_state
from sabiroute.main import create_app
from sabiroute.providers.litellm_client import LiteLLMClient

MESSAGES = [{"role": "user", "content": "hello"}]

SUCCESS_BODY = {
    "id": "chatcmpl-census",
    "model": "stub",
    "choices": [{"message": {"role": "assistant", "content": "ok"}}],
    "usage": {"prompt_tokens": 3, "completion_tokens": 2, "total_tokens": 5},
}


def _error_body(message: str) -> dict[str, Any]:
    return {"error": {"message": message, "type": "upstream_error"}}


class _ScriptedHandler(BaseHTTPRequestHandler):
    """Serves one scripted action per inbound POST, in order."""

    server_version = "CensusStub/1.0"

    def log_message(self, *args: object) -> None:
        pass

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw.decode("utf-8"))
        except ValueError:
            payload = None
        actions = self.server.script  # type: ignore[attr-defined]
        seen = self.server.seen  # type: ignore[attr-defined]
        action = actions[min(len(seen), len(actions) - 1)]
        model = payload.get("model") if isinstance(payload, dict) else None
        seen.append({"path": self.path, "model": model})
        kind = action[0]
        if kind == "hang":
            # Hold the connection open without replying until teardown:
            # the client must time out (not observe a close).
            self.server.hang_event.wait(timeout=30)  # type: ignore[attr-defined]
            return
        if kind == "reset":
            # Abrupt close: deterministic client-side transport failure.
            try:
                self.connection.shutdown(2)
            except OSError:
                pass
            self.connection.close()
            return
        if kind == "sse":
            frames = [
                b'data: {"choices":[{"delta":{"content":"hello"}}]}\n\n',
                b'data: {"choices":[{"delta":{"content":" world"}}]}\n\n',
                b'data: {"choices":[],"usage":{"prompt_tokens":3,'
                b'"completion_tokens":2,"total_tokens":5}}\n\n',
                b"data: [DONE]\n\n",
            ]
            encoded = b"".join(frames)
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)
            return
        status, body = action
        encoded = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


@pytest.fixture()
def stub_proxy():
    server = ThreadingHTTPServer(("127.0.0.1", 0), _ScriptedHandler)
    server.script = [(200, SUCCESS_BODY)]
    server.seen = []
    import threading as _threading

    server.hang_event = _threading.Event()
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.hang_event.set()
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


def _client_for(server: ThreadingHTTPServer, timeout_seconds: float = 120.0):
    port = server.server_address[1]
    client = LiteLLMClient(
        base_url=f"http://127.0.0.1:{port}", timeout_seconds=timeout_seconds
    )
    state = build_gateway_state(
        config=make_config(), client=client, key_store=InMemoryApiKeyStore()
    )
    key = provision_test_key(state)
    app = create_app(state=state)
    return TestClient(app, headers={"Authorization": f"Bearer {key}"}), state


def _event(state) -> Any:
    store = state.key_store
    assert isinstance(store, InMemoryApiKeyStore)
    return next(iter(store.usage_events.values()))


def test_success_single_attempt_single_request(stub_proxy) -> None:
    stub_proxy.script = [(200, SUCCESS_BODY)]
    client, state = _client_for(stub_proxy)

    response = client.post(
        "/v1/chat/completions",
        json={"model": "primary", "messages": MESSAGES},
    )

    assert response.status_code == 200
    assert len(stub_proxy.seen) == 1
    assert stub_proxy.seen[0]["path"] == "/v1/chat/completions"
    assert stub_proxy.seen[0]["model"] == "primary"
    event = _event(state)
    assert event.final_status == 200
    assert len(event.routing_decisions) == 1


def test_retryable_500_falls_back_with_matching_counts(stub_proxy) -> None:
    stub_proxy.script = [(500, _error_body("boom")), (200, SUCCESS_BODY)]
    client, state = _client_for(stub_proxy)

    response = client.post(
        "/v1/chat/completions",
        json={"model": "fast", "messages": MESSAGES},
    )

    assert response.status_code == 200
    assert [r["model"] for r in stub_proxy.seen] == ["primary", "secondary"]
    event = _event(state)
    assert [d["outcome"] for d in event.routing_decisions] == ["failure", "success"]
    assert len(stub_proxy.seen) == len(event.routing_decisions) == 2


def test_upstream_429_falls_back_with_matching_counts(stub_proxy) -> None:
    stub_proxy.script = [(429, _error_body("slow down")), (200, SUCCESS_BODY)]
    client, state = _client_for(stub_proxy)

    response = client.post(
        "/v1/chat/completions",
        json={"model": "fast", "messages": MESSAGES},
    )

    assert response.status_code == 200
    assert len(stub_proxy.seen) == 2
    event = _event(state)
    assert event.routing_decisions[0]["failure_category"] == "rate_limit"
    assert event.routing_decisions[1]["outcome"] == "success"


def test_transport_reset_retries_next_deployment(stub_proxy) -> None:
    stub_proxy.script = [("reset", None), (200, SUCCESS_BODY)]
    client, state = _client_for(stub_proxy)

    response = client.post(
        "/v1/chat/completions",
        json={"model": "fast", "messages": MESSAGES},
    )

    assert response.status_code == 200
    # Both inbound connections observed: the reset one and the success.
    assert len(stub_proxy.seen) == 2
    assert stub_proxy.seen[1]["model"] == "secondary"
    event = _event(state)
    assert [d["outcome"] for d in event.routing_decisions] == ["failure", "success"]
    assert event.routing_decisions[0]["failure_category"] == "transport"


def test_upstream_401_fails_over_per_documented_contract(stub_proxy) -> None:
    stub_proxy.script = [(401, _error_body("bad key")), (200, SUCCESS_BODY)]
    client, state = _client_for(stub_proxy)

    response = client.post(
        "/v1/chat/completions",
        json={"model": "fast", "messages": MESSAGES},
    )

    assert response.status_code == 200
    assert [r["model"] for r in stub_proxy.seen] == ["primary", "secondary"]
    event = _event(state)
    assert event.routing_decisions[0]["failure_category"] == "auth"
    assert event.routing_decisions[1]["outcome"] == "success"


def test_exhaustion_bounds_stub_requests_to_max_attempts(stub_proxy) -> None:
    stub_proxy.script = [(500, _error_body("down")), (500, _error_body("down"))]
    client, state = _client_for(stub_proxy)

    response = client.post(
        "/v1/chat/completions",
        json={"model": "fast", "messages": MESSAGES},
    )

    assert response.status_code == 502
    # fast policy: max_attempts == 2, so exactly two inbound requests.
    assert len(stub_proxy.seen) == 2
    event = _event(state)
    assert event.final_status == 502
    assert [d["outcome"] for d in event.routing_decisions] == ["failure", "failure"]


def test_streaming_success_single_request(stub_proxy) -> None:
    stub_proxy.script = [("sse", None)]
    client, state = _client_for(stub_proxy)

    response = client.post(
        "/v1/chat/completions",
        json={"model": "primary", "messages": MESSAGES, "stream": True},
    )

    assert response.status_code == 200
    assert response.text.count("[DONE]") == 1
    assert len(stub_proxy.seen) == 1
    assert stub_proxy.seen[0]["model"] == "primary"
    event = _event(state)
    assert event.final_status == 200
    assert len(event.routing_decisions) == 1
    assert event.routing_decisions[0]["outcome"] == "success"


def test_streaming_open_failure_falls_back_with_matching_counts(stub_proxy) -> None:
    stub_proxy.script = [(500, _error_body("open failed")), ("sse", None)]
    client, state = _client_for(stub_proxy)

    response = client.post(
        "/v1/chat/completions",
        json={"model": "fast", "messages": MESSAGES, "stream": True},
    )

    assert response.status_code == 200
    assert response.headers["X-SabiRoute-Deployment"] == "secondary"
    assert [r["model"] for r in stub_proxy.seen] == ["primary", "secondary"]
    event = _event(state)
    assert [d["outcome"] for d in event.routing_decisions] == ["failure", "success"]
    assert len(stub_proxy.seen) == len(event.routing_decisions) == 2


def test_error_category_distinguishes_timeout_from_transport() -> None:
    from sabiroute.api.completions import _error_category
    from sabiroute.providers.litellm_client import LiteLLMClientError

    assert (
        _error_category(LiteLLMClientError("timed out", timed_out=True)) == "timeout"
    )
    assert _error_category(LiteLLMClientError("reset", status_code=None)) == "transport"
    assert (
        _error_category(LiteLLMClientError("boom", status_code=500)) == "server"
    )


def test_hanging_upstream_times_out_with_bounded_attempts(stub_proxy) -> None:
    stub_proxy.script = [("hang", None)]
    client, state = _client_for(stub_proxy, timeout_seconds=0.5)

    response = client.post(
        "/v1/chat/completions",
        json={"model": "primary", "messages": MESSAGES},
    )

    assert response.status_code == 502
    # Single-alias request: the hung deployment is attempted once, excluded
    # as attempted, and there is nothing left to try. No retry storm.
    assert len(stub_proxy.seen) == 1
    event = _event(state)
    assert event.final_status == 502
    assert [d["outcome"] for d in event.routing_decisions] == ["failure"]
    assert event.routing_decisions[0]["failure_category"] == "timeout"
