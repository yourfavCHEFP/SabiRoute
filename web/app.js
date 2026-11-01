"use strict";

/* ------------------------------------------------------------------ */
/* API client: network + auth only. No DOM access in this section.      */
/* Same-origin by default; override with window.SABICHAT_API_BASE.      */
/* The session token lives in memory only — never in URLs, logs, or    */
/* persistent browser storage.                                         */
/* ------------------------------------------------------------------ */

const API_BASE = (window.SABICHAT_API_BASE || "").replace(/\/$/, "");

class ApiError extends Error {
  constructor(status, type, message) {
    super(message);
    this.status = status;
    this.type = type;
  }
}

async function apiFetch(path, { method = "GET", token = null, body = null, signal = null } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      method,
      headers,
      body: body === null ? null : JSON.stringify(body),
      signal,
    });
  } catch (err) {
    if (err && err.name === "AbortError") throw err;
    throw new ApiError(0, "network_error", "Couldn't reach the SabiChat backend.");
  }
  let payload = {};
  try {
    payload = await response.json();
  } catch (_) {
    payload = {};
  }
  if (!response.ok) {
    const inner =
      payload && typeof payload === "object" && payload.detail && payload.detail.error
        ? payload.detail.error
        : {};
    throw new ApiError(
      response.status,
      typeof inner.type === "string" ? inner.type : "request_failed",
      typeof inner.message === "string" ? inner.message : "The request failed."
    );
  }
  return payload;
}

const api = {
  register: (email, password) =>
    apiFetch("/v1/auth/register", { method: "POST", body: { email, password } }),
  login: (email, password) =>
    apiFetch("/v1/auth/login", { method: "POST", body: { email, password } }),
  logout: (token) => apiFetch("/v1/auth/logout", { method: "POST", token }),
  me: (token) => apiFetch("/v1/auth/me", { token }),
  listConversations: (token, limit = 50) =>
    apiFetch(`/v1/conversations?limit=${limit}`, { token }),
  createConversation: (token, title) =>
    apiFetch("/v1/conversations", { method: "POST", token, body: { title } }),
  getConversation: (token, id, limit = 200) =>
    apiFetch(`/v1/conversations/${encodeURIComponent(id)}?limit=${limit}`, { token }),
  postMessage: (token, id, content, signal) =>
    apiFetch(`/v1/conversations/${encodeURIComponent(id)}/messages`, {
      method: "POST",
      token,
      body: { content },
      signal,
    }),
  quotaSummary: (token, signal) =>
    apiFetch("/v1/chat/quota-summary", { token, signal }),
};

/* ------------------------------------------------------------------ */
/* Presentation. Model output is rendered with textContent only.        */
/* ------------------------------------------------------------------ */

