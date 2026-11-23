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
| `sabiroute-groq` | `groq/openai/gpt-oss-120b` | `GROQ_API_KEY` | **2026-11-23 probe: OK — real non-empty completion** |
| `sabiroute-together` | `together_ai/openai/gpt-oss-120B` | `TOGETHERAI_API_KEY` | 2026-11-23 probe: HTTP 401 |
| `sabiroute-deepinfra` | `deepinfra/meta-llama/Meta-Llama-3-70B-Instruct` | `DEEPINFRA_API_KEY` | 2026-11-23 probe: HTTP 402, positive balance required |
| `sabiroute-kimi` | `moonshot/kimi-k3.1-pro` | `MOONSHOT_API_KEY` | 2026-11-23 probe: HTTP 429 `exceeded_current_quota_error` — account **suspended, insufficient balance**. Key itself is valid (`/models` returns 200). The previously configured `moonshot-v1-128k` is **retired** and absent from that list. Two separate problems; the model id is fixed, the balance is not |
| `sabiroute-minimax` | `minimax/MiniMax-M2.1` | `MINIMAX_API_KEY` | 2026-11-23 probe: HTTP 402, insufficient balance |
| `sabiroute-cloudflare` | `cloudflare/@cf/meta/llama-3.3-70b-instruct-fp8-fast` | `CLOUDFLARE_API_KEY`, `CLOUDFLARE_ACCOUNT_ID` | **2026-11-23 probe: OK — real non-empty completion** |
| `sabiroute-openrouter` | `openrouter/google/gemini-3.8-flash` | `OPENROUTER_API_KEY` | **2026-11-23 probe: OK — non-empty completion once the output budget exceeds its reasoning trace** |
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

Phase 02 is **6 of 14 verified** as of 2026-11-23: `sabiroute-groq`,
`sabiroute-cloudflare`, `sabiroute-openrouter`, `sabiroute-nvidia`,
`sabiroute-cohere` and `sabiroute-pollinations` each returned a real non-empty
completion.

### A correction worth keeping

An earlier run of the same probe that day reported **4 of 14**, marking Groq and
OpenRouter as returning HTTP 200 with empty assistant text. That result was an
**artefact of the probe, not a provider fault**: both are reasoning models that
spend their output budget on a reasoning trace before emitting any `content`.
With `max_tokens` capped at 16, the whole budget went to reasoning and `content`
came back empty with `finish_reason: "length"`.

The probe now starts at 64 tokens and escalates once to 512 when it sees an
empty `content` alongside a length stop. A measurement that cannot tell "the
model refused" from "I did not give it room to answer" will keep producing this
error, and it errs in the direction that looks like a failing provider.

This also supersedes the counts of 1 and of 3 recorded earlier: those tracked
what this document said, not what the providers did.

### What still blocks the other eight

| Cause | Aliases | Fixable here? |
|---|---|---|
| Account balance (401/402/429) | openai, deepinfra, minimax, huggingface, cerebras | No — payment only |
| Invalid credential | together (401, "Invalid API key provided") | No — needs a new key |
| Account suspended for balance | kimi (429) | No — recharge |
| Provider degraded | gemini (503 "high demand", 3/3 attempts) | No — wait and re-probe |

Six of the eight are account state and **no code change moves any of them**.
Per-alias detail and an ask-ordering live in
`artifacts/PHASE02-PROVIDER-REQUIREMENTS-2026-11-23.md`.

### What "working" has to mean

- **A set credential is not a working alias.** All fourteen variables are set;
  eight aliases still fail.
- **HTTP 200 is not a working alias** — and an empty completion is not a
  completion. But check *why* it is empty before blaming the provider.

Do not raise this count without re-running the probe and recording the date.
