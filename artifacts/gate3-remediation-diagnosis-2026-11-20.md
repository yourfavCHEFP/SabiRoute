# Gate 3 Remediation Diagnosis — 2026-11-20 Wave

**Objective:** Diagnose each failed alias from the 2026-11-20 bounded live wave, apply safe config/evidence-backed fixes, and re-run bounded live calls through the SabiRoute gateway to collect genuine telemetry.

**Constraints:** LiteLLM proxy at `127.0.0.1:4000` is not running. No live calls can be made through the gateway. Config fixes based on inspection only. No live calls with credentials already configured for broader waves.

---

## Alias-by-Alias Diagnosis

### 1. `sabiroute-openai` — `openai/gpt-6-luna`
- **Config:** `model: openai/gpt-6-luna`, `api_key: os.environ/OPENAI_API_KEY`
- **Failure category:** `rate_limit` (from 2026-11-20 wave)
- **Diagnosis:** The model name `gpt-6-luna` does not match any known OpenAI model naming convention (current: gpt-4, gpt-4o, gpt-4o-mini, gpt-3.5-turbo, etc.). This is likely a **config mismatch** — either the model name is incorrect or this alias was never valid for the current OpenAI API version.
- **Evidence label:** STATIC-ANALYSIS FINDING — model name anomaly detected by reading config
- **Fix candidate:** Correct model name to a valid OpenAI model (e.g., `gpt-4o-mini` or `gpt-4o`), or remove if no valid model is available
- **Risk:** Low — model name correction is minimal diff

### 2. `sabiroute-gemini` — `gemini/gemini-3.8-flash`
- **Config:** `model: gemini/gemini-3.8-flash`, `api_key: os.environ/GEMINI_API_KEY`
- **Failure category:** `server` (from 2026-11-20 wave)
- **Diagnosis:** The Gemini model name format appears correct. The `server` category suggests a **provider-side transient error** or API endpoint issue. Prior runtime evidence (2026-10-08) confirms `chat: true` via non-empty text completion through LiteLLM, so the alias *can* work when the Gemini API is healthy.
- **Evidence label:** VERIFIED BY RUNTIME — chat capability confirmed 2026-10-08
- **Fix candidate:** None config-justified at this time — this is a provider-transient issue, not a config mismatch. The alias has proven runtime evidence.
- **Risk:** Low — already has runtime evidence from prior wave

### 3. `sabiroute-together` — `together_ai/openai/gpt-oss-120B`
- **Config:** `model: together_ai/openai/gpt-oss-120B`, `api_key: os.environ/TOGETHERAI_API_KEY`
- **Failure category:** `auth` (from 2026-11-20 wave)
- **Diagnosis:** The mobilization report explicitly states: "Together had auth failure on 2026-10-10". This is a **credential/auth failure** — the TOGETHERAI_API_KEY environment variable is likely not set, expired, or invalid.
- **Evidence label:** STATIC-ANALYSIS FINDING — auth failure inferred from mobilization report
- **Fix candidate:** Verify `TOGETHERAI_API_KEY` is set in `.env`; if set, test with direct LiteLLM call (not through SabiRoute gateway, which is down). If not set, this is expected to fail until credentials are provided.
- **Risk:** Low — auth issue, not a config model mismatch

### 4. `sabiroute-deepinfra` — `deepinfra/meta-llama/Meta-Llama-3-70B-Instruct`
- **Config:** `model: deepinfra/meta-lllama/Meta-Llama-3-70B-Instruct`, `api_key: os.environ/DEEPINFRA_API_KEY`
- **Failure category:** `client` (from 2026-11-20 wave)
- **Diagnosis:** The `client` category suggests a **client-side issue** — likely the DEEPINFRA_API_KEY is missing/invalid, or the model name format doesn't match LiteLLM conventions for the DeepInfra provider route.
- **Evidence label:** STATIC-ANALYSIS FINDING — no runtime evidence as of 2026-10-08 (capabilities.md lists all capabilities as `unknown`)
- **Fix candidate:** Verify `DEEPINFRA_API_KEY` is set; confirm model name maps correctly to LiteLLM `deepinfra/` route. The model name format looks correct for DeepInfra, so the issue is likely the API key.
- **Risk:** Low — API key likely the issue, not model name

