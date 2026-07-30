# Design Document: ResumeJDMatch AI

## Overview

ResumeJDMatch AI is a full-stack web application that analyzes alignment between a candidate's resume and a target job description, then produces optimized application materials. The system uses 10 modular AI agents orchestrated in a dependency-ordered pipeline to perform parsing, scoring, gap analysis, tailoring, verification, generation, and packaging.

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| 10 discrete AI agents vs. monolithic prompt | Isolation enables independent testing, retry logic, token budget control, and prompt versioning per task |
| Azure OpenAI Structured Outputs mode | Guarantees JSON schema conformance from LLM responses, eliminating post-hoc parsing failures |
| Two-pass scoring architecture | Quantifies improvement delta, giving candidates concrete before/after metrics |
| Claim Verification Agent as post-processor | Ensures zero-fabrication guarantee by cross-referencing every factual claim against source |
| Versioned prompt templates (prompts/v1/) | Enables A/B testing, rollback, and iterative prompt improvement without code changes |
| Semantic equivalence mapping as config | Allows domain experts to extend synonym/abbreviation mappings without engineering changes |
| OpenTelemetry per-agent spans | Granular observability enables cost tracking, latency debugging, and quality monitoring per agent |

### Research Findings

- **Azure OpenAI Structured Outputs**: Azure supports strict JSON schema enforcement via the `response_format` parameter with `type: "json_schema"`. This eliminates the need for retry-on-parse-failure for structured extraction tasks.
- **FastAPI Agent Architecture**: Production patterns favor a three-layer topology: stateless API gateway, async orchestration engine, and background task workers. Pydantic models serve as inter-agent contracts.
- **ATS-Safe DOCX Generation**: Single-column layout, standard fonts (Arial/Calibri/Times New Roman), 10-12pt size, no tables/images/text boxes, standard section headers. `python-docx` provides full control over these constraints.
- **OpenTelemetry for FastAPI**: The `opentelemetry-instrumentation-fastapi` package provides auto-instrumentation. Custom spans wrap each agent invocation with token usage attributes.

---

## Architecture

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND (React + TS + Tailwind)                │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐  ┌────────────────────────┐  │
│  │  Auth UI │  │Upload/   │  │  Dashboard   │  │  Download/Email Panel  │  │
│  │          │  │Paste UI  │  │  (Results)   │  │                        │  │
│  └────┬─────┘  └────┬─────┘  └──────┬───────┘  └───────────┬────────────┘  │
└───────┼──────────────┼───────────────┼──────────────────────┼───────────────┘
        │              │               │                      │
        ▼              ▼               ▼                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         API GATEWAY (FastAPI)                                │
│  ┌────────────┐  ┌───────────────┐  ┌──────────────┐  ┌──────────────────┐ │
│  │ Auth Routes│  │ Analysis Routes│  │ Result Routes│  │ Download Routes  │ │
│  └────────────┘  └───────┬───────┘  └──────────────┘  └──────────────────┘ │
└──────────────────────────┼──────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                     ORCHESTRATION LAYER                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  Pipeline Orchestrator (async, dependency-ordered, retry logic)      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│       │           │           │          │          │          │             │
│       ▼           ▼           ▼          ▼          ▼          ▼             │
│  ┌─────────┐ ┌─────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌─────────┐     │
│  │Resume   │ │JD       │ │Match   │ │Gap     │ │Resume  │ │Claim    │     │
│  │Parser   │ │Parser   │ │Scoring │ │Analysis│ │Tailor  │ │Verify   │     │
│  └─────────┘ └─────────┘ └────────┘ └────────┘ └────────┘ └─────────┘     │
│       │           │           │          │          │          │             │
│       ▼           ▼           ▼          ▼          ▼          ▼             │
│  ┌─────────┐ ┌─────────┐ ┌────────┐ ┌────────────────────────────────┐     │
│  │ATS Check│ │Cover    │ │Interview│ │Package Generation              │     │
│  │         │ │Letter   │ │Prep    │ │                                │     │
│  └─────────┘ └─────────┘ └────────┘ └────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────────────┘
        │                                                          │
        ▼                                                          ▼
┌───────────────────┐  ┌───────────────────┐  ┌───────────────────────────────┐
│  Azure OpenAI     │  │  PostgreSQL       │  │  Azure Blob Storage           │
│  (GPT-5 mini)     │  │  (Data Store)    │  │  (File Store)                 │
└───────────────────┘  └───────────────────┘  └───────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────────────────────────┐
│  OpenTelemetry Collector → Azure Monitor / Jaeger / Grafana                   │
└───────────────────────────────────────────────────────────────────────────────┘
```

### Agent Execution Flow (Dependency Order)

```
┌──────────────────────────────────────────────────────────────────┐
│                    PHASE 1: PARSING (parallel)                    │
│  Resume_Parser_Agent ──┐                                         │
│                        ├──► Parsed Resume + Parsed JD            │
│  JD_Parser_Agent ──────┘                                         │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│              PHASE 2: ANALYSIS (parallel after Phase 1)           │
│  Match_Scoring_Agent ──────► Pass 1 Score + Breakdown            │
│  Gap_Analysis_Agent ───────► Gap Report                          │
│  ATS_Check_Agent ──────────► ATS Risk Report                     │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                    PHASE 3: TAILORING (sequential)                │
│  Resume_Tailoring_Agent ───► Tailored Resume                     │
│  Claim_Verification_Agent ─► Verified Tailored Resume            │
│  Match_Scoring_Agent ──────► Pass 2 Score (re-score)             │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│              PHASE 4: GENERATION (parallel)                       │
│  Cover_Letter_Agent ────────► Cover Letter                       │
│  Interview_Prep_Agent ──────► Interview Guide                    │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                    PHASE 5: PACKAGING                             │
│  Package_Generation_Agent ──► DOCX + PDF files                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## Components and Interfaces

