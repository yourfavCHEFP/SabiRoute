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
`chat` and `streaming`. No other capabilities have deployment-specific
evidence. Untyped ordinary chat keeps the existing ordered route and fallback
behavior until a request explicitly requires a capability.

## Evidence matrix (2026-10-08)

| Deployment alias | `chat` | All other capabilities | Evidence |
|---|---|---|---|
| `sabiroute-openai` | unknown | unknown | No deployment-specific runtime evidence collected |
| `sabiroute-gemini` | true | unknown | 2026-10-08 non-empty completion. **2026-11-23 probe: HTTP 503 then timeout — not reproducible today**; keeps its 2026-10-08 basis, is not currently relied on |
| `sabiroute-groq` | true | `streaming` true; all other capabilities unknown | 2026-10-08 non-empty completion and 13 SSE chunks. **2026-11-23 probe: non-empty completion confirmed**; an earlier empty result that day was a probe budget artefact |
| `sabiroute-together` | unknown | unknown | No deployment-specific runtime evidence collected |
| `sabiroute-deepinfra` | unknown | unknown | No deployment-specific runtime evidence collected |
| `sabiroute-kimi` | unknown | unknown | No deployment-specific runtime evidence collected |
| `sabiroute-minimax` | unknown | unknown | No deployment-specific runtime evidence collected |
| `sabiroute-cloudflare` | true | unknown | 2026-11-23 probe: real non-empty completion (2.6s) |
| `sabiroute-openrouter` | true | unknown | **2026-11-23 probe: non-empty completion confirmed** once the output budget exceeded its reasoning trace |
| `sabiroute-huggingface` | unknown | unknown | No deployment-specific runtime evidence collected |
| `sabiroute-cerebras` | unknown | unknown | No deployment-specific runtime evidence collected |
| `sabiroute-nvidia` | true | unknown | 2026-11-23 probe: real non-empty completion (1.0s) |
| `sabiroute-cohere` | true | unknown | 2026-11-23 probe: real non-empty completion (2.9s) |
| `sabiroute-pollinations` | true | unknown | 2026-11-23 probe: real non-empty completion (1.2s) |

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
