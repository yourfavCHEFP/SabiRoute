# Sprint 1 — Provider Alias Verification (2026-11-22)

## Result: 6/14 STABLE VERIFIED (was 4/14 at sprint start); gemini intermittent

### Verified (HTTP 200 through SabiRoute gateway)
| Alias | Model | Status |
|---|---|---|
| sabiroute-groq | groq/openai/gpt-oss-120b | ✅ |
| sabiroute-gemini | gemini/gemini-3.8-flash | ⚠️ INTERMITTENT (200 in 2 of 4 runs; 503 transient otherwise) |
| sabiroute-cloudflare | cloudflare/@cf/meta/llama-3.3-70b-instruct-fp8-fast | ✅ |
| sabiroute-openrouter | openrouter/google/gemini-3.8-flash | ✅ |
| sabiroute-cohere | cohere_chat/command-a-03-2025 | ✅ |
| sabiroute-nvidia | nvidia_nim/nvidia/nemotron-3.5-bolt-e4b | ✅ |
| sabiroute-pollinations | openai/openai (Pollinations alias) | ✅ |

### Blocked — external account/billing (no code defect remains)
| Alias | HTTP | Exact upstream cause |
|---|---|---|
| sabiroute-openai | 429 | "You have no credits remaining" |
| sabiroute-minimax | 402 | "insufficient balance (1008)" |
| sabiroute-cerebras | 402 | "Payment required to access this resource" |
| sabiroute-deepinfra | 402 | "You need positive balance to do inference" |
| sabiroute-kimi | 429 | "account ... is suspended due to insufficient balance" |
| sabiroute-huggingface | 402 | "Purchase pre-paid credits or subscribe to PRO" |

### Blocked — invalid credential
| Alias | HTTP | Cause |
|---|---|---|
| sabiroute-together | 401 | "Invalid API key provided" (reset at together.ai) |

## Root causes fixed this sprint (zero cost)
1. **Stale proxy master key** — proxy was running with the pre-rotation `LITELLM_MASTER_KEY`, so every gateway→proxy call was rejected. Restarted proxy with current `.env`.
2. **Incomplete proxy config** — `config/litellm-proxy.example.yaml` had only 10 aliases (missing minimax, cloudflare, openrouter, huggingface, cerebras; contained a bogus `sabiroute-claude`). Regenerated from `config/config.yaml` as single source of truth → all 14.
3. **Retired model names** — fixed:
   - pollinations: `openai/gpt-4o-mini` → `openai/openai` (Pollinations alias) → **now works**
   - minimax: `MiniMax-M2.1` → `MiniMax-M3` (M2.1/M2 both retired 404) → now correct, blocked by balance
   - cerebras: `llama3-70b-instruct` → `gpt-oss-120b` (account exposes only gpt-oss-120b, qwen-3.8-27b) → now correct, blocked by payment

## Reproducibility
- Proxy: `litellm --config config/litellm-proxy.example.yaml --port 4000 --host 127.0.0.1`
- Proxy config is generated from `config/config.yaml`; both contain `os.environ/` references only (no secrets).
- Gateway loads `.env` at startup — restart required after any key change.

## Evidence labels
- VERIFIED BY RUNTIME: the 7 HTTP 200 results and 7 failure codes/messages above.
- VERIFIED BY INSPECTION: proxy config model count (14) and config.yaml model strings.
- UNPROVEN: long-term model availability; provider-side quota changes.
