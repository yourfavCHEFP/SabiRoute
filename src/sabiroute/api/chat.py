"""SabiChat backend: auth, sessions, conversations, gateway chat.

Design notes (read before extending):

- Authentication uses opaque bearer session tokens (``secrets.token_urlsafe``,
  SHA-256 digest persisted, 7-day absolute expiry, revocation on logout).
  Bearer headers were chosen over cookies to match the existing API's
  ``Authorization: Bearer`` conventions and to avoid a CSRF surface entirely;
  there are no cookies, so cookie-attribute weakening cannot happen. The
  client must keep the token in memory and never place it in URLs. Token
  plaintext is returned once, at login/registration, and never again.
- The chat endpoint never calls LiteLLM. It calls the gateway's own
  ``POST /v1/chat/completions`` in-process (ASGI transport) with a
  server-held service key, forcing ``sabi_route_free_chat: True`` itself and
  dropping any client-supplied marker/usage-source fields (the request model
  ignores unknown fields). Policy, budgets, Free Pool eligibility, and usage
  accounting therefore apply unchanged; per-request attribution is
  ``free_pool`` on allow, ``unknown`` otherwise.
- The service key is provisioned once via the existing ``issue_api_key`` and
  cached only in process memory (never in the database, never in a response).
  A restart mints a fresh key; superseded rows are retained, not deleted.
  Per-user gateway keys and quotas are an explicit future gap, not smuggled
  in here: every chat request is Free-Chat-gated, so no unlimited access.
- Auth/chat rate limits are in-process fixed windows (single-process
  semantics, documented). Redis-backed global limiting is a Sprint 5 concern.
"""

from __future__ import annotations

import asyncio
import re
import secrets
import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, Field

from ..chat.passwords import (
    PasswordPolicyError,
    dummy_verify,
    hash_password,
    validate_password_shape,
    verify_password,
)
from ..chat.store import (
    DuplicateEmailError,
    SabiChatConversation,
    SabiChatSession,
    SabiChatStore,
    SabiChatUser,
    digest_token,
)
from ..freepool.eligibility import FREE_CHAT_MARKER
from ..gateway import GatewayState
from ..quotas import quota_reset_at, quota_window_start
from ..security.keys import SABI_USER_ID_FIELD, issue_api_key

router = APIRouter(tags=["sabichat"])

_bearer = HTTPBearer(auto_error=False)
_bearer_dependency = Depends(_bearer)


SESSION_TTL = timedelta(days=7)
MAX_CONTENT_CHARS = 8000
MAX_TITLE_CHARS = 120
MAX_MODEL_CHARS = 256
HISTORY_WINDOW = 20
GATEWAY_MAX_TOKENS = 1024
INTERNAL_TIMEOUT_SECONDS = 120.0
AUTH_LIMIT_PER_MINUTE = 10
CHAT_LIMIT_PER_MINUTE = 60

_EMAIL_PATTERN = re.compile(r"^[^@\s]{1,200}@[^@\s]{1,200}\.[^@\s]{1,20}$")


class ChatServiceUnavailable(RuntimeError):
    """The chat backend has no usable store or service credential."""


class ChatUpstreamTimeout(RuntimeError):
    """The in-process gateway call timed out."""


class ChatUpstreamTransport(RuntimeError):
    """The in-process gateway call failed before responding."""


class FixedWindowLimiter:
    """In-process fixed-window rate limiter (single-process semantics).

    Adequate for sign-in/chat abuse brakes on one host. It is not shared
    across processes or restarts; global limiting belongs in Sprint 5.
    """

    def __init__(self, max_requests: int, window_seconds: float) -> None:
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._hits: dict[str, list[float]] = {}

    def check(self, key: str) -> float | None:
        """Return None when admitted, else retry-after seconds."""
        now = time.monotonic()
        cutoff = now - self._window_seconds
        hits = [moment for moment in self._hits.get(key, []) if moment > cutoff]
        if len(hits) >= self._max_requests:
            oldest = min(hits)
            self._hits[key] = hits
            return max(0.0, oldest + self._window_seconds - now)
        hits.append(now)
        self._hits[key] = hits
        return None


@dataclass
class ChatSessionContext:
    """Authenticated request identity: user plus the session that proved it."""

    user: SabiChatUser
    session: SabiChatSession


