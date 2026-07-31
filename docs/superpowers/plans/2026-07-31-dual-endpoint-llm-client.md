# Dual-Endpoint LLM Client Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `LLMService` auto-select `AsyncOpenAI` (v1 endpoint) or `AsyncAzureOpenAI` (classic) based on the endpoint URL, enabling three model profiles switchable via `.env` alone.

**Architecture:** Detect endpoint style in `LLMService.__init__` by checking if `AZURE_OPENAI_ENDPOINT` stripped of trailing slashes ends with `/openai/v1`. Both clients expose the identical `.chat.completions.create()` interface so `chat_completion()` is untouched. `.env` and `.env.example` are updated with three commented profile blocks — Profile B (`gpt-5.4-mini`, v1) active by default.

**Tech Stack:** Python 3.11+, `openai` SDK (`AsyncOpenAI` + `AsyncAzureOpenAI`), `pydantic-settings`, pytest, pytest-asyncio.

**Spec:** `docs/superpowers/specs/2026-07-31-dual-endpoint-llm-client-design.md`

---

## Files Changed

| File | Action |
|---|---|
| `backend/tests/unit/test_llm_service_client.py` | Create — unit tests for client selection logic |
| `backend/app/services/llm_service.py` | Modify — add `AsyncOpenAI` import + v1 detection in `__init__` |
| `backend/.env` | Modify — three profile blocks, Profile B active |
| `backend/.env.example` | Modify — three profile blocks, placeholder credentials |

---

## Task 1: Unit tests for client selection

**Files:**
- Create: `backend/tests/unit/test_llm_service_client.py`

- [ ] **Step 1: Create the test file**

```python
"""Unit tests for LLMService dual-endpoint client selection."""

from unittest.mock import MagicMock, patch

import pytest

from app.services.llm_service import LLMService


def _mock_settings(endpoint: str, deployment: str = "test-model") -> MagicMock:
    s = MagicMock()
    s.AZURE_OPENAI_ENDPOINT = endpoint
    s.AZURE_OPENAI_API_KEY.get_secret_value.return_value = "test-key"
    s.AZURE_OPENAI_DEPLOYMENT_NAME = deployment
    s.AZURE_OPENAI_FALLBACK_DEPLOYMENT = ""
    s.AZURE_OPENAI_API_VERSION = "2024-12-01-preview"
    return s


class TestLLMServiceClientSelection:
    """LLMService picks the right client based on endpoint URL."""

    def test_v1_endpoint_uses_async_openai(self):
        settings = _mock_settings(
            "https://resource.services.ai.azure.com/openai/v1"
        )
        with patch("app.services.llm_service.AsyncOpenAI") as mock_v1, \
             patch("app.services.llm_service.AsyncAzureOpenAI") as mock_azure:
            LLMService(settings=settings)
            mock_v1.assert_called_once_with(
                base_url="https://resource.services.ai.azure.com/openai/v1",
                api_key="test-key",
            )
            mock_azure.assert_not_called()

    def test_v1_endpoint_trailing_slash_normalised(self):
        """Trailing slash on v1 endpoint is stripped before comparison."""
        settings = _mock_settings(
            "https://resource.services.ai.azure.com/openai/v1/"
        )
        with patch("app.services.llm_service.AsyncOpenAI") as mock_v1, \
             patch("app.services.llm_service.AsyncAzureOpenAI"):
            LLMService(settings=settings)
            # base_url passed WITHOUT trailing slash
            call_kwargs = mock_v1.call_args.kwargs
            assert call_kwargs["base_url"] == \
                "https://resource.services.ai.azure.com/openai/v1"

    def test_classic_endpoint_uses_async_azure_openai(self):
        settings = _mock_settings(
            "https://resource.services.ai.azure.com/"
        )
        with patch("app.services.llm_service.AsyncAzureOpenAI") as mock_azure, \
             patch("app.services.llm_service.AsyncOpenAI") as mock_v1:
            LLMService(settings=settings)
            mock_azure.assert_called_once_with(
                azure_endpoint="https://resource.services.ai.azure.com/",
                api_key="test-key",
                api_version="2024-12-01-preview",
            )
            mock_v1.assert_not_called()

    def test_classic_endpoint_no_trailing_slash(self):
        """Classic endpoint without trailing slash still uses AsyncAzureOpenAI."""
        settings = _mock_settings(
            "https://resource.services.ai.azure.com"
        )
        with patch("app.services.llm_service.AsyncAzureOpenAI") as mock_azure, \
             patch("app.services.llm_service.AsyncOpenAI") as mock_v1:
            LLMService(settings=settings)
            mock_azure.assert_called_once()
            mock_v1.assert_not_called()
```