### Backend Folder Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app factory, lifespan events
│   ├── config.py                  # Pydantic Settings (env vars)
│   ├── dependencies.py            # Dependency injection providers
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── auth.py                # POST /auth/register, /auth/login, /auth/refresh
│   │   ├── resumes.py             # POST/GET /resumes, /resumes/{id}/versions
│   │   ├── jobs.py                # POST /jobs (JD input)
│   │   ├── analysis.py            # POST /analysis/run, GET /analysis/{run_id}
│   │   ├── downloads.py           # GET /downloads/{run_id}/{artifact_type}
│   │   └── health.py              # GET /health, /health/agents
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base.py                # BaseAgent abstract class
│   │   ├── resume_parser.py
│   │   ├── jd_parser.py
│   │   ├── match_scoring.py
│   │   ├── gap_analysis.py
│   │   ├── resume_tailoring.py
│   │   ├── cover_letter.py
│   │   ├── interview_prep.py
│   │   ├── ats_check.py
│   │   ├── claim_verification.py
│   │   └── package_generation.py
│   │
│   ├── orchestrator/
│   │   ├── __init__.py
│   │   ├── pipeline.py            # Pipeline definition and execution
│   │   ├── retry.py               # Exponential backoff retry logic
│   │   └── circuit_breaker.py     # Model fallback circuit breaker
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── db.py                  # SQLAlchemy ORM models
│   │   └── schemas.py             # Pydantic request/response schemas
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── resume_parsed.py       # ParsedResume JSON schema
│   │   ├── jd_parsed.py           # ParsedJD JSON schema
│   │   ├── score_output.py        # ScoreOutput JSON schema
│   │   ├── gap_report.py          # GapReport JSON schema
│   │   ├── tailored_resume.py     # TailoredResume JSON schema
│   │   ├── cover_letter.py        # CoverLetter JSON schema
│   │   ├── interview_guide.py     # InterviewGuide JSON schema
│   │   ├── ats_report.py          # ATSReport JSON schema
│   │   └── verification_report.py # VerificationReport JSON schema
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py        # Authentication logic
│   │   ├── storage_service.py     # Azure Blob Storage operations
│   │   ├── llm_service.py         # Azure OpenAI client wrapper
│   │   ├── document_service.py    # DOCX/PDF generation
│   │   └── email_service.py       # Email delivery
│   │
│   ├── security/
│   │   ├── __init__.py
│   │   ├── sanitizer.py           # Prompt injection sanitization
│   │   ├── pii_redactor.py        # PII redaction for logs
│   │   └── rate_limiter.py        # Per-user rate limiting
│   │
│   ├── observability/
│   │   ├── __init__.py
│   │   ├── tracing.py             # OTel tracer setup and span helpers
│   │   ├── metrics.py             # OTel metrics (counters, histograms)
│   │   └── logging.py             # Structured logging with PII redaction
│   │
│   ├── semantic/
│   │   ├── __init__.py
│   │   ├── synonym_map.py         # Skill synonym/abbreviation mappings
│   │   └── matcher.py             # Semantic matching logic
│   │
│   └── prompts/
│       └── v1/
│           ├── resume_parser.yaml
│           ├── jd_parser.yaml
│           ├── match_scoring.yaml
│           ├── gap_analysis.yaml
│           ├── resume_tailoring.yaml
│           ├── cover_letter.yaml
│           ├── interview_prep.yaml
│           ├── ats_check.yaml
│           └── claim_verification.yaml
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── property/
│
├── alembic/                       # Database migrations
├── Dockerfile
├── requirements.txt
└── pyproject.toml
```

### Frontend Folder Structure

```
frontend/
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── vite-env.d.ts
│   │
│   ├── api/
│   │   ├── client.ts              # Axios/fetch wrapper with auth interceptor
│   │   ├── auth.ts                # Auth API calls
│   │   ├── analysis.ts            # Analysis API calls
│   │   ├── resumes.ts             # Resume CRUD API calls
│   │   └── downloads.ts           # Download API calls
│   │
│   ├── components/
│   │   ├── auth/
│   │   │   ├── LoginForm.tsx
│   │   │   ├── RegisterForm.tsx
│   │   │   └── OAuthButton.tsx
│   │   ├── upload/
│   │   │   ├── ResumeUpload.tsx
│   │   │   ├── JDInput.tsx
│   │   │   └── VersionSelector.tsx
│   │   ├── dashboard/
│   │   │   ├── ScoreCard.tsx
│   │   │   ├── CategoryBreakdown.tsx
│   │   │   ├── KeywordPanel.tsx
│   │   │   ├── TailoredResumePreview.tsx
│   │   │   ├── CoverLetterPanel.tsx
│   │   │   ├── InterviewGuidePanel.tsx
│   │   │   └── DownloadActions.tsx
│   │   └── common/
│   │       ├── Gauge.tsx
│   │       ├── CollapsiblePanel.tsx
│   │       ├── LoadingState.tsx
│   │       └── ErrorBoundary.tsx
│   │
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   ├── useAnalysis.ts
│   │   └── usePolling.ts
│   │
│   ├── store/
│   │   ├── authStore.ts           # Zustand auth state
│   │   └── analysisStore.ts       # Zustand analysis state
│   │
│   ├── types/
│   │   ├── api.ts                 # API response types
│   │   ├── resume.ts              # Resume/JD types
│   │   └── analysis.ts            # Analysis result types
│   │
│   ├── utils/
│   │   ├── validation.ts
│   │   └── formatting.ts
│   │
│   └── styles/
│       └── globals.css            # Tailwind base + custom styles
│
├── public/
├── index.html
├── tailwind.config.ts
├── tsconfig.json
├── vite.config.ts
└── package.json
```

---

## AI Agent Design

### Base Agent Contract

```python
from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import TypeVar, Generic

TInput = TypeVar("TInput", bound=BaseModel)
TOutput = TypeVar("TOutput", bound=BaseModel)

class BaseAgent(ABC, Generic[TInput, TOutput]):
    """Base class for all AI agents."""

    agent_name: str
    max_output_tokens: int
    temperature: float = 0.2
    prompt_version: str = "v1"

    @abstractmethod
    async def execute(self, input_data: TInput) -> TOutput:
        """Execute the agent's primary task."""
        ...

    async def validate_output(self, output: TOutput) -> bool:
        """Validate output against the agent's JSON schema."""
        ...

    async def health_check(self) -> bool:
        """Return True if agent is operational."""
        ...
