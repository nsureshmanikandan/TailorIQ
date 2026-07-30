# Implementation Tasks

## Task 1: Project Setup and Configuration
- [x] 1.1 Initialize backend Python project with FastAPI, pyproject.toml, and requirements.txt
- [x] 1.2 Initialize frontend React + TypeScript + Tailwind project with Vite
- [x] 1.3 Create Docker Compose for local development (PostgreSQL, Redis, backend, frontend)
- [x] 1.4 Create backend configuration module with Pydantic Settings (environment variables)
- [x] 1.5 Set up Alembic for database migrations

## Task 2: Database Schema and Models
- [x] 2.1 Create SQLAlchemy ORM models (User, Resume, ResumeVersion, JobDescription, MatchResult, GeneratedArtifact, AuditLog)
- [x] 2.2 Create initial Alembic migration for all tables
- [x] 2.3 Create Pydantic request/response schemas for API layer

## Task 3: Authentication System
- [x] 3.1 Implement JWT auth service (token generation, validation, refresh)
- [x] 3.2 Create auth API routes (register, login, refresh, password reset)
- [x] 3.3 Implement auth middleware and dependency injection
- [ ] 3.4 Add rate limiting middleware

## Task 4: Resume and JD Input APIs
- [x] 4.1 Implement resume upload endpoint (PDF/DOCX to Azure Blob Storage)
- [x] 4.2 Implement resume text paste endpoint
- [x] 4.3 Implement resume version management (save/load up to 3 versions)
- [x] 4.4 Implement JD text input endpoint
- [x] 4.5 Implement JD URL fetch endpoint (HTML stripping, text extraction)

## Task 5: AI Agent Base Infrastructure
- [x] 5.1 Create BaseAgent abstract class with execute/validate/health_check
- [x] 5.2 Create LLM service wrapper for Azure OpenAI (structured output, token tracking)
- [x] 5.3 Create prompt template loader (versioned YAML prompts)
- [x] 5.4 Implement retry logic with exponential backoff
- [x] 5.5 Implement circuit breaker for model fallback
- [x] 5.6 Create input sanitizer for prompt injection defense

## Task 6: AI Agents Implementation
- [x] 6.1 Implement ResumeParserAgent with prompt template
- [x] 6.2 Implement JDParserAgent with prompt template
- [x] 6.3 Implement MatchScoringAgent with weighted formula
- [x] 6.4 Implement GapAnalysisAgent
- [x] 6.5 Implement ResumeTailoringAgent
- [x] 6.6 Implement ClaimVerificationAgent
- [x] 6.7 Implement CoverLetterAgent
- [x] 6.8 Implement InterviewPrepAgent
- [x] 6.9 Implement ATSCheckAgent
- [x] 6.10 Implement PackageGenerationAgent (DOCX/PDF generation)

## Task 7: Pipeline Orchestrator
- [x] 7.1 Implement pipeline orchestrator with 5-phase execution order
- [x] 7.2 Implement analysis run API (POST /analysis/run, GET /analysis/{run_id})
- [x] 7.3 Implement partial results handling on agent failure
- [x] 7.4 Add token usage tracking and cost computation per run

## Task 8: Semantic Keyword Intelligence
- [x] 8.1 Create semantic synonym mapping config (YAML)
- [x] 8.2 Implement SemanticMap class with equivalence checking
- [x] 8.3 Integrate semantic matching into scoring agent

## Task 9: Document Generation and Downloads
- [x] 9.1 Implement ATS-safe DOCX generator using python-docx
- [ ] 9.2 Implement PDF generation
- [ ] 9.3 Implement ZIP bundle packaging
- [x] 9.4 Create download API routes
- [ ] 9.5 Implement email delivery of package

## Task 10: OpenTelemetry Observability
- [x] 10.1 Set up OpenTelemetry tracing with FastAPI auto-instrumentation
- [x] 10.2 Add custom spans for each agent with attributes
- [x] 10.3 Implement PII redactor for logs and traces
- [x] 10.4 Add metrics (request count, latency, token usage, errors)

## Task 11: Frontend Dashboard
- [x] 11.1 Set up React project structure with routing and state management (Zustand)
- [x] 11.2 Build auth pages (login, register)
- [x] 11.3 Build resume upload/paste component
- [x] 11.4 Build JD input component (text + URL)
- [x] 11.5 Build score card component with before/after gauge and delta
- [x] 11.6 Build category breakdown component
- [x] 11.7 Build keyword panel (matched green, added amber)
- [x] 11.8 Build tailored resume preview with highlighted changes
- [x] 11.9 Build cover letter collapsible panel
- [x] 11.10 Build interview guide collapsible panel
- [x] 11.11 Build download actions bar
- [x] 11.12 Integrate API client with all backend endpoints

## Task 12: Security and Privacy
- [x] 12.1 Implement PII redaction in all logging
- [x] 12.2 Add input validation and sanitization across all endpoints
- [ ] 12.3 Implement user consent flow before AI processing
- [ ] 12.4 Implement account deletion with cascade data removal

## Task 13: Testing
- [x] 13.1 Write property-based tests for scoring integrity (P1)
- [x] 13.2 Write property-based tests for claim preservation (P2)
- [x] 13.3 Write property-based tests for PII redaction (P10)
- [x] 13.4 Write unit tests for auth, input validation, semantic matching
- [ ] 13.5 Write integration tests for full pipeline with mocked LLM