class SabiChatService:
    """Per-application chat helper: limits, service key, gateway calls."""

    def __init__(self, state: GatewayState) -> None:
        self._state = state
        self._key_lock = asyncio.Lock()
        self._service_key_id: str | None = None
        self._service_plaintext: str | None = None
        self.auth_limiter = FixedWindowLimiter(AUTH_LIMIT_PER_MINUTE, 60.0)
        self.chat_limiter = FixedWindowLimiter(CHAT_LIMIT_PER_MINUTE, 60.0)

    async def service_headers(self) -> dict[str, str]:
        """Bearer headers for the server-held gateway service key.

        Provisioned once via the existing key issuance and cached only in
        memory. Raises ``ChatServiceUnavailable`` when no key store exists.
        """
        if self._service_plaintext is not None:
            return {"Authorization": f"Bearer {self._service_plaintext}"}
        store = self._state.key_store
        if store is None:
            raise ChatServiceUnavailable("Request accounting is unavailable.")
        async with self._key_lock:
            if self._service_plaintext is not None:
                return {"Authorization": f"Bearer {self._service_plaintext}"}
            record, plaintext = await self._state.store_executor.run(
                issue_api_key,
                store,
                project_id="sabichat-service",
                name="sabichat-service",
            )
            self._service_key_id = record.key_id
            self._service_plaintext = plaintext
            # Publish the service key's identity so the gateway can recognize
            # its own credential for trusted identity establishment. Key IDs
            # are non-secret identifiers; the plaintext never leaves memory.
            self._state.sabichat_service_key_id = record.key_id
            return {"Authorization": f"Bearer {plaintext}"}

    async def complete(
        self,
        app: Any,
        model: str,
        messages: list[dict[str, Any]],
        *,
        user_id: str,
    ) -> tuple[int, dict[str, str], str | None, dict[str, Any]]:
        """Call the gateway completions path in-process as Free Chat.

        Returns ``(status_code, headers, deployment_header, body)``. The Free
        Chat marker and the canonical user ID are set server-side from the
        validated session; the caller cannot influence either. Headers are
        the gateway response headers (notably ``Retry-After`` on quota
        exhaustion) so the chat wrapper can propagate them.
        """
        headers = await self.service_headers()
        payload = {
            "model": model,
            "messages": messages,
            FREE_CHAT_MARKER: True,
            SABI_USER_ID_FIELD: user_id,
            "max_tokens": GATEWAY_MAX_TOKENS,
        }
        transport = httpx.ASGITransport(app=app)
        try:
            async with httpx.AsyncClient(
                transport=transport,
                base_url="http://sabichat-internal",
                timeout=httpx.Timeout(INTERNAL_TIMEOUT_SECONDS),
            ) as client:
                response = await client.post(
                    "/v1/chat/completions", json=payload, headers=headers
                )
        except httpx.TimeoutException as exc:
            raise ChatUpstreamTimeout("Gateway request timed out.") from exc
        except httpx.HTTPError as exc:
            raise ChatUpstreamTransport("Gateway request failed.") from exc
        try:
            body = response.json()
        except ValueError:
            body = {}
        if not isinstance(body, dict):
            body = {}
        return (
            response.status_code,
            dict(response.headers),
            response.headers.get("X-SabiRoute-Deployment"),
            body,
        )


def _service(request: Request) -> SabiChatService:
    service = getattr(request.app.state, "sabichat", None)
    if not isinstance(service, SabiChatService):
        service = SabiChatService(request.app.state.gateway)
        request.app.state.sabichat = service
    return service


def _chat_store(request: Request) -> SabiChatStore:
    state = getattr(request.app.state, "gateway", None)
    store = getattr(state, "chat_store", None)
    if not isinstance(store, SabiChatStore):
        raise HTTPException(
            status_code=503,
            detail={"error": {"message": "Chat is unavailable.", "type": "chat_unavailable"}},
        )
    return store


def _executor(request: Request):  # type: ignore[no-untyped-def]
    return request.app.state.gateway.store_executor


def _password_executor(request: Request):  # type: ignore[no-untyped-def]
    """CPU-bound PBKDF2 hashing must never occupy database executor slots."""
    return request.app.state.gateway.password_executor


def _normalize_email(raw: str) -> str:
    email = (raw or "").strip().lower()
    if len(email) > 320 or _EMAIL_PATTERN.match(email) is None:
        raise HTTPException(
            status_code=400,
            detail={"error": {"message": "Invalid email address.", "type": "invalid_email"}},
        )
    return email


