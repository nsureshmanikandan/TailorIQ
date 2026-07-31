# Dual-Endpoint LLM Client Design

**Date:** 2026-07-31
**Status:** Approved
**Scope:** `backend/app/services/llm_service.py`, `backend/app/config.py`, `backend/.env`, `backend/.env.example`

---

## Problem

`gpt-5.4-mini` is deployed on Azure AI Foundry using the new OpenAI-compatible v1 endpoint
(`/openai/v1`), which requires the standard `AsyncOpenAI` client and no `api-version` parameter.
The existing models (`gpt-5.4-nano`, `gpt-5-mini`) use the classic Azure endpoint requiring
`AsyncAzureOpenAI` with an `api-version`. The codebase must support all three without any
code changes when switching models.

---

## Decision

**Approach A — Auto-detect from the endpoint URL.**

If `AZURE_OPENAI_ENDPOINT` (stripped of trailing slash) ends with `/openai/v1`, instantiate
`AsyncOpenAI(base_url=endpoint, api_key=...)`. Otherwise instantiate
`AsyncAzureOpenAI(azure_endpoint=endpoint, api_key=..., api_version=...)`.

Zero new environment variables. The endpoint URL itself is the signal. `AZURE_OPENAI_API_VERSION`
is retained in config for classic-endpoint profiles and silently ignored by v1 profiles.

---

## Architecture

### `LLMService.__init__` — dual-client fork

```
endpoint = settings.AZURE_OPENAI_ENDPOINT.rstrip("/")

if endpoint.endswith("/openai/v1"):
    client = AsyncOpenAI(base_url=endpoint, api_key=api_key)
else:
    client = AsyncAzureOpenAI(azure_endpoint=endpoint, api_key=api_key, api_version=version)
```

`chat_completion()` is unchanged — both clients expose the identical
`.chat.completions.create(**kwargs)` interface. Reasoning model detection (temperature/seed
skipping), token tracking, and JSON parsing all remain unaffected.

### Unchanged components

| Component | Why untouched |
|---|---|
| `chat_completion()` | Same interface on both clients |
| `_is_reasoning_model()` | `gpt-5.4-mini` correctly returns False (not reasoning) |
| All agents | Read `max_output_tokens` from config; unaware of client type |
| `config.py` | No new fields; `AZURE_OPENAI_API_VERSION` kept, ignored for v1 |

---

## Three Model Profiles

All profiles live in `.env`. To switch: comment the active block, uncomment the target, restart backend.

### Profile A — `gpt-5.4-nano` (ultra-fast, cheapest)

```env
AZURE_OPENAI_ENDPOINT=https://agentforgeai-resource.services.ai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-5.4-nano
AZURE_OPENAI_API_VERSION=2024-12-01-preview
LLM_MAX_TOKENS_RESUME_PARSER=8000
LLM_MAX_TOKENS_JD_PARSER=3000
LLM_MAX_TOKENS_MATCH_SCORING=2000
LLM_MAX_TOKENS_GAP_ANALYSIS=3000
LLM_MAX_TOKENS_ATS_CHECK=1500
LLM_MAX_TOKENS_RESUME_TAILORING=10000
LLM_MAX_TOKENS_CLAIM_VERIFICATION=5000
LLM_MAX_TOKENS_COVER_LETTER=1500
LLM_MAX_TOKENS_INTERVIEW_PREP=6000
```

- Client: `AsyncAzureOpenAI`
- Speed: ~3–4 min total
- Use for: demos, rapid iteration

### Profile B — `gpt-5.4-mini` (sweet spot) ← DEFAULT

```env
AZURE_OPENAI_ENDPOINT=https://agentforgeai-resource.services.ai.azure.com/openai/v1
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-5.4-mini
AZURE_OPENAI_API_VERSION=2024-12-01-preview
LLM_MAX_TOKENS_RESUME_PARSER=8000
LLM_MAX_TOKENS_JD_PARSER=3000
LLM_MAX_TOKENS_MATCH_SCORING=2000
LLM_MAX_TOKENS_GAP_ANALYSIS=3000
LLM_MAX_TOKENS_ATS_CHECK=1500
LLM_MAX_TOKENS_RESUME_TAILORING=10000
LLM_MAX_TOKENS_CLAIM_VERIFICATION=5000
LLM_MAX_TOKENS_COVER_LETTER=1500
LLM_MAX_TOKENS_INTERVIEW_PREP=6000
```

- Client: `AsyncOpenAI` (v1 endpoint auto-detected)
- `AZURE_OPENAI_API_VERSION` present but ignored at runtime
- Token limits: same as nano — not a reasoning model, no hidden chain-of-thought tokens
- Speed: ~3–4 min, higher output quality than nano
- Rate limit: 500K TPM / 500 req/min
- Use for: standard production runs

### Profile C — `gpt-5-mini` (reasoning, highest quality)

```env
AZURE_OPENAI_ENDPOINT=https://agentforgeai-resource.services.ai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-5-mini
AZURE_OPENAI_API_VERSION=2024-12-01-preview
LLM_MAX_TOKENS_RESUME_PARSER=16000
LLM_MAX_TOKENS_JD_PARSER=6000
LLM_MAX_TOKENS_MATCH_SCORING=4000
LLM_MAX_TOKENS_GAP_ANALYSIS=6000
LLM_MAX_TOKENS_ATS_CHECK=3000
LLM_MAX_TOKENS_RESUME_TAILORING=20000
LLM_MAX_TOKENS_CLAIM_VERIFICATION=10000
LLM_MAX_TOKENS_COVER_LETTER=3000
LLM_MAX_TOKENS_INTERVIEW_PREP=12000
```

- Client: `AsyncAzureOpenAI`
- `temperature` and `seed` automatically skipped (reasoning model detection)
- Token limits: 2× nano — reasoning tokens count against `max_completion_tokens`
- Speed: ~8–10 min
- Use for: final resume submissions, highest accuracy

---

## Files Changed

| File | Change |
|---|---|
| `backend/app/services/llm_service.py` | `__init__`: add v1 detection + conditional client instantiation; add `AsyncOpenAI` import |
| `backend/.env` | Replace current single profile with three commented profile blocks; Profile B active by default |
| `backend/.env.example` | Same three-profile layout with placeholder credentials |

---

## Error Handling

No new error cases. Both clients raise the same `openai.*` exceptions already caught by
`retry.py` (`RateLimitError`, `APIConnectionError`, `APITimeoutError`). A misconfigured
endpoint (wrong URL suffix) will surface as an `APIConnectionError` on first call, which
retries then logs clearly.

---

## Out of Scope

- Per-request deployment override (existing `deployment_override` param unchanged)
- Health check endpoint changes
- Frontend changes
- Any database migration