```

### Agent 1: Resume_Parser_Agent

| Attribute | Value |
|-----------|-------|
| **Purpose** | Extract structured data from resume text/document content |
| **Input** | `ResumeParserInput(raw_text: str, file_format: str)` |
| **Output** | `ParsedResume` (see Data Models) |
| **Token Budget** | ≤ 4000 output tokens |
| **Temperature** | 0.1 |
| **Validation** | Output must conform to `ParsedResume` JSON schema; null fields allowed; original text sections preserved |
| **Failure Handling** | Retry 2x with exponential backoff; on final failure return partial result with confidence flags |

### Agent 2: JD_Parser_Agent

| Attribute | Value |
|-----------|-------|
| **Purpose** | Extract structured requirements from job description text |
| **Input** | `JDParserInput(raw_text: str)` |
| **Output** | `ParsedJD` (see Data Models) |
| **Token Budget** | ≤ 3000 output tokens |
| **Temperature** | 0.1 |
| **Validation** | Output must conform to `ParsedJD` JSON schema; skills categorized as must-have/nice-to-have |
| **Failure Handling** | Retry 2x; on failure inform user JD could not be parsed |

### Agent 3: Match_Scoring_Agent

| Attribute | Value |
|-----------|-------|
| **Purpose** | Compute ATS-style alignment score between parsed resume and parsed JD |
| **Input** | `ScoringInput(parsed_resume: ParsedResume, parsed_jd: ParsedJD, semantic_map: dict)` |
| **Output** | `ScoreOutput` (see Data Models) |
| **Token Budget** | ≤ 2000 output tokens |
| **Temperature** | 0.2 (with fixed seed) |
| **Validation** | Overall score = weighted sum ±1; all scores in [0, 100]; no protected attribute inference |
| **Failure Handling** | Retry 2x; on failure return error with available partial scores |

### Agent 4: Gap_Analysis_Agent

| Attribute | Value |
|-----------|-------|
| **Purpose** | Identify skills, certifications, and experience gaps between resume and JD |
| **Input** | `GapInput(parsed_resume: ParsedResume, parsed_jd: ParsedJD, score_output: ScoreOutput)` |
| **Output** | `GapReport` (see Data Models) |
| **Token Budget** | ≤ 3000 output tokens |
| **Temperature** | 0.3 |
| **Validation** | Every gap references a specific JD requirement; gaps categorized as critical/recommended |
| **Failure Handling** | Retry 2x; on failure provide scoring breakdown as fallback gap indicator |

### Agent 5: Resume_Tailoring_Agent

| Attribute | Value |
|-----------|-------|
| **Purpose** | Rewrite resume content for JD alignment while preserving all factual claims |
| **Input** | `TailoringInput(parsed_resume: ParsedResume, parsed_jd: ParsedJD, gap_report: GapReport, source_text: str)` |
| **Output** | `TailoredResume` (see Data Models) |
| **Token Budget** | ≤ 6000 output tokens |
| **Temperature** | 0.4 |
| **Validation** | All employer names, titles, dates, degrees, certifications traceable to source; no new factual claims |
| **Failure Handling** | Retry 2x; on failure return original resume with keyword suggestions as annotations |

### Agent 6: Claim_Verification_Agent

| Attribute | Value |
|-----------|-------|
| **Purpose** | Verify every factual claim in tailored output against source resume |
| **Input** | `VerificationInput(tailored_resume: TailoredResume, source_resume: ParsedResume, source_text: str)` |
| **Output** | `VerificationReport` with verified resume (unverified claims removed) |
| **Token Budget** | ≤ 2000 output tokens |
| **Temperature** | 0.1 |
| **Validation** | Zero unverified claims in final output; every claim has citation to source section |
| **Failure Handling** | Retry 2x; on failure flag entire tailored resume as unverified and use original |

### Agent 7: Cover_Letter_Agent

| Attribute | Value |
|-----------|-------|
| **Purpose** | Generate personalized cover letter from resume and JD |
| **Input** | `CoverLetterInput(parsed_resume: ParsedResume, parsed_jd: ParsedJD, tailored_resume: TailoredResume)` |
| **Output** | `CoverLetter` (see Data Models) |
| **Token Budget** | ≤ 1500 output tokens |
| **Temperature** | 0.6 |
| **Validation** | Word count 250-350; contains company name and role title; all claims grounded in source resume |
| **Failure Handling** | Retry 2x; on failure inform user cover letter could not be generated |

### Agent 8: Interview_Prep_Agent

| Attribute | Value |
|-----------|-------|
| **Purpose** | Generate interview questions with STAR-format answer skeletons |
| **Input** | `InterviewPrepInput(parsed_resume: ParsedResume, parsed_jd: ParsedJD, gap_report: GapReport)` |
| **Output** | `InterviewGuide` (see Data Models) |
| **Token Budget** | ≤ 4000 output tokens |
| **Temperature** | 0.5 |
| **Validation** | 8-10 behavioral + 3-4 technical = 11-14 total; no fabricated examples; gap-related questions included |
| **Failure Handling** | Retry 2x; on failure provide generic questions based on JD requirements |

### Agent 9: ATS_Check_Agent

| Attribute | Value |
|-----------|-------|
| **Purpose** | Scan resume for ATS compatibility issues |
| **Input** | `ATSCheckInput(raw_text: str, file_format: str, has_tables: bool, has_images: bool, has_columns: bool)` |
| **Output** | `ATSReport` (see Data Models) |
| **Token Budget** | ≤ 1500 output tokens |
| **Temperature** | 0.1 |
| **Validation** | Each risk has severity (critical/warning/info) and remediation; zero critical = ATS-safe flag |
| **Failure Handling** | Retry 2x; on failure mark ATS status as "unable to determine" |

### Agent 10: Package_Generation_Agent

| Attribute | Value |
|-----------|-------|
| **Purpose** | Assemble final deliverables into downloadable DOCX/PDF documents |
| **Input** | `PackageInput(tailored_resume: TailoredResume, cover_letter: CoverLetter, interview_guide: InterviewGuide)` |
| **Output** | `GeneratedPackage(resume_docx: bytes, resume_pdf: bytes, cover_letter_docx: bytes, interview_pdf: bytes, zip_bundle: bytes)` |
| **Token Budget** | N/A (no LLM call — document generation only) |
| **Temperature** | N/A |
| **Validation** | Valid DOCX/PDF files; ATS-safe formatting (single column, standard fonts, no tables) |
| **Failure Handling** | Retry 2x; on failure provide plain text versions as fallback |

---

## Data Models

### Database Schema (PostgreSQL)

```sql
-- Users
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),          -- NULL for OAuth-only users
    oauth_provider VARCHAR(50),          -- 'google', 'microsoft', NULL
    oauth_provider_id VARCHAR(255),
    email_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Resumes
CREATE TABLE resumes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    original_filename VARCHAR(255),
    file_format VARCHAR(10) NOT NULL,    -- 'pdf', 'docx', 'text'
    blob_storage_path VARCHAR(500),      -- Azure Blob path (NULL for text input)
    raw_text TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Resume Versions (max 3 per user: fresher, experienced, domain-specific)
CREATE TABLE resume_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    resume_id UUID NOT NULL REFERENCES resumes(id) ON DELETE CASCADE,
    label VARCHAR(50) NOT NULL,          -- 'fresher', 'experienced', 'domain_specific'
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, label)               -- One version per label per user
);

-- Job Descriptions
CREATE TABLE job_descriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    source_type VARCHAR(10) NOT NULL,    -- 'text', 'url'
    source_url VARCHAR(2000),
    raw_text TEXT NOT NULL,
    parsed_data JSONB,                   -- ParsedJD JSON
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Match Results (one per analysis run)
CREATE TABLE match_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    resume_id UUID NOT NULL REFERENCES resumes(id),
    jd_id UUID NOT NULL REFERENCES job_descriptions(id),
    run_id UUID NOT NULL UNIQUE,         -- Correlation ID for the full pipeline
    status VARCHAR(20) NOT NULL DEFAULT 'pending',  -- pending, running, completed, failed, partial
    pass1_score JSONB,                   -- ScoreOutput JSON
    pass2_score JSONB,                   -- ScoreOutput JSON
    gap_report JSONB,                    -- GapReport JSON
    ats_report JSONB,                    -- ATSReport JSON
    parsed_resume JSONB,                 -- ParsedResume JSON
    parsed_jd JSONB,                     -- ParsedJD JSON (denormalized for result access)
    tailored_resume JSONB,               -- TailoredResume JSON
    verification_report JSONB,           -- VerificationReport JSON
    cover_letter JSONB,                  -- CoverLetter JSON
    interview_guide JSONB,              -- InterviewGuide JSON
    total_tokens_used INTEGER DEFAULT 0,
    total_cost_usd NUMERIC(6,4) DEFAULT 0.0,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Generated Artifacts (downloadable files)
CREATE TABLE generated_artifacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    match_result_id UUID NOT NULL REFERENCES match_results(id) ON DELETE CASCADE,
    artifact_type VARCHAR(50) NOT NULL,  -- 'resume_docx', 'resume_pdf', 'cover_letter_docx', 'interview_pdf', 'zip_bundle'
    blob_storage_path VARCHAR(500) NOT NULL,
    file_size_bytes INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Audit Log
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    run_id UUID,
    agent_name VARCHAR(50),
    action VARCHAR(100) NOT NULL,
    details JSONB,                       -- PII-redacted context
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_resumes_user_id ON resumes(user_id);
CREATE INDEX idx_resume_versions_user_id ON resume_versions(user_id);
CREATE INDEX idx_job_descriptions_user_id ON job_descriptions(user_id);
CREATE INDEX idx_match_results_user_id ON match_results(user_id);
CREATE INDEX idx_match_results_run_id ON match_results(run_id);
CREATE INDEX idx_generated_artifacts_match_result ON generated_artifacts(match_result_id);
CREATE INDEX idx_audit_log_user_run ON audit_log(user_id, run_id);
```


### Structured JSON Schemas (Pydantic Models)

#### ParsedResume Schema

```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date

class Skill(BaseModel):
    name: str
    category: str  # "hard_skill", "soft_skill"
    confidence: float = Field(ge=0.0, le=1.0)
    source_text: str  # Original text where skill was found
    is_contextual: bool = False  # True if inferred from context