def _rate_limited_response(retry_after: float) -> HTTPException:
    return HTTPException(
        status_code=429,
        detail={"error": {"message": "Too many attempts.", "type": "rate_limit_exceeded"}},
        headers={"Retry-After": str(max(1, int(retry_after) + 1))},
    )


def _invalid_credentials() -> HTTPException:
    # Generic on purpose: identical for unknown emails, wrong passwords, and
    # disabled accounts, so responses do not reveal which accounts exist.
    return HTTPException(
        status_code=401,
        detail={
            "error": {"message": "Invalid email or password.", "type": "invalid_credentials"}
        },
        headers={"WWW-Authenticate": "Bearer"},
    )


def _unauthorized_session() -> HTTPException:
    return HTTPException(
        status_code=401,
        detail={"error": {"message": "Invalid session.", "type": "invalid_session"}},
        headers={"WWW-Authenticate": "Bearer"},
    )


async def require_chat_session(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = _bearer_dependency,
) -> ChatSessionContext:
    """Validate a session bearer token against server-side session state."""
    if (
        credentials is None
        or credentials.scheme.lower() != "bearer"
        or not credentials.credentials
    ):
        raise _unauthorized_session()
    store = _chat_store(request)
    token_hash = digest_token(credentials.credentials)
    session = await _executor(request).run(store.get_session, token_hash)
    if session is None or session.revoked_at is not None:
        raise _unauthorized_session()
    if session.expires_at <= datetime.now(UTC):
        raise _unauthorized_session()
    user = await _executor(request).run(store.get_user, session.user_id)
    if user is None or user.disabled_at is not None:
        raise _unauthorized_session()
    return ChatSessionContext(user=user, session=session)


# Module singleton like _bearer_dependency: B008 forbids Depends() calls in
# argument defaults, so endpoints share this instead of calling Depends().
_chat_session_dependency = Depends(require_chat_session)


def _user_payload(user: SabiChatUser) -> dict[str, Any]:
    return {
        "user_id": user.user_id,
        "email": user.email,
        "created_at": user.created_at.isoformat(),
    }


def _session_payload(user: SabiChatUser, token: str, expires_at: datetime) -> dict[str, Any]:
    return {**_user_payload(user), "token": token, "expires_at": expires_at.isoformat()}


def _conversation_payload(
    conversation: SabiChatConversation, messages: list[dict[str, Any]] | None = None
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "conversation_id": conversation.conversation_id,
        "title": conversation.title,
        "created_at": conversation.created_at.isoformat(),
        "updated_at": conversation.updated_at.isoformat(),
    }
    if messages is not None:
        payload["messages"] = messages
    return payload


def _message_payload(
    message_id: str,
    role: str,
    content: str,
    model: str | None,
    deployment: str | None,
    error_type: str | None,
    created_at: Any,
) -> dict[str, Any]:
    return {
        "message_id": message_id,
        "role": role,
        "content": content,
        "model": model,
        "deployment": deployment,
        "error_type": error_type,
        "created_at": created_at.isoformat() if hasattr(created_at, "isoformat") else created_at,
    }


class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=1024)


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=1024)


class CreateConversationRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")

    title: str | None = Field(default=None, max_length=MAX_TITLE_CHARS)


class PostMessageRequest(BaseModel):
    # Unknown fields are ignored: a client-supplied Free Chat marker or
    # usage-source label can never reach the gateway call.
    model_config = ConfigDict(extra="ignore")

    content: str = Field(min_length=1, max_length=MAX_CONTENT_CHARS)
    model: str | None = Field(default=None, max_length=MAX_MODEL_CHARS)


def _client_ip(request: Request) -> str:
    client = request.client
    return client.host if client is not None else "unknown"


@router.post("/v1/auth/register", status_code=201)
async def register(payload: RegisterRequest, request: Request) -> dict[str, Any]:
    service = _service(request)
    store = _chat_store(request)
    retry_after = service.auth_limiter.check(f"auth:{_client_ip(request)}")
    if retry_after is not None:
        raise _rate_limited_response(retry_after)
    email = _normalize_email(payload.email)
    try:
        validate_password_shape(payload.password)
    except PasswordPolicyError as exc:
        raise HTTPException(
            status_code=400,
            detail={"error": {"message": str(exc), "type": "invalid_password"}},
        ) from exc
    try:
        password_hash = await _password_executor(request).run(hash_password, payload.password)
        user = await _executor(request).run(store.create_user, email, password_hash)
    except DuplicateEmailError:
        # Generic on purpose: same vague shape as validation failures, so
        # registration does not confirm whether an email is taken.
        raise HTTPException(
            status_code=400,
            detail={
                "error": {
                    "message": "Could not complete registration.",
                    "type": "registration_failed",
                }
            },
        ) from None
    return await _issue_session_response(request, store, user)


