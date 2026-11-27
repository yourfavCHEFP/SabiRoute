# Provider configuration and verification

`config/config.yaml` is the single runtime source of truth for deployment
aliases and LiteLLM provider/model identifiers. LiteLLM is pointed at this same
file by Compose. The files under `config/models/` are not loaded by the current
runtime; changing one of those fragments does not add or update a deployment.

The registry currently contains these configured aliases:

| SabiRoute alias | LiteLLM model | Credential variable | Runtime evidence |
| --- | --- | --- | --- |
| `sabiroute-openai` | `openai/gpt-6-luna` | `OPENAI_API_KEY` | Configured; prior request returned no credits |
| `sabiroute-gemini` | `gemini/gemini-3.8-flash` | `GEMINI_API_KEY` | Real completion previously verified through SabiRoute and LiteLLM |
| `sabiroute-groq` | `groq/openai/gpt-oss-120b` | `GROQ_API_KEY` | Configured; unverified |
| `sabiroute-together` | `together_ai/openai/gpt-oss-120B` | `TOGETHERAI_API_KEY` | Configured; unverified |
| `sabiroute-deepinfra` | `deepinfra/meta-llama/Meta-Llama-3-70B-Instruct` | `DEEPINFRA_API_KEY` | Configured; unverified |
| `sabiroute-kimi` | `moonshot/moonshot-v1-128k` | `MOONSHOT_API_KEY` | Configured; unverified |
| `sabiroute-minimax` | `minimax/MiniMax-M2.1` | `MINIMAX_API_KEY` | Configured; unverified |
| `sabiroute-cloudflare` | `cloudflare/@cf/meta/llama-3.3-70b-instruct-fp8-fast` | `CLOUDFLARE_API_KEY`, `CLOUDFLARE_ACCOUNT_ID` | Configured; unverified |
| `sabiroute-openrouter` | `openrouter/google/gemini-3.8-flash` | `OPENROUTER_API_KEY` | Configured; unverified |
| `sabiroute-huggingface` | `huggingface/meta-llama/Llama-3.3-70B-Instruct` | `HF_TOKEN` | Configured; unverified |
| `sabiroute-cerebras` | `cerebras/llama3-70b-instruct` | `CEREBRAS_API_KEY` | Configured; unverified |
| `sabiroute-nvidia` | `nvidia_nim/meta/llama3-70b-instruct` | `NVIDIA_NIM_API_KEY` | Configured; unverified |
| `sabiroute-cohere` | `cohere_chat/command-a-03-2025` | `COHERE_API_KEY` | Configured; unverified |
| `sabiroute-pollinations` | `openai/gpt-6-luna` at the configured Pollinations API base | `POLLINATION_API_KEY` | Configured; unverified |

“Configured” means the alias and credential reference exist in YAML. It does not
mean the credential is present, the account has quota, or a live completion has
passed. The SabiRoute registry preserves environment references and resolves
provider credentials only at the LiteLLM request boundary. Never put key values
in YAML, reports, or terminal output.

The provider verification script can test one named deployment, but it also
writes provider error details to `reports/provider_verification.json`. Review
and sanitize that report before sharing it. Avoid broad provider runs unless you
intend to make a request to every configured provider that has a credential.

Phase 02 is therefore **partially verified**: Gemini has real-runtime evidence;
OpenAI is configured but currently out of credits; the other listed integrations
still need intentional validation before being described as working providers.