function friendlyError(err) {
  if (!(err instanceof ApiError)) return "Something went wrong.";
  switch (err.type) {
    case "network_error":
      return "Couldn't reach the SabiChat backend. Check the connection and retry.";
    case "invalid_session":
      return "Your session expired. Please sign in again.";
    case "rate_limit_exceeded":
    case "rate_limited":
      return "Too many requests — please wait a moment and retry.";
    case "free_pool_unmapped_deployment":
      return "That model isn't eligible for Free Chat right now.";
    case "free_pool_unavailable":
    case "free_pool_no_capable_deployment":
    case "free_pool_no_healthy_deployment":
    case "free_pool_route_configuration_error":
      return "Free Chat has no eligible capacity right now. Please try again later.";
    case "budget_exceeded":
      return "The chat service budget is exhausted right now. Please try again later.";
    case "quota_exceeded":
      // Server message already states the limit and reliable reset time.
      return err.message || "Daily chat limit reached.";
    case "quota_unavailable":
      return "Usage limits are temporarily unavailable. Please try again later.";
    case "gateway_timeout":
    case "gateway_transport":
    case "gateway_error":
      return "The chat service had trouble reaching the provider. Please retry.";
    default:
      return err.message || "The request failed.";
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const $ = (id) => document.getElementById(id);

  const viewAuth = $("view-auth");
  const viewApp = $("view-app");
  const tabLogin = $("tab-login");
  const tabRegister = $("tab-register");
  const authForm = $("auth-form");
  const authEmail = $("auth-email");
  const authPassword = $("auth-password");
  const authSubmit = $("auth-submit");
  const authError = $("auth-error");
  const conversationList = $("conversation-list");
  const messageList = $("message-list");
  const emptyState = $("empty-state");
  const composer = $("composer");
  const composerInput = $("composer-input");
  const sendButton = $("send-button");
  const cancelButton = $("cancel-button");
  const banner = $("banner");
  const userEmail = $("user-email");
  const quotaMeter = $("quota-meter");
  const quotaText = $("quota-text");
  const quotaBar = $("quota-bar");
  const quotaFill = $("quota-fill");
  const quotaReset = $("quota-reset");

  let session = null; // { token, user_id, email } — memory only.
  let conversations = [];
  let currentMessages = [];
  let activeId = null;
  let pending = null; // AbortController for the in-flight send, if any.
  let authMode = "login";

  function showBanner(text) {
    banner.textContent = text;
    banner.hidden = false;
  }
  function hideBanner() {
    banner.hidden = true;
    banner.textContent = "";
  }

  /* Daily Free Pool usage meter. Data comes only from the session-
     authenticated quota-summary endpoint — never invented, never cached
     across users. Stale values are labelled stale, never shown as fresh. */
  let quotaSeq = 0;
  let quotaInfo = null; // { status, used, quota, resetAt } — session-scoped.

  function formatTokens(n) {
    return Number(n).toLocaleString("en-US");
  }

  function renderQuotaReady(data) {
    const used = data.used_tokens;
    const quota = data.quota_tokens;
    const remaining = data.remaining_tokens;
    const resetAt = data.reset_at;
    if (
      !Number.isFinite(used) || used < 0 ||
      !Number.isFinite(quota) || quota < 1 ||
      !Number.isFinite(remaining) || remaining < 0 ||
      typeof resetAt !== "string" || !resetAt ||
      Number.isNaN(Date.parse(resetAt))
    ) {
      renderQuotaUnavailable();
      return;
    }
    quotaInfo = { status: "ready", used, quota, resetAt };
    quotaMeter.hidden = false;
    quotaText.textContent =
      `Free Pool today: ${formatTokens(used)} / ${formatTokens(quota)} · ${formatTokens(remaining)} left`;
    const pct = Math.min(100, (used / quota) * 100);
    quotaFill.style.width = `${pct}%`;
    quotaBar.setAttribute("aria-valuemax", String(quota));
    quotaBar.setAttribute("aria-valuenow", String(used));
    quotaBar.hidden = false;
    quotaReset.textContent = `Resets ${new Date(resetAt).toUTCString()}`;
  }

  function renderQuotaUnavailable() {
    quotaInfo = { status: "unavailable" };
    quotaMeter.hidden = false;
    quotaText.textContent = "Free Pool usage is temporarily unavailable.";
    quotaBar.hidden = true;
    quotaReset.textContent = "";
  }

  function renderQuotaStale() {
    if (quotaInfo && quotaInfo.status === "ready") {
      quotaReset.textContent = "Couldn't refresh — showing last known usage.";
      return;
    }
    quotaInfo = { status: "stale" };
    quotaMeter.hidden = false;
    quotaText.textContent = "Couldn't load Free Pool usage.";
    quotaBar.hidden = true;
    quotaReset.textContent = "";
  }

  function refreshQuota() {
    if (!session) return;
    const mySession = session;
    const seq = ++quotaSeq;
    const hadData = quotaInfo && quotaInfo.status === "ready";
    if (!hadData && quotaMeter.hidden) {
      quotaMeter.hidden = false;
      quotaText.textContent = "Loading Free Pool usage…";
      quotaBar.hidden = true;
      quotaReset.textContent = "";
    }
    api
      .quotaSummary(mySession.token)
      .then((data) => {
        if (session !== mySession || seq !== quotaSeq) return;
        if (!data || data.enrolled !== true) {
          quotaInfo = { status: "unenrolled" };
          quotaMeter.hidden = true;
          return;
        }
        renderQuotaReady(data);
      })
      .catch((err) => {
        if (session !== mySession || seq !== quotaSeq) return;
        if (err instanceof ApiError && err.type === "quota_unavailable") {
          renderQuotaUnavailable();
          return;
        }
        renderQuotaStale();
      });
  }

  function showAuth(message) {
    session = null;
    quotaInfo = null;
    quotaSeq++;
    quotaMeter.hidden = true;
    activeId = null;
    conversations = [];
    // Account-scoped UI must not survive the session: clear rendered
    // messages, the in-memory message state, the composer draft, and any
    // prior-session banner before showing the authentication view.
    renderMessages([]);
    composerInput.value = "";
    hideBanner();
    viewApp.hidden = true;
    viewAuth.hidden = false;
    authError.hidden = !message;
    authError.textContent = message || "";
  }

  function setAuthMode(mode) {
    authMode = mode;
    const isLogin = mode === "login";
    tabLogin.setAttribute("aria-selected", String(isLogin));
    tabRegister.setAttribute("aria-selected", String(!isLogin));
    authSubmit.textContent = isLogin ? "Sign in" : "Register";
    authPassword.setAttribute("autocomplete", isLogin ? "current-password" : "new-password");
    authError.hidden = true;
  }
  tabLogin.addEventListener("click", () => setAuthMode("login"));
  tabRegister.addEventListener("click", () => setAuthMode("register"));

  async function enterApp(data) {
    session = { token: data.token, user_id: data.user_id, email: data.email };
    userEmail.textContent = data.email;
    viewAuth.hidden = true;
    viewApp.hidden = false;
    hideBanner();
    await refreshConversations();
    refreshQuota();
    composerInput.focus();
  }

  authForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    authError.hidden = true;
    authSubmit.disabled = true;
    try {
      const email = authEmail.value.trim();
      const password = authPassword.value;
      const data =
        authMode === "login" ? await api.login(email, password) : await api.register(email, password);
      authPassword.value = "";
      await enterApp(data);
    } catch (err) {
      authError.textContent = friendlyError(err);
      authError.hidden = false;
    } finally {
      authSubmit.disabled = false;
    }
  });

  $("sign-out").addEventListener("click", async () => {
    if (pending) {
      pending.abort(); // In-flight work belongs to the ending session; drop it.
      pending = null;
    }
    if (session) {
      try {
        await api.logout(session.token);
      } catch (_) {
        /* Signing out is best-effort; session state is server-side. */
      }
    }
    showAuth("");
  });

  $("new-chat").addEventListener("click", async () => {
    if (!session) return;
    hideBanner();
    try {
      const created = await api.createConversation(session.token, "New conversation");
      conversations.unshift(created);
      renderConversationList();
      await selectConversation(created.conversation_id);
    } catch (err) {
      handleApiError(err);
    }
  });

  async function refreshConversations() {
    try {
      const data = await api.listConversations(session.token);
      conversations = Array.isArray(data.items) ? data.items : [];
      renderConversationList();
    } catch (err) {
      handleApiError(err);
    }
  }

  function renderConversationList() {
    while (conversationList.firstChild) conversationList.removeChild(conversationList.firstChild);
    for (const conv of conversations) {
      const li = document.createElement("li");
      const button = document.createElement("button");
      button.type = "button";
      if (conv.conversation_id === activeId) button.setAttribute("aria-current", "true");
      const title = document.createElement("span");
      title.className = "conv-title";
      title.textContent = conv.title || "Untitled";
      button.appendChild(title);
      button.addEventListener("click", () => selectConversation(conv.conversation_id));
      li.appendChild(button);
      conversationList.appendChild(li);
    }
  }

  function renderMessages(messages) {
    currentMessages = Array.isArray(messages) ? messages : [];
    while (messageList.firstChild) messageList.removeChild(messageList.firstChild);
    for (const item of currentMessages) {
      const li = document.createElement("li");
      li.className = "message" + (item.pending ? " pending" : "");
      li.dataset.role = item.role === "user" ? "user" : "assistant";
      const label = document.createElement("span");
      label.className = "role-label";
      label.textContent = item.role === "user" ? "You" : "Assistant";
      const body = document.createElement("div");
      body.textContent =
        item.content || (item.error_type ? "(this response failed — see notice above)" : "");
      li.appendChild(label);
      li.appendChild(body);
      messageList.appendChild(li);
    }
    messageList.scrollTop = messageList.scrollHeight;
  }

  function setComposerEnabled(enabled) {
    composerInput.disabled = !enabled;
    sendButton.disabled = !enabled;
    cancelButton.hidden = enabled;
  }

  async function selectConversation(id) {
    if (!session) return;
    if (pending) {
      pending.abort(); // Never let a late response land in the wrong conversation.
      pending = null;
    }
    activeId = id; // Set before the fetch so failures still show the selection.
    renderConversationList();
    // Clear immediately: switching conversations must never show stale messages.
    renderMessages([]);
    messageList.hidden = false;
    emptyState.hidden = true;
    composer.hidden = false;
    setComposerEnabled(false);
    hideBanner();
    if (
      quotaInfo &&
      quotaInfo.status === "ready" &&
      quotaInfo.resetAt &&
      Date.now() >= Date.parse(quotaInfo.resetAt)
    ) {
      refreshQuota(); // UTC quota window rolled over while idle.
    }
    try {
      const data = await api.getConversation(session.token, id);
      if (activeId !== id) return; // User moved on while loading.
      renderMessages(Array.isArray(data.messages) ? data.messages : []);
    } catch (err) {
      handleApiError(err);
    } finally {
      if (activeId === id) setComposerEnabled(true);
      composerInput.focus();
    }
  }

  composer.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!session || !activeId || pending) return; // Guard against double submits.
    const content = composerInput.value.trim();
    if (!content) return;
    composerInput.value = "";
    hideBanner();
    setComposerEnabled(false);

    // Optimistic user bubble; replaced by server state below.
    renderMessages([
      ...currentMessages,
      { role: "user", content },
      { role: "assistant", content: "Thinking…", pending: true },
    ]);

    // Captured up front: the session or selection may change mid-flight
    // (switch, logout), and a late response must never render into whatever
    // happens to be active when it lands.
    const mySession = session;
    const myId = activeId;
    const controller = new AbortController();
    pending = controller;
    try {
      const result = await api.postMessage(mySession.token, myId, content, controller.signal);
      if (!result || !result.assistant_message) throw new Error("bad response");
      const data = await api.getConversation(mySession.token, myId);
      if (activeId !== myId) return; // User moved on; their view owns the screen now.
      renderMessages(Array.isArray(data.messages) ? data.messages : []);
      refreshQuota(); // One refresh per completed logical request.
    } catch (err) {
      if (err && err.name === "AbortError") {
        // Cancelled or navigated away: drop the optimistic "Thinking…"
        // bubble by re-syncing, but only if this conversation is still the
        // active one. Never surface errors here — navigation already owns
        // the screen, and logout already owns the session state.
        try {
          const data = await api.getConversation(mySession.token, myId);
          if (activeId === myId) {
            renderMessages(Array.isArray(data.messages) ? data.messages : []);
          }
        } catch (_) {
          /* Stale view after navigation/logout; nothing to show. */
        }
        return;
      }
      if (err instanceof ApiError) {
        handleApiError(err);
        if (err.type === "quota_exceeded") {
          // The composer was cleared optimistically above; restore the draft
          // so the limit costs history, not the user's words.
          composerInput.value = content;
        }
        refreshQuota();
        // Re-sync: the user message is stored even when the assistant fails.
        try {
          const data = await api.getConversation(mySession.token, myId);
          if (activeId !== myId) return;
          renderMessages(Array.isArray(data.messages) ? data.messages : []);
        } catch (_) {
          /* Banner already explains the failure. */
        }
      } else {
        showBanner("Something went wrong.");
      }
    } finally {
      if (pending === controller) pending = null;
      if (activeId === myId) setComposerEnabled(true);
      composerInput.focus();
    }
  });

  cancelButton.addEventListener("click", () => {
    if (pending) pending.abort();
  });

  composerInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      composer.requestSubmit();
    }
  });

  function handleApiError(err) {
    if (err instanceof ApiError && err.type === "invalid_session") {
      showAuth("Your session expired. Please sign in again.");
      return;
    }
    showBanner(friendlyError(err));
  }

  setAuthMode("login");
  viewAuth.hidden = false;
});