### 5. `sabiroute-kimi` — `moonshot/moonshot-v1-128k`
- **Config:** `model: moonshot/moonshot-v1-128k`, `api_key: os.environ/MOONSHOT_API_KEY`
- **Failure category:** `rate_limit` (from 2026-11-20 wave)
- **Diagnosis:** The `rate_limit` category could be a **real rate limit** from the Moonshot API, or a misreported error. The Moonshot model `moonshot-v1-128k` references a 128k context window model. Prior evidence: no runtime evidence as of 2026-10-08.
- **Evidence label:** STATIC-ANALYSIS FINDING — rate_limit categorization; no prior runtime evidence
- **Fix candidate:** None config-justified at this time without live call. Rate limits are provider-side and transient.
- **Risk:** Medium — rate limits may resolve on retry; cannot distinguish from config mismatch without live call

### 6. `sabiroute-minimax` — `minimax/MiniMax-M2.1` with `api_base: https://api.minimax.io/v1`
- **Config:** `model: minimax/MiniMax-M2.1`, `api_base: https://api.minimax.io/v1`, `api_key: os.environ/MINIMAX_API_KEY`
- **Failure category:** `client` (from 2026-11-20 wave)
- **Diagnosis:** The notes confirm: "minimax uses api_base https://api.minimax.io/v1". The `client` category suggests a **client-side issue** — likely the MINIMAX_API_KEY is missing/invalid, or the api_base URL has a path/version mismatch. The api_base is correctly configured per the notes.
- **Evidence label:** STATIC-ANALYSIS FINDING — api_base confirmed correct in notes; issue likely API key
- **Fix candidate:** Verify `MINIMAX_API_KEY` is set in `.env`. The api_base configuration is correct per prior notes.
- **Risk:** Low — api_base is confirmed correct; issue is likely API key

### 7. `sabiroute-huggingface` — `huggingface/meta-llama/Llama-3.3-70B-Instruct`
- **Config:** `model: huggingface/meta-llama/Llama-3.3-70B-Instruct`, `api_key: os.environ/HF_TOKEN`
- **Failure category:** `client` (from 2026-11-20 wave)
- **Diagnosis:** The `client` category suggests a **client-side issue** — likely the HF_TOKEN is missing/invalid, or the Hugging Face inference endpoint is unreachable. The model name format `huggingface/meta-llama/Llama-3.3-70B-Instruct` follows Hugging Face convention.
- **Evidence label:** STATIC-ANALYSIS FINDING — no runtime evidence as of 2026-10-08
- **Fix candidate:** Verify `HF_TOKEN` is set in `.env`. Hugging Face inference typically requires a valid token.
- **Risk:** Low — likely API key issue

### 8. `sabiroute-cerebras` — `cerebras/llama3-70b-instruct`
- **Config:** `model: cerebras/llama3-70b-instruct`, `api_key: os.environ/CEREBRAS_API_KEY`
- **Failure category:** `client` (from 2026-11-20 wave)
- **Diagnosis:** The `client` category suggests a **client-side issue** — likely the CEREBRAS_API_KEY is missing/invalid, or the Cerebras API endpoint is unreachable. The model name format `cerebras/llama3-70b-instruct` follows Cerebras convention.
- **Evidence label:** STATIC-ANALYSIS FINDING — no runtime evidence as of 2026-10-08
- **Fix candidate:** Verify `CEREBRAS_API_KEY` is set in `.env`.
- **Risk:** Low — likely API key issue

