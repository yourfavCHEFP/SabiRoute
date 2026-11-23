# Provider configuration and verification

`config/config.yaml` is the single runtime source of truth for deployment
aliases and LiteLLM provider/model identifiers. LiteLLM is pointed at this same
file by Compose. The files under `config/models/` are not loaded by the current
runtime; changing one of those fragments does not add or update a deployment.

The registry currently contains these configured aliases:

| SabiRoute alias | LiteLLM model | Credential variable | Runtime evidence |
| --- | --- | --- | --- |
| `sabiroute-openai` | `openai/gpt-6-luna` | `OPENAI_API_KEY` | 2026-11-23 probe: HTTP 429, no credits remaining |
| `sabiroute-gemini` | `gemini/gemini-3.8-flash` | `GEMINI_API_KEY` | Verified 2026-10-08; 2026-11-23 probe: HTTP 503 then 25s timeout (provider-side demand) |
| `sabiroute-groq` | `groq/openai/gpt-oss-120b` | `GROQ_API_KEY` | 2026-11-23 probe: 200 with empty assistant content — not usable |
| `sabiroute-together` | `together_ai/openai/gpt-oss-120B` | `TOGETHERAI_API_KEY` | 2026-11-23 probe: HTTP 401 |
| `sabiroute-deepinfra` | `deepinfra/meta-llama/Meta-Llama-3-70B-Instruct` | `DEEPINFRA_API_KEY` | 2026-11-23 probe: HTTP 402, positive balance required |
| `sabiroute-kimi` | `moonshot/moonshot-v1-128k` | `MOONSHOT_API_KEY` | 2026-11-23 probe: HTTP 429 |
| `sabiroute-minimax` | `minimax/MiniMax-M2.1` | `MINIMAX_API_KEY` | 2026-11-23 probe: HTTP 402, insufficient balance |
| `sabiroute-cloudflare` | `cloudflare/@cf/meta/llama-3.3-70b-instruct-fp8-fast` | `CLOUDFLARE_API_KEY`, `CLOUDFLARE_ACCOUNT_ID` | **2026-11-23 probe: OK — real non-empty completion** |
| `sabiroute-openrouter` | `openrouter/google/gemini-3.8-flash` | `OPENROUTER_API_KEY` | 2026-11-23 probe: 200 with empty content at `max_tokens` 16; HTTP 402 on a full-length request |
| `sabiroute-huggingface` | `huggingface/meta-llama/Llama-3.3-70B-Instruct` | `HF_TOKEN` | 2026-11-23 probe: HTTP 402, pre-paid credits required |
| `sabiroute-cerebras` | `cerebras/llama3-70b-instruct` | `CEREBRAS_API_KEY` | 2026-11-23 probe: HTTP 402, payment required |
| `sabiroute-nvidia` | `nvidia_nim/nvidia/nemotron-3.5-bolt-e4b` | `NVIDIA_NIM_API_KEY` | **2026-11-23 probe: OK — real non-empty completion** |
| `sabiroute-cohere` | `cohere_chat/command-a-03-2025` | `COHERE_API_KEY` | **2026-11-23 probe: OK — real non-empty completion** |
| `sabiroute-pollinations` | `openai/gpt-6-luna` at the configured Pollinations API base | `POLLINATION_API_KEY` | **2026-11-23 probe: OK — real non-empty completion** |

**Contract-gap note [VERIFIED BY INSPECTION]:** the aliases above are not a provider-contract matrix. Provider-reported usage, tool calls, context limits, authentication translation, and live response shape remain untested dimensions. R2 stays `BLOCKED — NOT DONE`; this note upgrades no provider status.

“Configured” means the alias and credential reference exist in YAML. It does not
mean the credential is present, the account has quota, or a live completion has
passed. The SabiRoute registry preserves environment references and resolves
provider credentials only at the LiteLLM request boundary. Never put key values
in YAML, reports, or terminal output.

The provider verification script can test one named deployment, but it also
writes provider error details to `reports/provider_verification.json`. Review
and sanitize that report before sharing it. Avoid broad provider runs unless you
intend to make a request to every configured provider that has a credential.

`scripts/probe_provider_aliases.py` is the deliberate, credential-aware
alternative introduced on 2026-11-23. It reads each deployment from
`config/config.yaml`, makes exactly one minimal completion per alias
(`max_tokens` 16, 25s cap, no retries), and prints a JSON verdict to stdout. It
writes no file and prints no credential value — only variable names. An alias
that returns 200 with empty assistant text is reported as `EMPTY_CONTENT`, not
as working.

## Phase 02 status

Phase 02 is **4 of 14 verified** as of 2026-11-23, by the probe above:
`sabiroute-cloudflare`, `sabiroute-nvidia`, `sabiroute-cohere` and
`sabiroute-pollinations` each returned a real non-empty completion.

This supersedes the earlier recorded count of 1. That figure was correct when it
was written — it reflected this document, and this document recorded only Gemini
because it had not been re-probed. It also supersedes the claim of 3 that
appeared in an older `config/config.yaml` comment, which named providers this
table did not carry.

Two distinctions the count depends on, both of which have changed a status
before and will again:

- **A credential being present is not a provider working.** All fourteen
  variables are set in the environment; ten aliases still fail.
- **HTTP 200 is not a usable alias.** Groq and OpenRouter both answered 200 with
  empty assistant text. OpenRouter additionally returns 402 once a request asks
  for more than a trivial completion. Neither is counted as working.

The nvidia row's model identifier was corrected on 2026-11-23 from
`nvidia_nim/meta/llama3-70b-instruct` to the value `config/config.yaml` actually
loads, `nvidia_nim/nvidia/nemotron-3.5-bolt-e4b`. The stale identifier returns a
real provider 404, so the previous row could not have passed a probe.

Do not raise this count without re-running the probe and recording the date.

Per-alias remediation and an ask-ordering live in
`artifacts/PHASE02-PROVIDER-REQUIREMENTS-2026-11-23.md`.