@router.post("/v1/auth/login")
async def login(payload: LoginRequest, request: Request) -> dict[str, Any]:
    service = _service(request)
    store = _chat_store(request)
    retry_after = service.auth_limiter.check(f"auth:{_client_ip(request)}")
    if retry_after is not None:
        raise _rate_limited_response(retry_after)
    email = _normalize_email(payload.email)
    user = await _executor(request).run(store.get_user_by_email, email)
    if user is None or user.disabled_at is not None:
        await _password_executor(request).run(dummy_verify, payload.password)
        raise _invalid_credentials()
    valid = await _password_executor(request).run(
        verify_password, payload.password, user.password_hash
    )
    if not valid:
        raise _invalid_credentials()
    return await _issue_session_response(request, store, user)


async def _issue_session_response(
    request: Request, store: SabiChatStore, user: SabiChatUser
) -> dict[str, Any]:
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(UTC) + SESSION_TTL
    await _executor(request).run(
        store.create_session, user.user_id, digest_token(token), expires_at
    )
    return _session_payload(user, token, expires_at)


@router.post("/v1/auth/logout")
async def logout(
    request: Request, context: ChatSessionContext = _chat_session_dependency
) -> dict[str, Any]:
    store = _chat_store(request)
    await _executor(request).run(store.revoke_session, context.session.session_id)
    return {"signed_out": True}


@router.get("/v1/auth/me")
async def me(context: ChatSessionContext = _chat_session_dependency) -> dict[str, Any]:
    return _user_payload(context.user)


@router.get("/v1/chat/quota-summary")
async def quota_summary(
    request: Request, context: ChatSessionContext = _chat_session_dependency
) -> dict[str, Any]:
    """Authenticated read of the caller's current-day Free Pool quota usage.

    The quota owner comes exclusively from the validated session context;
    no user ID, quota amount, or date window is accepted from the client.
    Unenrolled callers learn only that they are not enrolled. Store failures
    fail closed with ``quota_unavailable`` and never fabricate zero usage.
    """
    state = getattr(request.app.state, "gateway", None)
    policy = getattr(state, "quota_policy", None)
    if policy is None:
        raise HTTPException(
            status_code=503,
            detail={
                "error": {
                    "message": "Usage limits are temporarily unavailable.",
                    "type": "quota_unavailable",
                }
            },
        )
    if not policy.covers(context.user.user_id):
        return {"enrolled": False}
    store = getattr(state, "key_store", None)
    if store is None:
        raise HTTPException(
            status_code=503,
            detail={
                "error": {
                    "message": "Usage limits are temporarily unavailable.",
                    "type": "quota_unavailable",
                }
            },
        )
    window = quota_window_start(datetime.now(UTC))
    try:
        usage = await _executor(request).run(
            store.get_quota_usage, context.user.user_id, window
        )
    except Exception:
        raise HTTPException(
            status_code=503,
            detail={
                "error": {
                    "message": "Usage limits are temporarily unavailable.",
                    "type": "quota_unavailable",
                }
            },
        ) from None
    try:
        reserved = usage["reserved_tokens"]
        consumed = usage["consumed_tokens"]
    except (KeyError, TypeError):
        raise HTTPException(
            status_code=503,
            detail={
                "error": {
                    "message": "Usage limits are temporarily unavailable.",
                    "type": "quota_unavailable",
                }
            },
        ) from None
    if (
        not isinstance(reserved, int)
        or isinstance(reserved, bool)
        or not isinstance(consumed, int)
        or isinstance(consumed, bool)
        or reserved < 0
        or consumed < 0
    ):
        raise HTTPException(
            status_code=503,
            detail={
                "error": {
                    "message": "Usage limits are temporarily unavailable.",
                    "type": "quota_unavailable",
                }
            },
        )
    quota = policy.daily_tokens
    if not isinstance(quota, int) or isinstance(quota, bool) or quota < 1:
        raise HTTPException(
            status_code=503,
            detail={
                "error": {
                    "message": "Usage limits are temporarily unavailable.",
                    "type": "quota_unavailable",
                }
            },
        )
    used = reserved + consumed
    return {
        "enrolled": True,
        "used_tokens": used,
        "quota_tokens": quota,
        "remaining_tokens": max(0, quota - used),
        "window_start": window.isoformat(),
        "reset_at": quota_reset_at(window).isoformat(),
    }