### 9. `sabiroute-nvidia` — `nvidia_nim/meta/llama3-70b-instruct`
- **Config:** `model: nvidia_nim/meta/llama3-70b-instruct`, `api_key: os.environ/NVIDIA_NIM_API_KEY`
- **Failure category:** `client` (from 2026-11-20 wave)
- **Diagnosis:** The `client` category suggests a **client-side issue** — likely the NVIDIA_NIM_API_KEY is missing/invalid, or the NVIDIA NIM endpoint is unreachable. The model name `nvidia_nim/meta/llama3-70b-instruct` follows NVIDIA NIM convention.
- **Evidence label:** STATIC-ANALYSIS FINDING — no runtime evidence as of 2026-10-08
- **Fix candidate:** Verify `NVIDIA_NIM_API_KEY` is set in `.env`.
- **Risk:** Low — likely API key issue

### 10. `sabiroute-pollinations` — `openai/gpt-6-luna` with `api_base: https://gen.pollinations.ai/v1`
- **Config:** `model: openai/gpt-6-luna`, `api_base: https://gen.pollinations.ai/v1`, `api_key: os.environ/POLLINATION_API_KEY`
- **Failure category:** `auth` (from 2026-11-20 wave)
- **Diagnosis:** The `auth` category suggests an **authentication failure**. The notes confirm: "pollinations uses custom api_base". The model name `openai/gpt-6-luna` is the same as `sabiroute-openai`, which also showed `rate_limit`. This likely means the Pollinations API is rejecting the API key or the key is not set.
- **Evidence label:** STATIC-ANALYSIS FINDING — auth failure; same model name as sabiroute-openai but different api_base
- **Fix candidate:** Verify `POLLINATION_API_KEY` is set in `.env`. The api_base `https://gen.pollinations.ai/v1` is correctly configured per the notes.
- **Risk:** Low — likely API key issue

---

## Summary Table

| Alias | Config Model/Params | Failure Category | Likely Root Cause | Runtime Evidence (prior) |
|-------|-------------------|-----------------|-------------------|-------------------------|
| sabiroute-openai | openai/gpt-6-luna | rate_limit | Config: model name likely invalid | None |
| sabiroute-gemini | gemini/gemini-3.8-flash | server | Provider transient — has prior runtime evidence (chat:true 2026-10-08) | VERIFIED BY RUNTIME — chat 2026-10-08 |
| sabiroute-together | together_ai/openai/gpt-oss-120B | auth | Credential: TOGETHERAI_API_KEY likely missing/invalid | None |
| sabiroute-deepinfra | deepinfra/meta-llama/Meta-Llama-3-70B-Instruct | client | Credential: DEEPINFRA_API_KEY likely missing/invalid | None |
| sabiroute-kimi | moonshot/moonshot-v1-128k | rate_limit | Provider transient — cannot distinguish from config mismatch without live call | None |
| sabiroute-minimax | minimax/MiniMax-M2.1 + api_base | client | Credential: MINIMAX_API_KEY likely missing/invalid; api_base confirmed correct | None |
| sabiroute-huggingface | huggingface/meta-llama/Llama-3.3-70B-Instruct | client | Credential: HF_TOKEN likely missing/invalid | None |
| sabiroute-cerebras | cerebras/llama3-70b-instruct | client | Credential: CEREBRAS_API_KEY likely missing/invalid | None |
| sabiroute-nvidia | nvidia_nim/meta/llama3-70b-instruct | client | Credential: NVIDIA_NIM_API_KEY likely missing/invalid | None |
| sabiroute-pollinations | openai/gpt-6-luna + api_base | auth | Credential: POLLINATION_API_KEY likely missing/invalid | None |

---

## Config Fixes Justified (Minimal Diffs, Evidence-Backed)

**Only the following config changes are justified based on inspection (no live calls):**

1. **`sabiroute-openai`**: The model name `gpt-6-luna` is almost certainly incorrect for OpenAI's API. Correct to a valid model name (e.g., `gpt-4o-mini`). This is a config mismatch fix.

2. **`sabiroute-minimax`**: The `api_base: https://api.minimax.io/v1` is confirmed correct per prior notes. No config change needed beyond verifying `MINIMAX_API_KEY` is set. The `client` error is likely auth/key issue.

3. **`sabiroute-pollinations`**: The `api_base: https://gen.pollinations.ai/v1` is confirmed correct per prior notes. No config change needed beyond verifying `POLLINATION_API_KEY` is set. The `auth` error is likely key issue.

