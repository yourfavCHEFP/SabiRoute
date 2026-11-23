# Capability declarations and deterministic routing

SabiRoute capability metadata is deployment-specific and is declared in
`config/config.yaml`. The typed configuration accepts `true`, `false`, or
`unknown` for each capability:

```yaml
capabilities:
  chat: unknown
  coding: unknown
  vision: false
```

`true` means the deployment is explicitly verified to support the capability;
`false` means it is explicitly verified not to support it; `unknown` (or an
omitted field) makes no claim. Unknown never satisfies an explicit routing
requirement. Provider/model names and marketing descriptions are not evidence.

Capabilities remain `unknown` unless there is deployment-specific evidence.
On 2026-10-08, `sabiroute-gemini` returned a non-empty text completion through
LiteLLM, verifying `chat`. `sabiroute-groq` returned non-empty text and
incremental SSE chunks through the full SabiRoute → LiteLLM path, verifying
`chat` and `streaming`. A 2026-11-23 capability probe extended this set for the
six aliases with `chat` evidence; see *2026-11-23 capability probe* below.
Untyped ordinary chat keeps the existing ordered route and fallback behavior
until a request explicitly requires a capability.

## Evidence matrix (2026-10-08)

Rows carry the most recent evidence inline; the heading date marks the matrix's
original creation.

| Deployment alias | `chat` | All other capabilities | Evidence |
|---|---|---|---|
| `sabiroute-openai` | unknown | unknown | No deployment-specific runtime evidence collected |
| `sabiroute-gemini` | true | unknown | 2026-10-08 non-empty completion. **2026-11-23 probe: HTTP 503 then timeout — not reproducible today**; keeps its 2026-10-08 basis, is not currently relied on |
| `sabiroute-groq` | true | `streaming` true; `tool_use` true; `json`/`structured_output` unproven | 2026-10-08 non-empty completion and 13 SSE chunks. **2026-11-23 probe: non-empty completion confirmed**; an earlier empty result that day was a probe budget artefact. **2026-11-23 capability probe: streaming 32 chunks; `get_weather` tool call; `json_object` rejected HTTP 400 "Failed to validate JSON. Please adjust your prompt" — a provider-side JSON validation rejection, not proof of absence** |
| `sabiroute-together` | unknown | unknown | No deployment-specific runtime evidence collected |
| `sabiroute-deepinfra` | unknown | unknown | No deployment-specific runtime evidence collected |
| `sabiroute-kimi` | unknown | unknown | No deployment-specific runtime evidence collected |
| `sabiroute-minimax` | unknown | unknown | No deployment-specific runtime evidence collected |
| `sabiroute-cloudflare` | true | `streaming` true; `json` true; `structured_output` true; `tool_use` true | 2026-11-23 probe: real non-empty completion (2.6s). **2026-11-23 capability probe: streaming OK; strict JSON; `get_weather` tool call** |
| `sabiroute-openrouter` | true | `streaming` true; `json` true; `structured_output` true; `tool_use` true | **2026-11-23 probe: non-empty completion confirmed** once the output budget exceeded its reasoning trace. **2026-11-23 capability probe: streaming OK; strict JSON after one 512-token escalation; `get_weather` tool call emitted (finish_reason `length` — the reasoning trace consumed the budget after the call)** |
| `sabiroute-huggingface` | unknown | unknown | No deployment-specific runtime evidence collected |
| `sabiroute-cerebras` | unknown | unknown | No deployment-specific runtime evidence collected |
| `sabiroute-nvidia` | true | `streaming` true; `json` true; `structured_output` true; `tool_use` true | 2026-11-23 probe: real non-empty completion (1.0s). **2026-11-23 capability probe: streaming OK; strict JSON; `get_weather` tool call** |
| `sabiroute-cohere` | true | `streaming` true; `tool_use` true; `json`/`structured_output` unavailable through LiteLLM | 2026-11-23 probe: real non-empty completion (2.9s). **2026-11-23 capability probe: streaming OK; `get_weather` tool call; `response_format` rejected HTTP 400 by the LiteLLM `cohere_chat` adapter ("does not support parameters: ['response_format']") — an execution-layer limitation, not a Cohere API statement** |
| `sabiroute-pollinations` | true | `streaming` true; `json` true; `structured_output` true; `tool_use` true | 2026-11-23 probe: real non-empty completion (1.2s). **2026-11-23 capability probe: streaming OK; strict JSON; `get_weather` tool call** |

“All other capabilities” means `coding`, `reasoning`, `vision`,
`long_context`, `tool_use`, `structured_output`, `json`, `streaming`,
`low_latency`, `embedding`, and `multimodal` (plus `inline_completion`, which
is also supported by the typed schema). No capability is explicitly marked
unsupported (`false`) without evidence.
Requests that explicitly set `sabi_route_request_type`, use a route with
`required_capabilities`, or require a feature such as tool use, JSON output,
streaming, vision, or multimodal input are filtered against verified metadata.
Streaming is supported only for deployments explicitly marked `streaming: true`.

## 2026-11-23 probe

`scripts/probe_provider_aliases.py` made one real minimal completion per alias.
Four deployments returned non-empty assistant text — `cloudflare`, `nvidia`,
`cohere` and `pollinations` — and each is recorded as `chat: true` on that basis
alone. Nothing else was tested. No row above gains `coding`, `reasoning`,
`vision`, `tool_use`, `json`, `streaming` or any other capability from this
probe.