class Experience(BaseModel):
    job_title: str
    job_title_normalized: Optional[str] = None
    employer: str
    start_date: Optional[str] = None  # ISO format or "Present"
    end_date: Optional[str] = None
    description: str
    achievements: list[str]
    quantifiable_metrics: list[str]
    experience_type: str  # "full_time", "freelance", "volunteer", "open_source", "side_project"
    original_text: str

class Education(BaseModel):
    degree: str
    institution: str
    graduation_date: Optional[str] = None
    field_of_study: Optional[str] = None
    original_text: str

class Certification(BaseModel):
    name: str
    name_normalized: Optional[str] = None
    issuing_org: Optional[str] = None
    date_obtained: Optional[str] = None
    original_text: str

class ParsedResume(BaseModel):
    candidate_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    location: Optional[str] = None
    skills: list[Skill]
    experience: list[Experience]
    education: list[Education]
    certifications: list[Certification]
    projects: list[dict]  # {name, description, technologies, url}
    total_years_experience: Optional[float] = None
    domain_keywords: list[str]
    tools_and_platforms: list[str]
    original_sections: dict[str, str]  # section_name -> original text
    parse_confidence: float = Field(ge=0.0, le=1.0)
```

#### ParsedJD Schema

```python
class JDSkill(BaseModel):
    name: str
    category: str  # "hard_skill", "soft_skill"
    priority: str  # "must_have", "nice_to_have"
    signal_text: str  # The JD text that indicates priority

class ParsedJD(BaseModel):
    company_name: Optional[str] = None
    role_title: str
    role_title_normalized: Optional[str] = None
    seniority_level: Optional[str] = None  # "junior", "mid", "senior", "lead", "principal"
    seniority_indicators: list[str]  # Context clues for seniority
    must_have_skills: list[JDSkill]
    nice_to_have_skills: list[JDSkill]
    responsibilities: list[str]
    required_certifications: list[str]
    domain_requirements: list[str]
    ats_keywords: list[str]  # Key phrases for ATS matching
    experience_years_required: Optional[str] = None
    original_text: str
    parse_confidence: float = Field(ge=0.0, le=1.0)
```

#### ScoreOutput Schema

```python
class CategoryScore(BaseModel):
    category: str  # "hard_skill_overlap", "title_seniority_alignment", "keyword_phrase_match", "achievement_relevance"
    score: int = Field(ge=0, le=100)
    weight: float  # 0.40, 0.20, 0.25, 0.15
    reasoning: str
    matched_items: list[str]
    missing_items: list[str]

class ScoreOutput(BaseModel):
    overall_score: int = Field(ge=0, le=100)
    category_scores: list[CategoryScore]  # Exactly 4 categories
    matched_keywords: list[str]
    missing_keywords: list[str]
    skills_gap: list[str]
    certification_gap: list[str]
    achievement_gap: list[str]
    semantic_matches: list[dict]  # {resume_term, jd_term, match_type}
    scoring_seed: int  # Fixed seed for reproducibility
    model_version: str
```

#### GapReport Schema

```python
class GapItem(BaseModel):
    gap_type: str  # "hard_skill", "soft_skill", "certification", "domain_keyword", "experience_level", "achievement"
    description: str
    severity: str  # "critical", "recommended"
    jd_requirement_ref: str  # Specific JD requirement text
    suggestion: str  # Actionable remediation
    is_transferable: bool  # True if transferable skills partially address this

class GapReport(BaseModel):
    gaps: list[GapItem]
    critical_count: int
    recommended_count: int
    coverage_percentage: float  # % of JD must-haves met
    summary: str
```

#### TailoredResume Schema

```python
class TailoredSection(BaseModel):
    section_name: str
    content: str
    changes_made: list[str]  # Description of each change
    keywords_added: list[str]  # JD keywords inserted
    source_citations: list[dict]  # {claim, source_section, source_text}

class TailoredResume(BaseModel):
    sections: list[TailoredSection]
    full_text: str
    keywords_added: list[str]
    keywords_matched: list[str]
    factual_claims: list[dict]  # {claim_text, claim_type, source_reference}
    format_type: str  # Always "ats_safe"
```

#### CoverLetter Schema

```python
class CoverLetter(BaseModel):
    content: str
    word_count: int = Field(ge=250, le=350)
    company_name: str
    role_title: str
    jd_requirements_referenced: list[str]  # 1-2 JD requirements cited
    resume_evidence: list[dict]  # {claim, source_section}
    grounding_citations: list[dict]  # Internal: {claim, resume_section, resume_text}
    region_convention: Optional[str] = None  # "us", "uk", "apac"
```

#### InterviewGuide Schema

```python
class InterviewQuestion(BaseModel):
    question: str
    category: str  # "behavioral", "technical", "domain"
    source: str  # "jd_requirement", "gap_analysis", "achievement"
    star_skeleton: Optional[dict] = None  # {situation, task, action, result}
    resume_evidence: Optional[str] = None
    is_gap_question: bool = False  # True if targeting a resume gap
    note: Optional[str] = None  # e.g., "candidate should provide own example"

class InterviewGuide(BaseModel):
    behavioral_questions: list[InterviewQuestion]  # 8-10
    technical_questions: list[InterviewQuestion]  # 3-4
    total_count: int = Field(ge=11, le=14)
    preparation_tips: list[str]
```

---

## API Route Design (FastAPI Endpoints)

### Authentication

```python
# POST /api/v1/auth/register
# Body: {email: str, password: str}
# Response: {user_id: str, message: str}  (201)

# POST /api/v1/auth/login
# Body: {email: str, password: str}
# Response: {access_token: str, refresh_token: str, expires_in: int}  (200)

# POST /api/v1/auth/oauth/{provider}
# Body: {code: str, redirect_uri: str}
# Response: {access_token: str, refresh_token: str}  (200)

# POST /api/v1/auth/refresh
# Body: {refresh_token: str}
# Response: {access_token: str, expires_in: int}  (200)

# POST /api/v1/auth/password-reset/request
# Body: {email: str}
# Response: {message: str}  (200, always same response)

# POST /api/v1/auth/password-reset/confirm
# Body: {token: str, new_password: str}
# Response: {message: str}  (200)

# POST /api/v1/auth/verify-email
# Body: {token: str}
# Response: {message: str}  (200)
```

### Resumes

```python
# POST /api/v1/resumes/upload
# Body: multipart/form-data {file: UploadFile}
# Response: {resume_id: str, raw_text_preview: str}  (201)

# POST /api/v1/resumes/text
# Body: {text: str}
# Response: {resume_id: str}  (201)

# GET /api/v1/resumes
# Response: [{resume_id, filename, format, created_at}]  (200)

# POST /api/v1/resumes/{resume_id}/versions
# Body: {label: "fresher" | "experienced" | "domain_specific"}
# Response: {version_id: str}  (201)

# GET /api/v1/resumes/versions
# Response: [{version_id, label, resume_id, created_at}]  (200)

# GET /api/v1/resumes/{resume_id}
# Response: {resume_id, raw_text, filename, format, created_at}  (200)
```

### Job Descriptions

```python
# POST /api/v1/jobs/text
# Body: {text: str}
# Response: {jd_id: str}  (201)

# POST /api/v1/jobs/url
# Body: {url: str}
# Response: {jd_id: str, extracted_text_preview: str}  (201)

# GET /api/v1/jobs/{jd_id}
# Response: {jd_id, raw_text, source_type, source_url, created_at}  (200)
```

### Analysis

```python
# POST /api/v1/analysis/run
# Body: {resume_id: str, jd_id: str}
# Response: {run_id: str, status: "pending"}  (202)

# GET /api/v1/analysis/{run_id}
# Response: MatchResult full object with status  (200)