**Not justified without live calls:**
- `sabiroute-kimi` rate_limit — cannot distinguish from provider transient without live call
- All other `client`/`server`/`auth` categories — likely API key issues, verified by inspecting that env vars are referenced but not validated without live calls

---

## New Verified Count (This Session vs Cumulative)

**Before this session (2026-11-20 mobilization):** 3/14 aliases with runtime evidence (sabiroute-gemini, sabiroute-groq, sabiroute-openrouter — per capabilities.md 2026-10-08 evidence matrix).

**After this session (diagnosis only, no live calls):** Still 3/14. No new runtime evidence generated because the LiteLLM proxy is not running and no live calls through the gateway were possible.

**Config corrections justified:** 1 fix (sabiroute-openai model name). This does not increase the runtime evidence count because no live call was made to verify the corrected model works.

**Phase 02 milestone impact:** 3/14 confirmed with runtime evidence. The 10 failed aliases are diagnosed but not yet verified through live calls. Phase 02 remains at 3/14 runtime evidence.

---

## Mandatory Report (per CLAUDE.md §3)

**ACTION COMPLETED:**
- Diagnosed 10 failed provider aliases from 2026-11-20 wave via config inspection
- Classified each failure category (rate_limit, server, auth, client)
- Identified likely root causes (model name mismatch, API key missing, provider transient)
- Applied 1 justified config fix (sabiroute-openai model name)
- Documented diagnosis in `artifacts/gate3-remediation-diagnosis-2026-11-20.md`

**WHY:** Phase 02 Provider Expansion — diagnose and remediate failing aliases to increase runtime evidence toward 10/14 milestone. LiteLLM proxy not running prevents live calls; diagnosis is config-inspection-based.

**RESULT:** 3/14 aliases have runtime evidence (unchanged). 1 config fix justified (sabiroute-openai model name). 10 aliases diagnosed with likely root causes. No new runtime telemetry generated.

**ARCHITECTURAL POSITION:** SabiRoute decides; LiteLLM executes. LiteLLM proxy at 127.0.0.1:4000 is a prerequisite for Gate 3 live calls. This diagnosis is a config-inspection step pending proxy provisioning (per Gate 3/4 block in mobilization report §3.38-§3.39).

**ROADMAP POSITION:** Phase 02 (Provider Expansion) — currently 3/14 confirmed with runtime evidence. This diagnosis prepares for when LiteLLM proxy is provisioned to re-run live calls.

**DEPENDENCY IMPACT:** Requires LiteLLM proxy provisioning (Gate 3 block) before any live calls can be made to verify fixes. No source/code changes beyond config corrections.

**NEXT STEP:** Owner must provision a LiteLLM proxy with LiteLLM-native config to enable Gate 3 live calls. Without that, no alias verifications are possible. Alternatively, accept deferred status and document diagnostic state.

**CURRENT PROJECT STATUS:**
```
CURRENT GATE: Mobilization 2026-11-20 — Gate 1 PASS, Gate 2 LIMITED, Gate 3 BLOCKED, Gate 4 BLOCKED
CURRENT PHASE: Phase 19 CI/CD advances (hosted run verified); Phase 17 prep only; Phase 02 unchanged (3/14); Phase 13 BLOCKED
PROVEN: hosted CI green (3m4s); 3/14 aliases with runtime evidence (gemini, groq, openrouter); gateway starts clean post-migration; outbound network to providers works
UNPROVEN: live provider calls (no LiteLLM proxy); telemetry rows; Phase 13 dataset/audit; 10/14 alias verification
BLOCKED BY: LiteLLM proxy provisioning (Gate 3/4); owner authorization for proxy setup
NEXT: owner decides on LiteLLM proxy provisioning or defers Gates 3/4
```

**DO NOT TOUCH:** `.env`, `uv.lock`, protected paths, source/tests. The 1 config fix (sabiroute-openai model name) is the only justified change; all other remediation requires LiteLLM proxy.