- [ ] **Step 2: Run tests — verify they FAIL**

```bash
cd backend
pytest tests/unit/test_llm_service_client.py -v
```

Expected: `ImportError` or `AssertionError` because `AsyncOpenAI` is not yet imported in `llm_service.py` and the v1 branch doesn't exist.

---

## Task 2: Implement dual-client detection in `llm_service.py`

**Files:**
- Modify: `backend/app/services/llm_service.py`

- [ ] **Step 1: Update the import line (line 17)**

Replace:
```python
from openai import AsyncAzureOpenAI
```
With:
```python
from openai import AsyncAzureOpenAI, AsyncOpenAI
```

- [ ] **Step 2: Replace the `__init__` client construction block (lines 71–75)**

Replace:
```python
        self._client = AsyncAzureOpenAI(
            azure_endpoint=self._settings.AZURE_OPENAI_ENDPOINT,
            api_key=self._settings.AZURE_OPENAI_API_KEY.get_secret_value(),
            api_version=self._settings.AZURE_OPENAI_API_VERSION,
        )
```

With:
```python
        _endpoint = self._settings.AZURE_OPENAI_ENDPOINT.rstrip("/")
        if _endpoint.endswith("/openai/v1"):
            self._client = AsyncOpenAI(
                base_url=_endpoint,
                api_key=self._settings.AZURE_OPENAI_API_KEY.get_secret_value(),
            )
            logger.info("LLMService: using OpenAI v1 client (endpoint=%s)", _endpoint)
        else:
            self._client = AsyncAzureOpenAI(
                azure_endpoint=self._settings.AZURE_OPENAI_ENDPOINT,
                api_key=self._settings.AZURE_OPENAI_API_KEY.get_secret_value(),
                api_version=self._settings.AZURE_OPENAI_API_VERSION,
            )
            logger.info(
                "LLMService: using Azure OpenAI client (endpoint=%s, api_version=%s)",
                self._settings.AZURE_OPENAI_ENDPOINT,
                self._settings.AZURE_OPENAI_API_VERSION,
            )
```

- [ ] **Step 3: Run tests — verify they PASS**

```bash
cd backend
pytest tests/unit/test_llm_service_client.py -v
```

Expected output:
```
PASSED tests/unit/test_llm_service_client.py::TestLLMServiceClientSelection::test_v1_endpoint_uses_async_openai
PASSED tests/unit/test_llm_service_client.py::TestLLMServiceClientSelection::test_v1_endpoint_trailing_slash_normalised
PASSED tests/unit/test_llm_service_client.py::TestLLMServiceClientSelection::test_classic_endpoint_uses_async_azure_openai
PASSED tests/unit/test_llm_service_client.py::TestLLMServiceClientSelection::test_classic_endpoint_no_trailing_slash
```

- [ ] **Step 4: Run full unit test suite — verify nothing regressed**

```bash
cd backend
pytest tests/unit/ -v
```

Expected: all pre-existing tests still pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/llm_service.py backend/tests/unit/test_llm_service_client.py
git commit -m "feat: auto-detect v1 vs classic Azure endpoint in LLMService"
```

---

## Task 3: Update `.env` — three profiles, Profile B active

**Files:**
- Modify: `backend/.env`

> **SECURITY:** `.env` is in `.gitignore` and must never be committed. Your real `AZURE_OPENAI_API_KEY` value stays in place — only the structure around it changes.

- [ ] **Step 1: Replace the Azure OpenAI + Agent Token Limits section**

The current active block in `.env` (lines 4–37) sets Profile A (nano) or an older layout. Replace the entire Azure OpenAI section + model profile block with this structure, keeping your real API key on the `AZURE_OPENAI_API_KEY` line:

```env
# ─── Azure OpenAI ────────────────────────────────────────────────────────────
AZURE_OPENAI_ENDPOINT=https://agentforgeai-resource.services.ai.azure.com/
AZURE_OPENAI_API_KEY=<your-real-key-unchanged>
AZURE_OPENAI_API_VERSION=2024-12-01-preview
AZURE_OPENAI_FALLBACK_DEPLOYMENT=