# GET /api/v1/analysis/{run_id}/status
# Response: {status: str, current_phase: str, progress_pct: int}  (200)

# GET /api/v1/analysis/history
# Response: [{run_id, resume_id, jd_id, status, pass1_score, pass2_score, created_at}]  (200)
```

### Downloads

```python
# GET /api/v1/downloads/{run_id}/resume-docx
# Response: application/vnd.openxmlformats-officedocument.wordprocessingml.document

# GET /api/v1/downloads/{run_id}/resume-pdf
# Response: application/pdf

# GET /api/v1/downloads/{run_id}/cover-letter-docx
# Response: application/vnd.openxmlformats-officedocument.wordprocessingml.document

# GET /api/v1/downloads/{run_id}/interview-pdf
# Response: application/pdf

# GET /api/v1/downloads/{run_id}/all
# Response: application/zip

# POST /api/v1/downloads/{run_id}/email
# Response: {message: "Package sent to registered email"}  (200)
```

### Health

```python
# GET /api/v1/health
# Response: {status: "healthy", version: str, timestamp: str}  (200)

# GET /api/v1/health/agents
# Response: {agents: [{name, status, last_check}]}  (200)
```

---

## Core Scoring Algorithm

### Pseudocode

```python
def compute_match_score(parsed_resume: ParsedResume, parsed_jd: ParsedJD, semantic_map: dict) -> ScoreOutput:
    """
    Compute ATS-style alignment score.
    
    Weights:
      - Hard skill overlap: 40%
      - Title/seniority alignment: 20%
      - Keyword/phrase match: 25%
      - Quantifiable achievement relevance: 15%
    
    Bias constraints:
      - NEVER penalize employment gaps
      - NEVER penalize job-change frequency
      - NEVER use protected attributes
      - TREAT freelance/volunteer/open-source as equivalent to full-time
    """
    
    # 1. Hard Skill Overlap (40%)
    resume_skills = normalize_skills(parsed_resume.skills, semantic_map)
    jd_must_have = normalize_skills(parsed_jd.must_have_skills, semantic_map)
    jd_nice_to_have = normalize_skills(parsed_jd.nice_to_have_skills, semantic_map)
    
    must_have_matches = semantic_intersection(resume_skills, jd_must_have, semantic_map)
    nice_to_have_matches = semantic_intersection(resume_skills, jd_nice_to_have, semantic_map)
    
    # Must-haves count 80% of the hard skill score, nice-to-haves 20%
    must_have_ratio = len(must_have_matches) / max(len(jd_must_have), 1)
    nice_to_have_ratio = len(nice_to_have_matches) / max(len(jd_nice_to_have), 1)
    hard_skill_score = clamp(round((must_have_ratio * 0.8 + nice_to_have_ratio * 0.2) * 100), 0, 100)
    
    # 2. Title/Seniority Alignment (20%)
    title_similarity = semantic_title_match(
        parsed_resume.experience[0].job_title_normalized if parsed_resume.experience else None,
        parsed_jd.role_title_normalized,
        semantic_map
    )
    seniority_match = compute_seniority_alignment(
        infer_seniority(parsed_resume),
        parsed_jd.seniority_level
    )
    title_score = clamp(round((title_similarity * 0.6 + seniority_match * 0.4) * 100), 0, 100)
    
    # 3. Keyword/Phrase Match (25%)
    resume_text_normalized = normalize_text(parsed_resume)
    jd_keywords = parsed_jd.ats_keywords
    
    matched_keywords = []
    for keyword in jd_keywords:
        if semantic_contains(resume_text_normalized, keyword, semantic_map):
            matched_keywords.append(keyword)
    
    keyword_score = clamp(round(len(matched_keywords) / max(len(jd_keywords), 1) * 100), 0, 100)
    
    # 4. Achievement Relevance (15%)
    resume_achievements = extract_all_achievements(parsed_resume)  # Includes freelance, volunteer, OSS
    relevant_achievements = score_achievement_relevance(resume_achievements, parsed_jd)
    achievement_score = clamp(round(relevant_achievements * 100), 0, 100)
    
    # 5. Weighted Overall Score
    overall = round(
        hard_skill_score * 0.40 +
        title_score * 0.20 +
        keyword_score * 0.25 +
        achievement_score * 0.15
    )
    overall = clamp(overall, 0, 100)
    
    return ScoreOutput(
        overall_score=overall,
        category_scores=[...],
        matched_keywords=matched_keywords,
        missing_keywords=[k for k in jd_keywords if k not in matched_keywords],
        ...
    )


def semantic_intersection(set_a: list, set_b: list, semantic_map: dict) -> list:
    """Find matches using exact match + synonym mapping + contextual equivalence."""
    matches = []
    for item_b in set_b:
        for item_a in set_a:
            if exact_match(item_a, item_b) or synonym_match(item_a, item_b, semantic_map):
                matches.append((item_a, item_b))
                break
    return matches


def clamp(value: int, min_val: int, max_val: int) -> int:
    return max(min_val, min(max_val, value))
```

---

## Versioned LLM Prompt Template Design

### Prompt Directory Structure

```
backend/app/prompts/
├── v1/
│   ├── resume_parser.yaml
│   ├── jd_parser.yaml
│   ├── match_scoring.yaml
│   ├── gap_analysis.yaml
│   ├── resume_tailoring.yaml
│   ├── cover_letter.yaml
│   ├── interview_prep.yaml
│   ├── ats_check.yaml
│   └── claim_verification.yaml
├── v2/                            # Future version for A/B testing
│   └── ...
└── config.yaml                    # Active version mapping
```

### Prompt Template Format

```yaml
# prompts/v1/resume_parser.yaml
metadata:
  agent: resume_parser
  version: "1.0.0"
  description: "Extract structured resume data from raw text"
  max_output_tokens: 4000
  temperature: 0.1
  response_format: "json_schema"

system_prompt: |
  You are a precise resume parser. Extract structured data from the provided resume text.
  
  RULES:
  - Extract ALL fields specified in the output schema
  - If a field cannot be confidently determined, set it to null
  - Preserve original text for each section
  - Normalize job titles to canonical forms BUT preserve the original title
  - Extract soft skills from contextual descriptions (e.g., "led a team" → leadership)
  - Include volunteer, freelance, open-source, and side project experience
  - Return confidence scores for each extracted field
  - ONLY process English-language resumes
  
  NEVER:
  - Guess or fabricate information not present in the text
  - Infer personal demographics or protected attributes
  - Skip any section of the resume

user_prompt_template: |
  Parse the following resume text into structured JSON:
  
  ---
  {resume_text}
  ---
  
  Return the result conforming to the ParsedResume schema.

json_schema:
  $ref: "../schemas/resume_parsed.json"
```

### Prompt Config (Active Version Mapping)

```yaml
# prompts/config.yaml
active_versions:
  resume_parser: "v1"
  jd_parser: "v1"
  match_scoring: "v1"
  gap_analysis: "v1"
  resume_tailoring: "v1"
  cover_letter: "v1"
  interview_prep: "v1"
  ats_check: "v1"
  claim_verification: "v1"
```

---

## Semantic Keyword Intelligence Design

### Architecture

```python
# backend/app/semantic/synonym_map.py

