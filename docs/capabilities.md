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
| `sabiroute-gemini` | true | unknown | Non-empty text completion through LiteLLM; model alias `sabiroute-gemini` |
| `sabiroute-groq` | true | `streaming` true; all other capabilities unknown | Non-empty completion and 13 content chunks over SSE through SabiRoute → LiteLLM |
| `sabiroute-together` | unknown | unknown | No deployment-specific runtime evidence collected |
| `sabiroute-deepinfra` | unknown | unknown | No deployment-specific runtime evidence collected |
| `sabiroute-kimi` | unknown | unknown | No deployment-specific runtime evidence collected |
| `sabiroute-minimax` | unknown | unknown | No deployment-specific runtime evidence collected |
| `sabiroute-cloudflare` | unknown | unknown | No deployment-specific runtime evidence collected |
| `sabiroute-openrouter` | true | unknown | Non-empty text completion through LiteLLM using the configured OpenRouter deployment |
| `sabiroute-huggingface` | unknown | unknown | No deployment-specific runtime evidence collected |
| `sabiroute-cerebras` | unknown | unknown | No deployment-specific runtime evidence collected |
| `sabiroute-nvidia` | unknown | unknown | No deployment-specific runtime evidence collected |
| `sabiroute-cohere` | unknown | unknown | No deployment-specific runtime evidence collected |
| `sabiroute-pollinations` | unknown | unknown | No deployment-specific runtime evidence collected |

“All other capabilities” means `coding`, `reasoning`, `vision`,
`long_context`, `tool_use`, `structured_output`, `json`, `streaming`,
`low_latency`, `embedding`, and `multimodal` (plus `inline_completion`, which
is also supported by the typed schema). No capability is explicitly marked
unsupported (`false`) without evidence.
Requests that explicitly set `sabi_route_request_type`, use a route with
`required_capabilities`, or require a feature such as tool use, JSON output,
streaming, vision, or multimodal input are filtered against verified metadata.
Streaming is supported only for deployments explicitly marked `streaming: true`.

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