Six aliases now carry `chat` evidence, counting `groq` and `openrouter`, which
an earlier run of the same probe wrongly reported as empty: both are reasoning
models that spent the whole output budget on their reasoning trace. One row
still contradicts the probe and is left standing: `gemini` (503 then timeout,
provider-side). An empty completion is not evidence that `chat` is unsupported,
so no `true` is downgraded on that basis.


## 2026-11-23 capability probe

`scripts/probe_capabilities.py` probed the three capabilities the router cannot
use yet, for the six aliases that already had `chat` runtime evidence. One
probe per capability per alias (18 cells), 64-token start, a single escalation
to 512 tokens only when empty content arrived with `finish_reason == "length"`,
a 25s per-call cap, `num_retries=0`, and no file written. Nineteen HTTP requests
were made for the 18 cells: `openrouter`'s `json` cell escalated once. Calls
went through LiteLLM directly, as `probe_provider_aliases.py` does; they were
not sent through the SabiRoute API, so end-to-end routing on these capabilities
remains unverified.

`json` and `structured_output` share one probe, because the classifier requires
both for `response_format={"type": "json_object"}` and a parseable reply is the
evidence for both. Outcome vocabulary: `SUPPORTED`, `UNSUPPORTED`,
`ERROR_<status>`, `ERROR_TIMEOUT`, `ERROR_NO_STATUS`, `NO_CREDENTIAL`. A
provider error is recorded as an error and never collapsed into `UNSUPPORTED`.

| Deployment alias | `streaming` | `json` + `structured_output` | `tool_use` |
|---|---|---|---|
| `sabiroute-groq` | SUPPORTED | ERROR_400 | SUPPORTED |
| `sabiroute-cloudflare` | SUPPORTED | SUPPORTED | SUPPORTED |
| `sabiroute-openrouter` | SUPPORTED | SUPPORTED | SUPPORTED |
| `sabiroute-nvidia` | SUPPORTED | SUPPORTED | SUPPORTED |
| `sabiroute-cohere` | SUPPORTED | ERROR_400 | SUPPORTED |
| `sabiroute-pollinations` | SUPPORTED | SUPPORTED | SUPPORTED |

`SUPPORTED` for `streaming` means at least one non-empty content delta arrived
(2–32 chunks per alias). `SUPPORTED` for `json` means the assistant content was
strict JSON parseable by `json.loads`, without stripping a fence. `SUPPORTED`
for `tool_use` means the response carried a `tool_calls` entry naming the
offered `get_weather` function.

### The two ERROR_400 cells are not the same finding

- **`sabiroute-groq`** — HTTP 400, `Failed to validate JSON. Please adjust your
  prompt.` The provider rejected the completion as failing its JSON validation
  even though the prompt asked for JSON only. That is a provider-side rejection
  of this prompt/model combination, **not evidence that the model cannot
  produce JSON**. Both `json` and `structured_output` remain unproven for this
  alias, so neither flag should be set `true` or `false` on this result alone.
- **`sabiroute-cohere`** — HTTP 400, `cohere_chat does not support parameters:
  ['response_format']`, raised by the LiteLLM adapter before the provider saw a
  request. This is an **execution-engine limitation**: SabiRoute cannot request
  JSON through the current execution path. It is not a statement about
  Cohere's own API, and it must not be recorded as `false`.

### What this probe does not establish

`coding`, `reasoning`, `vision`, `long_context`, `low_latency`, `embedding` and
`multimodal` were not probed and remain `unknown` for all six aliases. A
`tool_use` result is not evidence of `coding` or `reasoning`. This document
records what was measured; it does not change runtime behaviour, and
`config/config.yaml` remains the only runtime source of truth.

### Model identifiers used

The probe reads each deployment's model identifier from `config/config.yaml`.
`docs/providers.md` still lists different identifiers for some aliases — for
example `minimax/MiniMax-M2.1` against the configured `minimax/MiniMax-M3`,
`cerebras/llama3-70b-instruct` against `cerebras/gpt-oss-120b`, and
`openai/gpt-6-luna` where `openai/gpt-4o-mini` (openai) and `openai/openai`
(pollinations) are configured. This note records the inconsistency; it does not
rewrite that document's history.


## Classification rules

- With no explicit request class, the structured class is `CHAT` for reporting,
  but this default alone does not exclude legacy deployments with unknown
  metadata.
- `sabi_route_request_type: inline_completion` requires `chat` and
  `inline_completion`.
- `sabi_route_request_type: coding_agent` requires `chat` and `coding`.
- Route YAML `required_capabilities` are always required.
- A non-empty `tools` list or non-`none` `tool_choice` requires `tool_use`.
- Any `response_format` requires `structured_output`; `json_object` and
  `json_schema` also require `json`.
- `stream: true` requires verified `streaming` support.
- Known image/audio/video content part types require `multimodal`; image part
  types `image`, `image_url`, and `input_image` also require `vision`. Plain text
  content parts and unrecognized part types do not imply a modality.
- Prompt intent or message wording does not imply a coding or reasoning class.
- Context size is not classified because a dependable cross-provider context
  requirement cannot be derived from the request alone.

## Eligibility, health, and fallback

For requests with explicit requirements, the router applies capability filtering
first, health/cooldown filtering second, and then chooses the first remaining
deployment in configured order. Fallback calls reuse that same requirement set
and attempted candidates; neither missing capabilities nor unhealthy candidates
can be reintroduced. If no capable deployment is configured, the API returns a
generic 503 without naming internal candidate aliases. Detailed route explanation
is kept internally and is not returned in response headers or the response body.

Only the deployment-specific capabilities listed as true in the evidence matrix
are enabled. No capability is explicitly unsupported (`false`).