class SemanticMap:
    """
    Configurable semantic equivalence mapping.
    Loaded from YAML config; extensible without code changes.
    """
    
    def __init__(self, config_path: str = "config/semantic_mappings.yaml"):
        self.mappings: dict[str, set[str]] = load_mappings(config_path)
    
    def are_equivalent(self, term_a: str, term_b: str) -> bool:
        """Check if two terms are semantically equivalent."""
        a_normalized = term_a.lower().strip()
        b_normalized = term_b.lower().strip()
        
        if a_normalized == b_normalized:
            return True
        
        # Check canonical group membership
        group_a = self.get_canonical_group(a_normalized)
        group_b = self.get_canonical_group(b_normalized)
        
        return group_a is not None and group_a == group_b
    
    def get_canonical_group(self, term: str) -> Optional[str]:
        """Get the canonical group ID for a term."""
        for group_id, synonyms in self.mappings.items():
            if term in synonyms:
                return group_id
        return None
    
    def expand_term(self, term: str) -> set[str]:
        """Get all equivalent terms for a given term."""
        group = self.get_canonical_group(term.lower().strip())
        if group:
            return self.mappings[group]
        return {term}
```

### Semantic Mappings Config

```yaml
# config/semantic_mappings.yaml
skill_synonyms:
  machine_learning:
    - "machine learning"
    - "ml"
    - "statistical learning"
    - "predictive modeling"
  
  amazon_web_services:
    - "amazon web services"
    - "aws"
    - "amazon cloud"
  
  kubernetes:
    - "kubernetes"
    - "k8s"
    - "container orchestration"
  
  continuous_integration:
    - "ci/cd"
    - "continuous integration"
    - "continuous deployment"
    - "continuous delivery"
    - "cicd"

  project_management_professional:
    - "pmp"
    - "project management professional"
  
  aws_solutions_architect:
    - "aws saa"
    - "aws solutions architect associate"
    - "aws certified solutions architect"

title_synonyms:
  software_engineer:
    - "software engineer"
    - "software developer"
    - "sde"
    - "programmer"
    - "software development engineer"
    - "application developer"
  
  data_scientist:
    - "data scientist"
    - "ml engineer"
    - "machine learning engineer"
    - "applied scientist"

contextual_equivalences:
  remote_team_leadership:
    patterns:
      - "managed a distributed team"
      - "led remote team"
      - "managed offshore team"
    implies: "remote team leadership"
```

---

## OpenTelemetry Instrumentation Plan

### Setup

```python
# backend/app/observability/tracing.py
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

def setup_tracing(app, db_engine):
    provider = TracerProvider()
    exporter = OTLPSpanExporter(endpoint=os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"])
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    
    FastAPIInstrumentor.instrument_app(app)
    HTTPXClientInstrumentor().instrument()
    SQLAlchemyInstrumentor().instrument(engine=db_engine)
```

### Span Naming Convention

| Operation | Span Name |
|-----------|-----------|
| Resume parsing | `resume_parser.extract` |
| JD parsing | `jd_parser.extract` |
| Match scoring (Pass 1) | `match_scoring.compute_pass1` |
| Match scoring (Pass 2) | `match_scoring.compute_pass2` |
| Gap analysis | `gap_analysis.identify` |
| Resume tailoring | `resume_tailoring.tailor` |
| Claim verification | `claim_verification.verify` |
| Cover letter gen | `cover_letter.generate` |
| Interview prep gen | `interview_prep.generate` |
| ATS check | `ats_check.scan` |
| Package generation | `package_generation.assemble` |
| Full pipeline | `orchestrator.run_pipeline` |

### Span Attributes

```python
# Attached to every agent span
span_attributes = {
    "user_id": hash(user_id),          # Hashed, never raw
    "run_id": run_id,
    "agent_name": agent.agent_name,
    "input_token_count": input_tokens,
    "output_token_count": output_tokens,
    "model_name": model_name,
    "duration_ms": duration_ms,
    "prompt_version": agent.prompt_version,
    "cost_usd": computed_cost,
    "retry_count": retry_count,
}
```

### Metrics

| Metric | Type | Labels |
|--------|------|--------|
| `analysis.request_count` | Counter | status, endpoint |
| `analysis.request_latency_ms` | Histogram | endpoint, quantile |
| `agent.token_usage` | Counter | agent_name, direction (input/output) |
| `agent.error_count` | Counter | agent_name, error_type |
| `agent.cost_usd` | Counter | agent_name |
| `auth.active_sessions` | Gauge | — |
| `analysis.queue_depth` | Gauge | — |

---

## Security Architecture

### Authentication Flow

```
┌────────┐    credentials    ┌──────────┐    verify     ┌────────────┐
│ Client │ ──────────────► │ Auth API │ ──────────► │ User DB    │
│        │ ◄────────────── │          │ ◄────────── │            │
│        │    JWT tokens     │          │   user row   │            │
└────────┘                   └──────────┘              └────────────┘
     │
     │  Bearer token in Authorization header
     ▼
┌──────────────────────────────────────────────────┐
│ JWT Middleware (validates on every request)        │
│ - Verify signature (RS256)                        │
│ - Check expiration                                │
│ - Extract user_id claim                           │
└──────────────────────────────────────────────────┘
```

### Security Layers

| Layer | Mechanism |
|-------|-----------|
| **Transport** | TLS 1.2+ enforced on all endpoints |
| **Authentication** | JWT (RS256) with short-lived access tokens (15min) + refresh tokens (7d) |
| **Authorization** | User can only access own data (user_id from JWT matched against resource owner) |
| **Input Validation** | Pydantic models validate all inputs; file size/type checks before processing |
| **Prompt Injection Defense** | `sanitizer.py` strips known injection patterns before LLM input |
| **Output Validation** | All LLM outputs validated against JSON schemas; malformed outputs rejected |
| **Rate Limiting** | 10 analyses/user/hour via Redis-backed sliding window |
| **PII Protection** | `pii_redactor.py` strips emails, phones, addresses from all logs/traces |
| **Data at Rest** | AES-256 encryption via Azure Blob Storage service encryption + PostgreSQL TDE |
| **Data Deletion** | Account deletion triggers cascade delete within 72 hours |
| **Bias Prevention** | Scoring algorithm explicitly excludes protected attributes and proxy signals |

### Prompt Injection Sanitization

```python
# backend/app/security/sanitizer.py
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"system:\s*you\s+are",
    r"forget\s+(everything|all|your\s+instructions)",
    r"new\s+instructions:",
    r"override\s+(system|instructions)",
    r"\[SYSTEM\]",
    r"```system",
]

def sanitize_input(text: str) -> str:
    """Remove known prompt injection patterns from user input."""
    sanitized = text
    for pattern in INJECTION_PATTERNS:
        sanitized = re.sub(pattern, "[REDACTED]", sanitized, flags=re.IGNORECASE)
    return sanitized
```

---

## Document Generation Design

### ATS-Safe DOCX Generation

```python
# backend/app/services/document_service.py
from docx import Document
from docx.shared import Pt, Inches, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH

ATS_SAFE_CONFIG = {
    "font_name": "Calibri",
    "font_size_body": Pt(11),
    "font_size_header": Pt(14),
    "font_size_section": Pt(12),
    "margins": Inches(1),
    "line_spacing": 1.15,
    "section_headers": ["Contact Information", "Summary", "Experience", "Education", "Skills", "Certifications"],
}

