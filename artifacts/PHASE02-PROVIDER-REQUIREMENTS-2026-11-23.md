# Phase 02 — what each blocked alias needs

**As of 2026-11-23.** Every figure comes from a real, minimal completion per
alias (`scripts/probe_provider_aliases.py`), not from documentation.

**Current state: 6 of 14 aliases return a real non-empty completion.**
Eight are blocked. **Six of the eight are account state and no code change
moves any of them.**

All fourteen credential variables are set, so nothing here is a missing-secret
problem.

## Working today — 6

| Alias | Model | Latency |
|---|---|---|
| `sabiroute-groq` | `groq/openai/gpt-oss-120b` | 4.0s |
| `sabiroute-cloudflare` | `cloudflare/@cf/meta/llama-3.3-70b-instruct-fp8-fast` | 1.0s |
| `sabiroute-openrouter` | `openrouter/google/gemini-3.8-flash` | 5.6s |
| `sabiroute-nvidia` | `nvidia_nim/nvidia/nemotron-3.5-bolt-e4b` | 3.5s |
| `sabiroute-cohere` | `cohere_chat/command-a-03-2025` | 3.0s |
| `sabiroute-pollinations` | `openai/gpt-6-luna` @ Pollinations base | 3.3s |

At least four of these are free-tier access paths. The gateway is demonstrably
functional without anyone paying for it.

**Groq and OpenRouter were wrongly reported as failing earlier the same day.**
Both are reasoning models that spend their output budget on a reasoning trace
before emitting `content`; at a 16-token cap the content came back empty. They
work at 64-512 tokens. The probe now escalates its budget instead of concluding
from a length stop.

## Blocked on money — 5

| Alias | Credential | Result | Ask |
|---|---|---|---|
| `sabiroute-openai` | `OPENAI_API_KEY` | 429 — "You have no credits remaining" | Add credit |
| `sabiroute-deepinfra` | `DEEPINFRA_API_KEY` | 402 — "You need positive balance" | Add balance |
| `sabiroute-minimax` | `MINIMAX_API_KEY` | 402 — "insufficient balance" | Add balance |
| `sabiroute-huggingface` | `HF_TOKEN` | 402 — "Purchase pre-paid credits" | Buy credits |
| `sabiroute-cerebras` | `CEREBRAS_API_KEY` | 402 — "Payment required" | Add payment method |

## Blocked on a credential — 1

| Alias | Result | What it needs |
|---|---|---|
| `sabiroute-together` | 401 — **"Invalid API key provided"** | A new key from the Together account. The variable is set; the key itself is rejected. Nothing on this side fixes it, and no amount of code work will. |

## Blocked on account tier — 1

| Alias | Result | What it needs |
|---|---|---|
| `sabiroute-kimi` | 429 (not a credit-exhaustion message) | Check the account's rate-limit tier and billing state. A 429 that is not about credits is a plan limit. |

## Blocked on the provider — 1

| Alias | Result | What it needs |
|---|---|---|
| `sabiroute-gemini` | 503 "experiencing high demand", then a 25s timeout | Nothing purchasable. The provider is degraded today. Re-probe later; it was verified working on 2026-10-08. |

## What to ask for, in priority order

1. **`sabiroute-together` — one key.** Free to ask for, one action, takes the
   count to 7 and proves the auth path for another provider family.
2. **`sabiroute-kimi` — check the plan.** Free to check. Likely takes the count
   to 8.
3. **Any one of the five 402/429 accounts.** Smallest top-up on offer. Each adds
   one.
4. **`sabiroute-openai`** — most expensive, most useful for credibility, since it
   is the reference provider for the OpenAI-compatible contract.
5. **`sabiroute-gemini`** — free; just wait and re-probe.

**Ceiling without payment: 8 of 14.** Items 1, 2 and 5 cost nothing and are
outstanding only because nobody has done them.

## What "working" has to mean

Three ways this number has already gone wrong:

- **A set credential is not a working alias.** All fourteen are set; eight fail.
- **HTTP 200 is not a working alias.** An empty completion is not a completion.
- **But a low output cap is not a broken provider.** That was the mistake that
  cost two aliases here. Before concluding from an empty response, check
  `finish_reason`. If it is `length`, the probe ran out of room, not out of
  provider.

Anyone quoting a Phase 02 number should be asked which probe produced it and on
what date.

To re-derive this table:

```
SABIROUTE_ENV_FILE=/path/to/.env \
PYTHONPATH=/path/to/SabiRoute-claude-fix/src \
  /path/to/.venv/bin/python scripts/probe_provider_aliases.py
```