@router.post("/v1/conversations", status_code=201)
async def create_conversation(
    payload: CreateConversationRequest,
    request: Request,
    context: ChatSessionContext = _chat_session_dependency,
) -> dict[str, Any]:
    store = _chat_store(request)
    title = (payload.title or "").strip() or "New conversation"
    conversation = await _executor(request).run(
        store.create_conversation, context.user.user_id, title[:MAX_TITLE_CHARS]
    )
    return _conversation_payload(conversation, messages=[])


@router.get("/v1/conversations")
async def list_conversations(
    request: Request,
    context: ChatSessionContext = _chat_session_dependency,
    limit: int = Query(default=20, ge=1, le=50),
    offset: int = Query(default=0, ge=0),
) -> dict[str, Any]:
    store = _chat_store(request)
    conversations, total = await _executor(request).run(
        store.list_conversations, context.user.user_id, limit=limit, offset=offset
    )
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [_conversation_payload(item) for item in conversations],
    }


@router.get("/v1/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    request: Request,
    context: ChatSessionContext = _chat_session_dependency,
    limit: int = Query(default=100, ge=1, le=200),
) -> dict[str, Any]:
    store = _chat_store(request)
    conversation = await _executor(request).run(
        store.get_conversation, conversation_id, context.user.user_id
    )
    if conversation is None:
        # Owner-scoped: another user's ID and a nonexistent ID look identical.
        raise HTTPException(
            status_code=404,
            detail={
                "error": {"message": "Conversation not found.", "type": "not_found"}
            },
        )
    messages = await _executor(request).run(
        store.list_messages, conversation.conversation_id, limit=limit
    )
    return _conversation_payload(
        conversation,
        messages=[
            _message_payload(
                item.message_id,
                item.role,
                item.content,
                item.model,
                item.deployment,
                item.error_type,
                item.created_at,
            )
            for item in messages
        ],
    )


_PUBLIC_GATEWAY_MESSAGES: dict[str, tuple[int, str]] = {
    # Fixed public messages: the gateway's raw error text is never forwarded,
    # so internal deployment names and provider details cannot leak.
    "free_pool_unavailable": (503, "Free Chat is not enabled on this gateway."),
    "free_pool_unmapped_deployment": (403, "The requested model is not eligible for Free Chat."),
    "free_pool_no_capable_deployment": (
        503,
        "No Free Chat deployment is verified for this request.",
    ),
    "free_pool_no_healthy_deployment": (
        503,
        "No healthy Free Chat deployment is currently available.",
    ),
    "free_pool_route_configuration_error": (503, "The Free Chat route is misconfigured."),
    "budget_exceeded": (429, "The chat service budget would be exceeded."),
    "rate_limit_exceeded": (429, "Too many chat requests."),
    "rate_limited": (429, "Too many chat requests."),
    "quota_exceeded": (429, "Daily chat limit reached."),
    "quota_unavailable": (503, "Usage limits are temporarily unavailable."),
    "quota_max_tokens_required": (
        400,
        "A positive max_tokens is required for metered requests.",
    ),
}


def _public_gateway_error(status_code: int, error_type: str) -> tuple[int, str, str]:
    mapped = _PUBLIC_GATEWAY_MESSAGES.get(error_type)
    if mapped is not None:
        status, message = mapped
        return status, error_type, message
    if status_code in (400, 403, 404, 429, 502, 503):
        return status_code, "gateway_error", "The chat service could not complete the request."
    return 502, "gateway_error", "The chat service could not complete the request."


