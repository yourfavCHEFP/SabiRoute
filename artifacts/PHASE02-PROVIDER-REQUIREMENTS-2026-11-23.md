# Phase 02 — what each blocked alias needs

**As of 2026-11-23.** Every figure here comes from one real, minimal completion
per alias (`scripts/probe_provider_aliases.py`, `max_tokens` 16, 25s cap, no
retries). Nothing is inferred from documentation.

**Current state: 4 of 14 aliases return a real non-empty completion.**
Ten are blocked. Six of those ten are blocked purely on account balance, and
**no code change moves any of them.**

All fourteen credential variables are set in the environment, so nothing here is
a missing-secret problem. It is an account-state problem.

## Working today — 4

| Alias | Model | Latency |
|---|---|---|
| `sabiroute-cloudflare` | `cloudflare/@cf/meta/llama-3.3-70b-instruct-fp8-fast` | 2.6s |
| `sabiroute-nvidia` | `nvidia_nim/nvidia/nemotron-3.5-bolt-e4b` | 1.0s |
| `sabiroute-cohere` | `cohere_chat/command-a-03-2025` | 2.9s |
| `sabiroute-pollinations` | `openai/gpt-6-luna` @ Pollinations base | 1.2s |

Three of these are free-tier access paths. That matters for the ask below: the
gateway is demonstrably functional, and it is functional on the tiers that
require no payment.

## Blocked on money — 6

These returned a real 402 or a credit-exhausted 429. Only payment unblocks them.

| Alias | Credential | Result | Ask |
|---|---|---|---|
| `sabiroute-openai` | `OPENAI_API_KEY` | 429 — "You have no credits remaining" | Add credit |
| `sabiroute-deepinfra` | `DEEPINFRA_API_KEY` | 402 — "You need positive balance" | Add balance |
| `sabiroute-minimax` | `MINIMAX_API_KEY` | 402 — "insufficient balance" | Add balance |
| `sabiroute-huggingface` | `HF_TOKEN` | 402 — "Purchase pre-paid credits" | Buy credits |
| `sabiroute-cerebras` | `CEREBRAS_API_KEY` | 402 — "Payment required" | Add payment method |
| `sabiroute-openrouter` | `OPENROUTER_API_KEY` | 402 on full-length requests | Add credit (see caveat) |

**OpenRouter caveat, so nobody funds the wrong thing.** OpenRouter also returns
**HTTP 200 with empty assistant text** at small `max_tokens`, because the
configured model is a reasoning model that spends its budget on
`reasoning_content` and returns an empty `content` field. Topping up the account
alone may not make this alias usable — the model choice or the output handling
likely needs changing too. Treat it as two problems, not one.

## Blocked but NOT money — 3

These are fixable without a single dollar and are the highest-value work
available in Phase 02.

| Alias | Result | What it actually needs |
|---|---|---|
| `sabiroute-together` | 401 | A valid credential. `TOGETHERAI_API_KEY` is set but rejected — likely revoked, expired, or issued for a different account. Re-issue it. |
| `sabiroute-groq` | 200, empty content | Not an auth problem; the provider answered. Investigate whether the configured model id returns content in the `content` field or only in a reasoning field, same class of issue as OpenRouter. |
| `sabiroute-kimi` | 429 | Check the account's rate-limit tier and billing state. A 429 that is not credit exhaustion means a plan limit. |

## Blocked on the provider — 1

| Alias | Result | What it needs |
|---|---|---|
| `sabiroute-gemini` | 503 "experiencing high demand", then a 25s timeout | Nothing purchasable. The provider is degraded. Re-probe later; it was verified working on 2026-10-08. |

## What to ask for, in priority order

If someone offers help, this is the order that buys the most:

1. **`sabiroute-together` — a working key.** Free. One credential re-issue takes
   the count to 5 and proves the whole auth path for another provider family.
2. **`sabiroute-groq` — an investigation, not money.** Free. It answers 200, so
   the account is fine; the output shape is the problem. Takes the count to 6.
3. **Any one of the four 402s** (`deepinfra`, `minimax`, `huggingface`,
   `cerebras`) — typically the smallest top-up on offer. Each takes the count up
   by one.
4. **`sabiroute-openai`** — most expensive and most useful for credibility, since
   it is the reference provider for the OpenAI-compatible contract.

**Ceiling without payment: 6 of 14.** Items 1 and 2 are free and nobody has done
them yet.

## What "working" has to mean

Two traps that have already corrupted this number once:

- **A set credential is not a working alias.** All fourteen are set; ten fail.
- **HTTP 200 is not a working alias.** Groq and OpenRouter both returned 200 with
  empty content. An empty completion is not a completion.

The probe reports `EMPTY_CONTENT` as a distinct outcome for exactly this reason.
Anyone quoting a higher Phase 02 number should be asked which probe produced it
and on what date.

To re-derive this table:

```
SABIROUTE_ENV_FILE=/path/to/.env \
PYTHONPATH=/path/to/SabiRoute-claude-fix/src \
  /path/to/.venv/bin/python scripts/probe_provider_aliases.py
```