# ── Model profiles — comment active block, uncomment target, restart backend ──
#
# PROFILE A — gpt-5.4-nano  (ultra-fast, cheapest, ~3-4 min)
# AZURE_OPENAI_ENDPOINT=https://agentforgeai-resource.services.ai.azure.com/
# AZURE_OPENAI_DEPLOYMENT_NAME=gpt-5.4-nano
# LLM_MAX_TOKENS_RESUME_PARSER=8000
# LLM_MAX_TOKENS_JD_PARSER=3000
# LLM_MAX_TOKENS_MATCH_SCORING=2000
# LLM_MAX_TOKENS_GAP_ANALYSIS=3000
# LLM_MAX_TOKENS_ATS_CHECK=1500
# LLM_MAX_TOKENS_RESUME_TAILORING=10000
# LLM_MAX_TOKENS_CLAIM_VERIFICATION=5000
# LLM_MAX_TOKENS_COVER_LETTER=1500
# LLM_MAX_TOKENS_INTERVIEW_PREP=6000
#
# PROFILE B — gpt-5.4-mini  (sweet spot, ~3-4 min, higher quality) ← DEFAULT
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-5.4-mini
# AZURE_OPENAI_API_VERSION not used — v1 endpoint auto-detected
AZURE_OPENAI_ENDPOINT=https://agentforgeai-resource.services.ai.azure.com/openai/v1
LLM_MAX_TOKENS_RESUME_PARSER=8000
LLM_MAX_TOKENS_JD_PARSER=3000
LLM_MAX_TOKENS_MATCH_SCORING=2000
LLM_MAX_TOKENS_GAP_ANALYSIS=3000
LLM_MAX_TOKENS_ATS_CHECK=1500
LLM_MAX_TOKENS_RESUME_TAILORING=10000
LLM_MAX_TOKENS_CLAIM_VERIFICATION=5000
LLM_MAX_TOKENS_COVER_LETTER=1500
LLM_MAX_TOKENS_INTERVIEW_PREP=6000
#
# PROFILE C — gpt-5-mini  (reasoning, highest quality, ~8-10 min)
# AZURE_OPENAI_ENDPOINT=https://agentforgeai-resource.services.ai.azure.com/
# AZURE_OPENAI_DEPLOYMENT_NAME=gpt-5-mini
# LLM_MAX_TOKENS_RESUME_PARSER=16000
# LLM_MAX_TOKENS_JD_PARSER=6000
# LLM_MAX_TOKENS_MATCH_SCORING=4000
# LLM_MAX_TOKENS_GAP_ANALYSIS=6000
# LLM_MAX_TOKENS_ATS_CHECK=3000
# LLM_MAX_TOKENS_RESUME_TAILORING=20000
# LLM_MAX_TOKENS_CLAIM_VERIFICATION=10000
# LLM_MAX_TOKENS_COVER_LETTER=3000
# LLM_MAX_TOKENS_INTERVIEW_PREP=12000
# ─────────────────────────────────────────────────────────────────────────────
```

Note: The `AZURE_OPENAI_ENDPOINT` at the top of the Azure OpenAI block is overridden by the active profile's `AZURE_OPENAI_ENDPOINT` line. pydantic-settings uses the last definition when a key appears twice in `.env`, so the profile line wins.

> **Wait — pydantic-settings `.env` behaviour:** Last occurrence wins for duplicate keys. Profile B's `AZURE_OPENAI_ENDPOINT=.../openai/v1` appears after the section header value and will override it. Test this by checking the logged endpoint on startup.

- [ ] **Step 2: Restart the backend and verify the correct client is chosen**

```bash
# In the backend terminal — restart uvicorn
# Look for this log line on startup:
# LLMService: using OpenAI v1 client (endpoint=https://agentforgeai-resource.services.ai.azure.com/openai/v1)
```

If you see `using Azure OpenAI client` instead, the endpoint override didn't apply — check that Profile B's `AZURE_OPENAI_ENDPOINT` line is uncommented and after the header value.

---

## Task 4: Update `.env.example` — three profiles with placeholders

**Files:**
- Modify: `backend/.env.example`

- [ ] **Step 1: Replace the Azure OpenAI section in `.env.example`**

The current `.env.example` has a single profile block. Replace the entire Azure OpenAI section with:

```env
# ─── Azure OpenAI ────────────────────────────────────────────────────────────
AZURE_OPENAI_API_KEY=<your-api-key>
AZURE_OPENAI_API_VERSION=2024-12-01-preview
AZURE_OPENAI_FALLBACK_DEPLOYMENT=