class ATSDocumentGenerator:
    """Generate ATS-safe DOCX documents."""
    
    def generate_resume_docx(self, tailored_resume: TailoredResume) -> bytes:
        doc = Document()
        self._set_margins(doc)
        
        for section in tailored_resume.sections:
            # Section header
            heading = doc.add_heading(section.section_name, level=1)
            self._style_heading(heading)
            
            # Section content (plain paragraphs, no tables/columns)
            for paragraph_text in section.content.split("\n\n"):
                para = doc.add_paragraph(paragraph_text)
                self._style_paragraph(para)
        
        buffer = BytesIO()
        doc.save(buffer)
        return buffer.getvalue()
    
    def _set_margins(self, doc):
        for section in doc.sections:
            section.top_margin = ATS_SAFE_CONFIG["margins"]
            section.bottom_margin = ATS_SAFE_CONFIG["margins"]
            section.left_margin = ATS_SAFE_CONFIG["margins"]
            section.right_margin = ATS_SAFE_CONFIG["margins"]
    
    def _style_paragraph(self, para):
        para.style.font.name = ATS_SAFE_CONFIG["font_name"]
        para.style.font.size = ATS_SAFE_CONFIG["font_size_body"]
        para.paragraph_format.line_spacing = ATS_SAFE_CONFIG["line_spacing"]
    
    def _style_heading(self, heading):
        for run in heading.runs:
            run.font.name = ATS_SAFE_CONFIG["font_name"]
            run.font.size = ATS_SAFE_CONFIG["font_size_section"]
            run.font.bold = True
```

### PDF Generation

PDF generation uses `weasyprint` or `reportlab` to convert the DOCX content (or an intermediate HTML representation) into PDF while maintaining ATS-safe formatting constraints. The PDF must be text-selectable (not image-based).

---

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Score Computation Integrity

*For any* parsed resume and parsed JD, the computed overall score SHALL equal `round(hard_skill_score * 0.40 + title_alignment_score * 0.20 + keyword_match_score * 0.25 + achievement_relevance_score * 0.15)` within ±1, and both the overall score and each category score SHALL be in the range [0, 100].

**Validates: Requirements 6.9, 6.10, 6.11**

### Property 2: Claim Preservation (No Fabrication)

*For any* tailored resume produced by the system, every employer name, job title, employment date, degree, and certification in the tailored output SHALL exist verbatim in the source resume. The set of factual claims in the tailored resume SHALL be a subset of the factual claims extractable from the source resume.

**Validates: Requirements 9.4, 9.5, 9.7, 9.8, 10.5**

### Property 3: Two-Pass Score Monotonicity

*For any* analysis run that completes both scoring passes, the Pass 2 score (tailored resume vs JD) SHALL be greater than or equal to the Pass 1 score (original resume vs JD).

**Validates: Requirements 7.6**

### Property 4: Cover Letter Constraints

*For any* generated cover letter, the word count SHALL be between 250 and 350 inclusive, and the letter SHALL contain the company name and role title extracted from the parsed JD.

**Validates: Requirements 11.1, 11.2, 11.9**

### Property 5: Parser Round-Trip

*For any* valid `ParsedResume` structure R, `parse(format(R))` SHALL produce a structure equivalent to R. Similarly, *for any* valid `ParsedJD` structure J, `parse(format(J))` SHALL produce a structure equivalent to J.

**Validates: Requirements 4.10, 5.8**

### Property 6: Gap Analysis Completeness

*For any* gap report, every item in the gap list SHALL reference a specific JD requirement that is not met by the source resume. The union of matched items and gap items SHALL cover all JD must-have requirements.

**Validates: Requirements 19.4**

### Property 7: ATS Check Determinism

*For any* resume input, running ATS checks twice on identical input SHALL produce identical results (same risks, same severities, same remediation suggestions).

**Validates: Requirements 8.1, 8.2, 8.3**

### Property 8: Interview Question Count

*For any* generated interview guide, the total question count SHALL be between 11 and 14 inclusive, with 8-10 behavioral questions and 3-4 technical questions.

**Validates: Requirements 12.1, 12.2, 12.8**

### Property 9: Score Improvement Truthfulness

*For any* two-pass analysis run, every keyword added in the tailored resume that was not in the original SHALL map to an existing factual claim in the source resume. No keyword is added without supporting evidence.

**Validates: Requirements 7.5, 9.3**

### Property 10: PII Redaction in Logs

*For any* log entry emitted by the system, the entry SHALL NOT contain unredacted email addresses, phone numbers, or physical addresses. All PII patterns shall be replaced with redaction markers.

**Validates: Requirements 15.5, 17.6**

### Property 11: Bias-Free Scoring (Career Path Neutrality)

*For any* pair of resumes that are identical in skills, achievements, and relevant experience but differ in career path linearity (employment gaps, job-change frequency, or traditional vs non-traditional work history), the system SHALL produce equivalent scores (±2) when evaluated against the same JD.

**Validates: Requirements 6.5, 6.6, 22.1, 22.2, 22.3, 22.7**

### Property 12: Semantic Equivalence Symmetry

*For any* pair of skill terms (X, Y) where X is configured as a synonym of Y, matching a resume containing X against a JD requiring Y SHALL produce the same match contribution as matching a resume containing Y against the same JD.

**Validates: Requirements 23.1, 23.3**

### Property 13: AI Output Schema Conformance

*For any* AI agent invocation, the output SHALL parse successfully against the agent's predefined JSON schema (Pydantic model) without validation errors.

**Validates: Requirements 21.1, 21.6**

### Property 14: Prompt Injection Resistance

*For any* user input containing known prompt injection patterns (e.g., "ignore previous instructions", "system: you are now..."), the sanitized input passed to AI agents SHALL not contain these patterns, and the agent output SHALL conform to the expected schema.

**Validates: Requirements 15.10, 15.11**

### Property 15: Grounding Completeness

*For any* factual claim in a tailored resume or cover letter, there SHALL exist a citation reference pointing to a specific section or text in the source resume. Zero ungrounded claims are permitted in verified output.

**Validates: Requirements 10.1, 10.5, 11.7, 21.3**

---

## Error Handling

### Error Categories and Responses

| Category | HTTP Code | User Message | System Action |
|----------|-----------|--------------|---------------|
| **Authentication failure** | 401 | "Invalid credentials" (generic) | Log attempt, rate-limit check |
| **File too large** | 413 | "File exceeds 5 MB limit" | Reject before upload to blob |
| **Unsupported format** | 400 | "Only PDF and DOCX files accepted" | Reject at validation layer |
| **Rate limit exceeded** | 429 | "Analysis limit reached. Try again in X minutes" | Return `Retry-After` header |
| **Agent failure (retries exhausted)** | 500 | "Analysis partially failed. View available results." | Return partial results, log failure |
| **LLM unavailable (circuit open)** | 503 | "AI service temporarily unavailable. Request queued." | Queue for retry, try fallback model |
| **Schema validation failure** | 500 | "Internal processing error. Retrying." | Log malformed output, retry with same input |
| **Token budget exceeded** | 200 (partial) | Results delivered with truncation warning | Truncate at safe boundary, log warning |
| **Non-English resume** | 422 | "Only English-language resumes are supported" | Reject with clear guidance |
| **JD URL unreachable** | 422 | "Could not fetch job posting. Please paste the text instead." | Log URL and status code |
| **Input too short (JD < 50 chars)** | 422 | "Extracted text too short. Please paste JD manually." | Prompt manual input |

### Retry Strategy

```python
# backend/app/orchestrator/retry.py
RETRY_CONFIG = {
    "max_retries": 2,
    "base_delay_seconds": 1.0,
    "max_delay_seconds": 8.0,
    "exponential_base": 2,
    "retryable_exceptions": [
        "RateLimitError",
        "ServiceUnavailableError",
        "TimeoutError",
        "SchemaValidationError",
    ],
}

