"""Entry-point and construction paths that only unusual environments reach.

Three of these are the degraded branches: a deployment whose working directory
has no static UI, a gateway whose store executor cannot run the session purge,
and a gateway configured from ``REDIS_URL`` rather than a host and port. The
fourth is the console-script hand-off to uvicorn.
"""
from __future__ import annotations

import pathlib
from types import SimpleNamespace

import pytest
from conftest import make_config
from fastapi.testclient import TestClient

import sabiroute.gateway as gateway_module
import sabiroute.main as main_module
from sabiroute.security.rate_limit import RedisTokenBucket


def test_web_dir_returns_none_when_no_candidate_directory_exists(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("SABIROUTE_WEB_DIR", raising=False)
    monkeypatch.setattr(pathlib.Path, "is_dir", lambda self: False)

    assert main_module._web_dir() is None


def test_startup_purges_sessions_without_an_executor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    purges: list[bool] = []

    class _Store:
        def purge_expired_sessions(self) -> None:
            purges.append(True)

    state = SimpleNamespace(key_store=None, chat_store=_Store(), store_executor=None)

    with TestClient(main_module.create_app(state)):
        pass

    assert purges == [True, True]


def test_cli_entry_point_delegates_to_uvicorn(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def fake_run(target: str, **kwargs: object) -> None:
        captured["target"] = target
        captured["kwargs"] = kwargs

    import uvicorn

    monkeypatch.setattr(uvicorn, "run", fake_run)
    monkeypatch.setenv("SABIROUTE_HOST", "0.0.0.0")
    monkeypatch.setenv("SABIROUTE_API_PORT", "9000")

    main_module.main([])

    assert captured["target"] == "sabiroute.main:app"
    assert captured["kwargs"] == {"host": "0.0.0.0", "port": 9000}


def test_redis_url_configures_the_rate_limiter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, dict[str, object]]] = []
    sentinel = object()

    def fake_from_url(url: str, **kwargs: object) -> object:
        calls.append((url, kwargs))
        return sentinel

    monkeypatch.setattr(
        gateway_module.Redis, "from_url", staticmethod(fake_from_url)
    )
    monkeypatch.setenv("REDIS_URL", "redis://cache.internal:6379/1")

    state = gateway_module.build_gateway_state(
        config=make_config(), key_store=object()
    )

    assert calls == [("redis://cache.internal:6379/1", {"decode_responses": True})]
    assert isinstance(state.rate_limiter, RedisTokenBucket)