# ── Model profiles — comment active block, uncomment target, restart backend ──
#
# PROFILE A — gpt-5.4-nano  (ultra-fast, cheapest, ~3-4 min)
# AZURE_OPENAI_ENDPOINT=https://<your-resource>.services.ai.azure.com/
# AZURE_OPENAI_DEPLOYMENT_NAME=gpt-5.4-nano
# LLM_MAX_TOKENS_RESUME_PARSER=8000
# LLM_MAX_TOKENS_JD_PARSER=3000
# LLM_MAX_TOKENS_MATCH_SCORING=2000
# LLM_MAX_TOKENS_GAP_ANALYSIS=3000
# LLM_MAX_TOKENS_ATS_CHECK=1500
# LLM_MAX_TOKENS_RESUME_TAILORING=10000
# LLM_MAX_TOKENS_CLAIM_VERIFICATION=5000
# LLM_MAX_TOKENS_COVER_LETTER=1500
# LLM_MAX_TOKENS_INTERVIEW_PREP=6000
#
# PROFILE B — gpt-5.4-mini  (sweet spot, ~3-4 min, higher quality) ← DEFAULT
AZURE_OPENAI_ENDPOINT=https://<your-resource>.services.ai.azure.com/openai/v1
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-5.4-mini
LLM_MAX_TOKENS_RESUME_PARSER=8000
LLM_MAX_TOKENS_JD_PARSER=3000
LLM_MAX_TOKENS_MATCH_SCORING=2000
LLM_MAX_TOKENS_GAP_ANALYSIS=3000
LLM_MAX_TOKENS_ATS_CHECK=1500
LLM_MAX_TOKENS_RESUME_TAILORING=10000
LLM_MAX_TOKENS_CLAIM_VERIFICATION=5000
LLM_MAX_TOKENS_COVER_LETTER=1500
LLM_MAX_TOKENS_INTERVIEW_PREP=6000
#
# PROFILE C — gpt-5-mini  (reasoning, highest quality, ~8-10 min)
# AZURE_OPENAI_ENDPOINT=https://<your-resource>.services.ai.azure.com/
# AZURE_OPENAI_DEPLOYMENT_NAME=gpt-5-mini
# LLM_MAX_TOKENS_RESUME_PARSER=16000
# LLM_MAX_TOKENS_JD_PARSER=6000
# LLM_MAX_TOKENS_MATCH_SCORING=4000
# LLM_MAX_TOKENS_GAP_ANALYSIS=6000
# LLM_MAX_TOKENS_ATS_CHECK=3000
# LLM_MAX_TOKENS_RESUME_TAILORING=20000
# LLM_MAX_TOKENS_CLAIM_VERIFICATION=10000
# LLM_MAX_TOKENS_COVER_LETTER=3000
# LLM_MAX_TOKENS_INTERVIEW_PREP=12000
# ─────────────────────────────────────────────────────────────────────────────
```

- [ ] **Step 2: Commit `.env.example`**

```bash
git add backend/.env.example backend/docs/superpowers/plans/2026-07-31-dual-endpoint-llm-client.md
git commit -m "feat: three model profiles in .env.example (nano/mini/gpt-5-mini)"
```

---

## Task 5: End-to-end smoke test with Profile B

- [ ] **Step 1: Confirm startup log shows v1 client**

Start backend and check logs for:
```
LLMService: using OpenAI v1 client (endpoint=https://agentforgeai-resource.services.ai.azure.com/openai/v1)
```

- [ ] **Step 2: Run one full pipeline**

Upload a resume + JD and run Analyze & Tailor. Verify:
- Phase 1 completes without `JSONDecodeError`
- Score is non-zero
- Tailored resume summary starts with the target job title (not the candidate's current title)
- All downloads (DOCX, PDF, Cover Letter) are available

- [ ] **Step 3: Final commit + push**

```bash
git push origin main
```