async def retry_with_backoff(agent_fn, input_data, config=RETRY_CONFIG):
    for attempt in range(config["max_retries"] + 1):
        try:
            result = await agent_fn(input_data)
            return result
        except tuple(config["retryable_exceptions"]) as e:
            if attempt == config["max_retries"]:
                raise AgentFailedError(agent_name, str(e))
            delay = min(
                config["base_delay_seconds"] * (config["exponential_base"] ** attempt),
                config["max_delay_seconds"]
            )
            await asyncio.sleep(delay)
```

### Circuit Breaker (Model Fallback)

```python
# backend/app/orchestrator/circuit_breaker.py
class ModelCircuitBreaker:
    """
    If primary model fails N times in M minutes, switch to fallback.
    Reset after recovery period.
    """
    def __init__(self):
        self.failure_count = 0
        self.failure_threshold = 3
        self.recovery_seconds = 60
        self.state = "closed"  # closed, open, half_open
    
    async def call(self, primary_fn, fallback_fn, input_data):
        if self.state == "open":
            return await fallback_fn(input_data)
        try:
            result = await primary_fn(input_data)
            self.reset()
            return result
        except (RateLimitError, ServiceUnavailableError):
            self.failure_count += 1
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
                schedule_recovery(self.recovery_seconds)
            return await fallback_fn(input_data)
```

### Partial Results Handling

When an agent fails after retries, the orchestrator:
1. Marks the pipeline status as `"partial"`
2. Stores all successfully completed agent outputs
3. Returns available results to the user with clear indicators of what failed
4. Logs the failure with correlation ID for debugging

---

## Testing Strategy

### Testing Approach Overview

The system uses a dual testing strategy:

1. **Property-Based Tests** — Verify universal correctness properties across randomized inputs (minimum 100 iterations per property)
2. **Unit Tests** — Verify specific examples, edge cases, and integration points
3. **Integration Tests** — Verify end-to-end flows with mocked external services

### Property-Based Testing Configuration

**Library**: [Hypothesis](https://hypothesis.readthedocs.io/) (Python)

**Configuration**:
```python
from hypothesis import settings, given, strategies as st

# Global settings for all property tests
settings.register_profile("ci", max_examples=200, deadline=30000)
settings.register_profile("dev", max_examples=100, deadline=10000)
settings.load_profile(os.getenv("HYPOTHESIS_PROFILE", "dev"))
```

**Property Test Requirements**:
- Each property test runs minimum 100 iterations
- Each test is tagged with its design property reference
- Tag format: `# Feature: resume-jd-match-ai, Property {N}: {title}`

### Property Test Implementation Plan

| Property | Test File | Generators Needed |
|----------|-----------|-------------------|
| P1: Score Computation Integrity | `tests/property/test_scoring.py` | Random category scores (0-100) |
| P2: Claim Preservation | `tests/property/test_claim_verification.py` | Random ParsedResume + TailoredResume pairs |
| P3: Two-Pass Monotonicity | `tests/property/test_two_pass.py` | Random resume/JD/tailored combinations |
| P4: Cover Letter Constraints | `tests/property/test_cover_letter.py` | Random CoverLetter instances |
| P5: Parser Round-Trip | `tests/property/test_parsers.py` | Random ParsedResume and ParsedJD structures |
| P6: Gap Analysis Completeness | `tests/property/test_gap_analysis.py` | Random GapReport + ParsedJD pairs |
| P7: ATS Check Determinism | `tests/property/test_ats_check.py` | Random resume text inputs |
| P8: Interview Question Count | `tests/property/test_interview_prep.py` | Random InterviewGuide instances |
| P9: Score Improvement Truthfulness | `tests/property/test_score_improvement.py` | Random tailored resume with keyword additions |
| P10: PII Redaction | `tests/property/test_pii_redaction.py` | Random text with embedded PII patterns |
| P11: Bias-Free Scoring | `tests/property/test_bias_free.py` | Resume pairs differing only in career path |
| P12: Semantic Symmetry | `tests/property/test_semantic.py` | Random synonym pairs from mapping |
| P13: Schema Conformance | `tests/property/test_schema.py` | Random agent outputs (fuzzed JSON) |
| P14: Prompt Injection Resistance | `tests/property/test_sanitizer.py` | Random text with injection patterns |
| P15: Grounding Completeness | `tests/property/test_grounding.py` | Random tailored content with citations |

### Unit Test Focus Areas

- Auth: Password complexity validation, token expiry, OAuth flow
- Input validation: File size/type checks, text length limits
- Scoring algorithm: Weight calculation with known inputs
- Semantic matching: Known synonym pairs, abbreviation expansion
- Document generation: DOCX structure validation, font/margin checks
- PII redaction: Known PII patterns in sample text
- Rate limiting: Counter increment and reset logic

### Integration Test Focus Areas

- Full pipeline execution with mocked LLM responses
- Azure Blob Storage upload/download (with Azurite emulator)
- Database CRUD operations (with test PostgreSQL)
- Authentication flow end-to-end
- Document generation file validity (DOCX/PDF parseable)
- Email delivery (with mock SMTP)

### Test Infrastructure

```
tests/
├── conftest.py                    # Shared fixtures, DB setup, mock providers
├── property/
│   ├── conftest.py                # Hypothesis settings, custom strategies
│   ├── strategies.py              # Reusable generators for domain objects
│   ├── test_scoring.py
│   ├── test_claim_verification.py
│   ├── test_two_pass.py
│   ├── test_cover_letter.py
│   ├── test_parsers.py
│   ├── test_gap_analysis.py
│   ├── test_ats_check.py
│   ├── test_interview_prep.py
│   ├── test_score_improvement.py
│   ├── test_pii_redaction.py
│   ├── test_bias_free.py
│   ├── test_semantic.py
│   ├── test_schema.py
│   ├── test_sanitizer.py
│   └── test_grounding.py
├── unit/
│   ├── test_auth.py
│   ├── test_input_validation.py
│   ├── test_scoring_algorithm.py
│   ├── test_semantic_map.py
│   ├── test_document_generator.py
│   ├── test_pii_redactor.py
│   └── test_rate_limiter.py
└── integration/
    ├── test_pipeline.py
    ├── test_storage.py
    ├── test_database.py
    ├── test_auth_flow.py
    └── test_document_output.py
```

---

## Environment Variables

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/resumejdmatch

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://<resource>.openai.azure.com/
AZURE_OPENAI_API_KEY=<key>
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-5-mini
AZURE_OPENAI_FALLBACK_DEPLOYMENT=gpt-4o-mini
AZURE_OPENAI_API_VERSION=2024-08-06

# Azure Blob Storage
AZURE_STORAGE_CONNECTION_STRING=<connection_string>
AZURE_STORAGE_CONTAINER_NAME=resumes

# Authentication
JWT_SECRET_KEY=<secret>
JWT_ALGORITHM=RS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# OAuth
OAUTH_GOOGLE_CLIENT_ID=<id>
OAUTH_GOOGLE_CLIENT_SECRET=<secret>
OAUTH_MICROSOFT_CLIENT_ID=<id>
OAUTH_MICROSOFT_CLIENT_SECRET=<secret>

# OpenTelemetry
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
OTEL_SERVICE_NAME=resumejdmatch-backend

# Rate Limiting
RATE_LIMIT_ANALYSES_PER_HOUR=10
REDIS_URL=redis://localhost:6379/0

# Email
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USERNAME=apikey
SMTP_PASSWORD=<sendgrid_api_key>
FROM_EMAIL=noreply@resumejdmatch.ai

# App
APP_ENV=production
LOG_LEVEL=INFO
CORS_ORIGINS=https://app.resumejdmatch.ai
PROMPT_VERSION=v1
SEMANTIC_MAPPINGS_PATH=config/semantic_mappings.yaml
```