@router.post("/v1/conversations/{conversation_id}/messages")
async def post_message(
    conversation_id: str,
    payload: PostMessageRequest,
    request: Request,
    context: ChatSessionContext = _chat_session_dependency,
) -> Any:
    service = _service(request)
    store = _chat_store(request)
    retry_after = service.chat_limiter.check(f"chat:{context.session.session_id}")
    if retry_after is not None:
        raise _rate_limited_response(retry_after)
    content = payload.content.strip()
    if not content:
        raise HTTPException(
            status_code=400,
            detail={
                "error": {"message": "Message content is required.", "type": "invalid_content"}
            },
        )
    model = (payload.model or "").strip() or "fast"
    conversation = await _executor(request).run(
        store.get_conversation, conversation_id, context.user.user_id
    )
    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail={"error": {"message": "Conversation not found.", "type": "not_found"}},
        )
    user_message = await _executor(request).run(
        store.create_message, conversation.conversation_id, "user", content
    )
    history = await _executor(request).run(
        store.list_messages, conversation.conversation_id, limit=HISTORY_WINDOW + 1
    )
    gateway_messages = [
        {"role": item.role, "content": item.content}
        for item in history[-HISTORY_WINDOW:]
        if item.content.strip()
    ]

    try:
        # Canonical identity only: the user ID comes from the validated
        # session context above, never from the request body.
        status_code, gateway_headers, deployment, body = await service.complete(
            request.app, model, gateway_messages, user_id=context.user.user_id
        )
    except ChatServiceUnavailable:
        raise HTTPException(
            status_code=503,
            detail={"error": {"message": "Chat is unavailable.", "type": "chat_unavailable"}},
        ) from None
    except ChatUpstreamTimeout:
        await _executor(request).run(
            store.create_message,
            conversation.conversation_id,
            "assistant",
            "",
            model=model,
            error_type="gateway_timeout",
        )
        await _executor(request).run(
            store.touch_conversation, conversation.conversation_id, context.user.user_id
        )
        raise HTTPException(
            status_code=504,
            detail={
                "error": {
                    "message": "The chat service timed out.",
                    "type": "gateway_timeout",
                }
            },
        ) from None
    except ChatUpstreamTransport:
        await _executor(request).run(
            store.create_message,
            conversation.conversation_id,
            "assistant",
            "",
            model=model,
            error_type="gateway_transport",
        )
        await _executor(request).run(
            store.touch_conversation, conversation.conversation_id, context.user.user_id
        )
        raise HTTPException(
            status_code=502,
            detail={
                "error": {
                    "message": "The chat service could not complete the request.",
                    "type": "gateway_transport",
                }
            },
        ) from None

    if status_code == 200:
        text = ""
        try:
            text = body["choices"][0]["message"].get("content") or ""
        except (KeyError, IndexError, TypeError, AttributeError):
            text = ""
        if not isinstance(text, str):
            text = ""
        assistant = await _executor(request).run(
            store.create_message,
            conversation.conversation_id,
            "assistant",
            text[:MAX_CONTENT_CHARS],
            model=model,
            deployment=deployment,
        )
        await _executor(request).run(
            store.touch_conversation, conversation.conversation_id, context.user.user_id
        )
        return {
            "conversation_id": conversation.conversation_id,
            "model": model,
            "deployment": deployment,
            "user_message": _message_payload(
                user_message.message_id,
                "user",
                user_message.content,
                None,
                None,
                None,
                user_message.created_at,
            ),
            "assistant_message": _message_payload(
                assistant.message_id,
                "assistant",
                assistant.content,
                model,
                deployment,
                None,
                assistant.created_at,
            ),
        }

    raw_error = body.get("error") if isinstance(body, dict) else None
    raw_type = raw_error.get("type") if isinstance(raw_error, dict) else None
    public_status, public_type, public_message = _public_gateway_error(
        status_code, raw_type if isinstance(raw_type, str) else "gateway_error"
    )
    if public_type == "quota_exceeded":
        # Reset time is gateway-computed from the UTC window (reliable by
        # construction); omitted entirely when the gateway did not send it.
        reset_at = raw_error.get("reset_at") if isinstance(raw_error, dict) else None
        if isinstance(reset_at, str) and reset_at:
            public_message = f"{public_message} Resets at {reset_at}."
    await _executor(request).run(
        store.create_message,
        conversation.conversation_id,
        "assistant",
        "",
        model=model,
        error_type=public_type,
    )
    await _executor(request).run(
        store.touch_conversation, conversation.conversation_id, context.user.user_id
    )
    error = HTTPException(
        status_code=public_status,
        detail={"error": {"message": public_message, "type": public_type}},
    )
    gateway_retry_after = gateway_headers.get("retry-after")
    if (
        public_type == "quota_exceeded"
        and isinstance(gateway_retry_after, str)
        and gateway_retry_after.isdigit()
    ):
        # Propagate the gateway's window-derived retry hint; the chat
        # wrapper never invents one (in particular, quota_unavailable
        # carries no Retry-After by gateway contract).
        error.headers = {"Retry-After": gateway_retry_after}
    raise error
