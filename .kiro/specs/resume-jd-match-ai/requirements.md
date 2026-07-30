# Requirements Document

## Product Naming

Before diving into requirements, here are 10 modern product name suggestions for the "ResumeJDMatch AI" concept:

| # | Name | Rationale |
|---|------|-----------|
| 1 | **FitCheck AI** | Casual, modern — "fit check" resonates with both fashion and job-fit culture |
| 2 | **MatchCraft** | Implies precision crafting of resume-to-JD alignment |
| 3 | **ResumeSync AI** | Signals synchronization between resume and job description |
| 4 | **TailorIQ** | Combines tailoring + intelligence; memorable and brandable |
| 5 | **ApplySharp** | Action-oriented; implies sharpening your application |
| 6 | **HireAlign** | Clear value prop — aligning you with hiring criteria |
| 7 | **Jobtune** | Short, catchy — "tune" your resume to the job |
| 8 | **CareerLens** | Implies seeing your career through the lens of the opportunity |
| 9 | **MatchPilot** | Suggests guided navigation toward a job match |
| 10 | **ResuFit** | Compact portmanteau of Resume + Fit; domain-friendly |

**Recommended:** **TailorIQ** — It communicates the core value (tailoring resumes intelligently), is brandable, domain-available-friendly, and works well as both a product name and a verb ("TailorIQ your resume"). It avoids the overused "AI" suffix while implying intelligence through "IQ".

> Note: The working name "ResumeJDMatch AI" is used throughout this document. Replace with the chosen brand name before launch.

---

## Introduction

ResumeJDMatch AI is a web application that helps job candidates optimize their application materials. Given a resume and a job description, the system analyzes alignment, identifies gaps, produces a truthfully tailored resume, generates a personalized cover letter, and prepares an interview guide — all while strictly preserving factual accuracy. The system never fabricates employment history, dates, employers, degrees, certifications, achievements, or skills not present in the source resume.

The platform uses modular AI agents orchestrated to perform parsing, scoring, tailoring, generation, and quality-checking tasks. It is designed for ATS compatibility, privacy-first operation, and cost-efficient AI usage.

---

## Glossary

- **System**: The ResumeJDMatch AI web application as a whole
- **Frontend**: The React + TypeScript + Tailwind CSS client application
- **Backend**: The Python FastAPI server application
- **Parser**: A component that extracts structured data from unstructured text
- **Resume_Parser_Agent**: AI agent responsible for extracting structured data from resume content
- **JD_Parser_Agent**: AI agent responsible for extracting structured data from job description content
- **Match_Scoring_Agent**: AI agent that computes ATS-style alignment scores
- **Gap_Analysis_Agent**: AI agent that identifies missing skills, keywords, and qualifications
- **Resume_Tailoring_Agent**: AI agent that rewrites resume content for JD alignment while preserving truth
- **Cover_Letter_Agent**: AI agent that generates personalized cover letters
- **Interview_Prep_Agent**: AI agent that produces interview questions and STAR-format answer skeletons
- **ATS_Check_Agent**: AI agent that evaluates resume formatting for ATS compatibility
- **Claim_Verification_Agent**: AI agent that validates tailored output against source resume claims
- **Package_Generation_Agent**: AI agent that assembles final deliverables into downloadable documents
- **ATS**: Applicant Tracking System — software used by employers to screen resumes
- **JD**: Job Description
- **STAR**: Situation, Task, Action, Result — behavioral interview answer framework
- **Score**: A numeric value 0–100 representing resume-to-JD alignment
- **Tailored_Resume**: A version of the candidate's resume rewritten for JD alignment without fabrication
- **Source_Resume**: The original resume uploaded or pasted by the user
- **Hard_Skill**: A specific technical or domain skill (e.g., Python, SQL, AWS)
- **Soft_Skill**: An interpersonal or behavioral skill (e.g., leadership, communication)
- **Keyword_Match**: A JD term or phrase found verbatim or semantically in the resume
- **PII**: Personally Identifiable Information
- **DOCX**: Microsoft Word Open XML Document format
- **PDF**: Portable Document Format
- **Azure_Blob_Storage**: Microsoft Azure object storage service for resume files
- **OpenTelemetry**: Observability framework for distributed tracing, metrics, and logging
- **OAuth**: Open Authorization standard for delegated authentication

---

## SME Review Notes

### GenAI SME Review Findings (Applied)
1. **Hallucination guardrails** — Added explicit LLM output validation with confidence thresholds and structured output enforcement
2. **Prompt injection defense** — Added requirement for input sanitization against adversarial resume/JD content
3. **Temperature and reproducibility** — Added requirement for low-temperature inference with seed pinning for scoring consistency
4. **Token budget management** — Added per-agent token budget caps to prevent runaway costs on long resumes
5. **Semantic matching vs. exact match** — Clarified that keyword matching must support synonyms and contextual equivalence (e.g., "ML" = "Machine Learning")
6. **Multi-language resume support** — Added requirement for English-language resumes only in MVP with clear error handling for non-English input
7. **LLM fallback and circuit breaker** — Added requirement for model fallback when primary model is unavailable or rate-limited
8. **Grounding and citation** — Added requirement that every AI-generated claim must cite the specific resume section it draws from

### HR Manager SME Review Findings (Applied)
1. **Career gap sensitivity** — Added requirement that the system must not penalize or flag employment gaps, as this introduces bias
2. **Job-hopping neutrality** — System must not penalize frequency of job changes in scoring
3. **Non-traditional career paths** — System must fairly score career changers, freelancers, and non-linear career paths
4. **Soft skill handling** — Added requirement for extracting and matching soft skills from context (not just keyword lists)
5. **Seniority inference accuracy** — Added guardrails for seniority-level matching to avoid penalizing overqualified or career-transitioning candidates
6. **Industry terminology normalization** — Added requirement to recognize equivalent job titles across industries (e.g., "Software Engineer" ≈ "Software Developer" ≈ "SDE")
7. **Volunteer and side-project recognition** — Added requirement to include volunteer work, open-source contributions, and side projects as valid experience evidence
8. **Cover letter cultural adaptation** — Added requirement for region-appropriate cover letter conventions
9. **Interview prep realism** — Added requirement that generated questions must reflect actual industry interview patterns, not textbook-only questions

---

## Requirements

### Requirement 1: User Authentication

**User Story:** As a candidate, I want to create an account and log in securely, so that I can save my resume versions and access my results across sessions.

#### Acceptance Criteria

1. THE System SHALL provide email/password registration with email verification
2. THE System SHALL provide OAuth login via at least one provider (Google or Microsoft)
3. WHEN a user submits valid credentials, THE System SHALL issue a session token within 2 seconds
4. WHEN a user submits invalid credentials, THE System SHALL return an authentication error without revealing whether the email exists
5. IF a session token expires, THEN THE System SHALL require re-authentication
6. THE System SHALL enforce password complexity: minimum 8 characters, at least one uppercase letter, one lowercase letter, one digit, and one special character
7. WHEN a user requests password reset, THE System SHALL send a time-limited reset link valid for 30 minutes

---

### Requirement 2: Resume Input and Storage

**User Story:** As a candidate, I want to upload my resume in multiple formats or paste it as text, so that the system can parse and analyze it.

#### Acceptance Criteria

1. WHEN a user uploads a file, THE System SHALL accept PDF and DOCX formats up to 5 MB
2. WHEN a user pastes text into the resume input field, THE System SHALL accept plain text up to 50,000 characters
3. IF a user uploads an unsupported file format, THEN THE System SHALL display an error message specifying accepted formats
4. IF a user uploads a file exceeding 5 MB, THEN THE System SHALL display an error message specifying the size limit
5. WHEN a file is uploaded, THE System SHALL store the file in Azure_Blob_Storage with encryption at rest
6. THE System SHALL allow each user to save up to 3 resume versions labeled as Fresher, Experienced, or Domain-specific
7. WHEN a user saves a resume version, THE System SHALL associate the version with the user account and persist it in the database
8. WHEN a user selects a previously saved resume version, THE System SHALL load that version for analysis

---

### Requirement 3: Job Description Input

**User Story:** As a candidate, I want to provide a job description by pasting text or providing a URL, so that the system can extract requirements for comparison.

#### Acceptance Criteria

1. WHEN a user pastes JD text, THE System SHALL accept plain text up to 50,000 characters
2. WHEN a user provides a JD URL, THE Backend SHALL fetch the page content within 10 seconds
3. WHEN a JD URL is fetched, THE Backend SHALL strip HTML tags, navigation elements, advertisements, and cookie banners to extract clean job description text
4. IF a JD URL is unreachable or returns a non-200 status, THEN THE System SHALL display an error message indicating the URL could not be fetched
5. IF the extracted text from a URL contains fewer than 50 characters of job-relevant content, THEN THE System SHALL prompt the user to paste the JD manually
6. THE System SHALL preserve the original JD text for reference alongside parsed structured data

---

### Requirement 4: Resume Parsing

**User Story:** As a candidate, I want my resume automatically parsed into structured fields, so that the system can perform precise matching and tailoring.

#### Acceptance Criteria

1. WHEN a resume is submitted, THE Resume_Parser_Agent SHALL extract: candidate name, email, phone number, LinkedIn URL, location, skills list, job titles, employer names, employment dates, years of experience, education entries, certifications, projects, quantifiable achievements, tools/platforms/technologies, domain keywords, volunteer work, open-source contributions, and side projects
2. WHEN parsing completes, THE Resume_Parser_Agent SHALL return structured JSON conforming to a defined resume schema
3. IF a field cannot be confidently extracted, THEN THE Resume_Parser_Agent SHALL mark that field as null rather than guessing
4. THE Resume_Parser_Agent SHALL preserve the original text of each section alongside extracted structured data
5. WHEN a resume contains multiple roles, THE Resume_Parser_Agent SHALL extract each role as a separate entry with its own employer, title, dates, and achievements
6. THE Resume_Parser_Agent SHALL extract soft skills from contextual descriptions (e.g., "led a team of 5" implies leadership) in addition to explicitly listed skills
7. THE Resume_Parser_Agent SHALL recognize and extract volunteer work, freelance engagements, open-source contributions, and side projects as valid experience entries
8. THE Resume_Parser_Agent SHALL normalize job titles to canonical forms for matching purposes while preserving the original title text (e.g., "SDE" → "Software Development Engineer", "Dev" → "Developer")
9. THE Resume_Parser_Agent SHALL only accept English-language resumes in the MVP; IF a non-English resume is detected, THEN THE System SHALL inform the user that only English resumes are supported
10. FOR ALL parsed resumes, formatting the parsed data back to text and re-parsing SHALL produce an equivalent structured object (round-trip property)

---

### Requirement 5: Job Description Parsing

**User Story:** As a candidate, I want the job description automatically parsed into structured requirements, so that matching can identify specific gaps.

#### Acceptance Criteria

1. WHEN a JD is submitted, THE JD_Parser_Agent SHALL extract: company name, role title, must-have skills, nice-to-have skills, responsibilities, seniority level, required certifications, domain requirements, and ATS-relevant keywords and phrases
2. WHEN parsing completes, THE JD_Parser_Agent SHALL return structured JSON conforming to a defined JD schema
3. IF a field is not present in the JD text, THEN THE JD_Parser_Agent SHALL mark that field as null
4. THE JD_Parser_Agent SHALL categorize each extracted skill as must-have or nice-to-have based on JD language signals (e.g., "required" vs "preferred", "bonus", "nice to have")
5. THE JD_Parser_Agent SHALL normalize industry-specific job title variations to canonical forms for matching (e.g., "Software Engineer" ≈ "Software Developer" ≈ "SDE" ≈ "Programmer")
6. THE JD_Parser_Agent SHALL distinguish between hard skills and soft skills in the extracted requirements
7. THE JD_Parser_Agent SHALL extract implied seniority indicators from context (e.g., "10+ years", "lead a team", "strategic vision") beyond explicit title-level labels
8. FOR ALL parsed JDs, formatting the parsed data back to text and re-parsing SHALL produce an equivalent structured object (round-trip property)

---

### Requirement 6: Match Scoring Engine

**User Story:** As a candidate, I want an ATS-style score comparing my resume to the JD, so that I understand how well I match and where to improve.

#### Acceptance Criteria

1. WHEN both resume and JD are parsed, THE Match_Scoring_Agent SHALL compute an overall score from 0 to 100
2. THE Match_Scoring_Agent SHALL apply the following weight formula: hard skill overlap 40%, title/seniority alignment 20%, keyword/phrase match 25%, quantifiable achievement relevance 15%
3. THE Match_Scoring_Agent SHALL return: overall score, category breakdown scores, reasoning text for each category, list of matched keywords, list of missing keywords, skills gap, certification gap, and achievement/metrics gap
4. THE Match_Scoring_Agent SHALL use semantic matching for keywords — recognizing synonyms, abbreviations, and contextual equivalences (e.g., "ML" = "Machine Learning", "CI/CD" = "Continuous Integration/Continuous Deployment")
5. THE Match_Scoring_Agent SHALL NOT penalize employment gaps, job-change frequency, or non-linear career paths in scoring
6. THE Match_Scoring_Agent SHALL fairly score non-traditional experience including freelance work, volunteer roles, open-source contributions, and career transitions
7. THE Match_Scoring_Agent SHALL use low-temperature inference (temperature ≤ 0.2) with a fixed seed to produce consistent scores for identical inputs within the same model version
8. THE Match_Scoring_Agent SHALL NOT infer or use age, graduation year (as proxy for age), gender, ethnicity, nationality, or any protected attribute in score computation
9. FOR ALL score computations, the overall score SHALL equal the weighted sum of category scores (within ±1 due to rounding)
10. FOR ALL score computations, each category score SHALL be between 0 and 100 inclusive
11. FOR ALL score computations, the overall score SHALL be between 0 and 100 inclusive

---

### Requirement 7: Two-Pass Scoring

**User Story:** As a candidate, I want to see my original score and my improved score after tailoring, so that I can quantify the value of optimization.

#### Acceptance Criteria

1. WHEN analysis begins, THE System SHALL compute Pass 1 score using the original resume against the JD
2. WHEN tailoring completes, THE System SHALL compute Pass 2 score using the tailored resume against the JD
3. THE System SHALL display: initial score, improved score, and numeric delta (e.g., "62 → 89, +27")
4. THE System SHALL display category-level before/after comparisons for all four scoring categories
5. THE System SHALL achieve score improvement only through truthful alignment techniques, not keyword stuffing
6. FOR ALL two-pass analyses, the Pass 2 score SHALL be greater than or equal to the Pass 1 score

---

### Requirement 8: ATS Friendliness Checks

**User Story:** As a candidate, I want to know if my resume has formatting issues that could cause ATS rejection, so that I can fix them before applying.

#### Acceptance Criteria

1. WHEN a resume is submitted, THE ATS_Check_Agent SHALL scan for: tables, images, headers/footers containing critical information, non-standard fonts, multi-column layouts, graphics-based skill bars, missing standard section headers, and overly complex formatting
2. WHEN an ATS risk is identified, THE ATS_Check_Agent SHALL classify it as critical, warning, or informational
3. WHEN an ATS risk is identified, THE ATS_Check_Agent SHALL provide a specific remediation suggestion
4. THE ATS_Check_Agent SHALL check for the presence of standard section headers: Experience, Education, Skills, and Contact Information
5. IF the resume contains zero critical ATS risks, THEN THE ATS_Check_Agent SHALL mark the resume as ATS-safe

---

### Requirement 9: Resume Tailoring

**User Story:** As a candidate, I want my resume rewritten for the target JD while keeping all facts truthful, so that I can improve my ATS score without misrepresentation.

#### Acceptance Criteria

1. WHEN tailoring is requested, THE Resume_Tailoring_Agent SHALL reorder bullet points to prioritize JD-relevant achievements
2. THE Resume_Tailoring_Agent SHALL strengthen achievement descriptions with clearer impact language while preserving factual accuracy
3. THE Resume_Tailoring_Agent SHALL insert JD keywords only where they are truthfully supported by the Source_Resume content
4. THE Resume_Tailoring_Agent SHALL preserve all employment dates, employer names, job titles, degrees, certifications, and quantifiable metrics from the Source_Resume without modification
5. THE Resume_Tailoring_Agent SHALL NOT add any skill, certification, employer, degree, achievement, or date that does not exist in the Source_Resume
6. THE Resume_Tailoring_Agent SHALL output content in an ATS-safe format without tables, images, columns, or graphics
7. FOR ALL tailored resumes, every employer name, job title, employment date, degree, and certification in the Tailored_Resume SHALL exist in the Source_Resume (claim preservation property)
8. FOR ALL tailored resumes, the set of factual claims in the Tailored_Resume SHALL be a subset of the factual claims in the Source_Resume (no fabrication property)

---

### Requirement 10: Claim Verification

**User Story:** As a candidate, I want assurance that the tailored resume contains no fabricated information, so that I can submit it with confidence.

#### Acceptance Criteria

1. WHEN a tailored resume is generated, THE Claim_Verification_Agent SHALL compare every factual claim in the Tailored_Resume against the Source_Resume
2. THE Claim_Verification_Agent SHALL verify: employer names, job titles, employment dates, degree names, institution names, certification names, quantifiable metrics, and specific skill claims
3. IF a claim in the Tailored_Resume cannot be traced to the Source_Resume, THEN THE Claim_Verification_Agent SHALL flag it as unverified and remove it from the output
4. THE Claim_Verification_Agent SHALL produce a verification report listing each claim and its source location in the original resume
5. FOR ALL verified tailored resumes, the count of unverified claims SHALL be zero

---

### Requirement 11: Cover Letter Generation

**User Story:** As a candidate, I want a personalized cover letter generated from my resume and the target JD, so that I can save time and submit a compelling application.

#### Acceptance Criteria

1. WHEN cover letter generation is requested, THE Cover_Letter_Agent SHALL produce a cover letter between 250 and 350 words
2. THE Cover_Letter_Agent SHALL personalize the letter to the specific company name and role title from the JD
3. THE Cover_Letter_Agent SHALL reference at least 1 and at most 2 specific JD requirements with evidence from the resume
4. THE Cover_Letter_Agent SHALL use a professional, concise tone without generic openers (e.g., no "I am writing to express my interest")
5. THE Cover_Letter_Agent SHALL NOT include any experience, skill, or achievement not present in the Source_Resume
6. THE Cover_Letter_Agent SHALL adapt the letter structure and conventions to the target region/market where identifiable from the JD (e.g., UK vs. US vs. APAC conventions)
7. THE Cover_Letter_Agent SHALL cite the specific resume section or achievement that supports each claim made in the letter (internal grounding reference, not visible to final output)
8. FOR ALL generated cover letters, every factual claim SHALL trace back to the Source_Resume (truthfulness property)
9. FOR ALL generated cover letters, the word count SHALL be between 250 and 350 inclusive

---

### Requirement 12: Interview Preparation Guide

**User Story:** As a candidate, I want interview questions and answer frameworks based on my resume and the JD, so that I can prepare effectively.

#### Acceptance Criteria

1. WHEN interview prep is requested, THE Interview_Prep_Agent SHALL generate 8 to 10 behavioral or role-specific questions
2. THE Interview_Prep_Agent SHALL generate 3 to 4 technical or domain-specific questions based on JD requirements
3. THE Interview_Prep_Agent SHALL provide STAR-format answer skeletons using achievements from the Source_Resume
4. WHEN a question targets a gap where the resume lacks relevant experience, THE Interview_Prep_Agent SHALL mark it as "candidate should provide their own example"
5. THE Interview_Prep_Agent SHALL NOT fabricate examples or achievements not present in the Source_Resume
6. THE Interview_Prep_Agent SHALL generate questions that reflect actual industry interview patterns and current hiring practices, not only textbook scenarios
7. THE Interview_Prep_Agent SHALL include questions that address potential concerns a hiring manager might raise based on the gap analysis (e.g., missing certifications, domain transition)
8. FOR ALL interview guides, the total question count SHALL be between 11 and 14 inclusive

---

### Requirement 13: Document Generation and Delivery

**User Story:** As a candidate, I want to download my tailored resume, cover letter, and interview guide as professional documents, so that I can use them immediately.

#### Acceptance Criteria

1. WHEN download is requested, THE Package_Generation_Agent SHALL generate the tailored resume as a DOCX file with ATS-safe formatting
2. WHEN download is requested, THE Package_Generation_Agent SHALL generate the tailored resume as a PDF file
3. WHEN download is requested, THE Package_Generation_Agent SHALL generate the cover letter as a DOCX file
4. WHEN download is requested, THE Package_Generation_Agent SHALL generate the interview preparation guide as a PDF file
5. THE System SHALL provide a "Download All" option that packages all documents into a single ZIP file
6. THE System SHALL provide an option to email the complete package to the user's registered email address
7. THE Package_Generation_Agent SHALL use ATS-safe formatting in all DOCX outputs: standard fonts (Arial, Calibri, or Times New Roman), single-column layout, no tables for content structure, standard section headers, and 10-12pt font size

---

### Requirement 14: Dashboard UI

**User Story:** As a candidate, I want a single-page dashboard that shows all analysis results in one view, so that I can quickly understand my match status and access all outputs.

#### Acceptance Criteria

1. THE Frontend SHALL render a single-page dashboard with a one-scroll layout containing all analysis sections
2. THE Frontend SHALL display a score card showing before/after scores as visual gauges with the numeric delta
3. THE Frontend SHALL display a category breakdown showing scores for each of the four weighted categories
4. THE Frontend SHALL display a keyword panel with matched keywords in green, added keywords in amber, and each keyword tagged to its resume section
5. THE Frontend SHALL display a tailored resume preview with highlighted changes
6. THE Frontend SHALL display the cover letter in a collapsible panel
7. THE Frontend SHALL display the interview guide in a collapsible panel
8. THE Frontend SHALL provide download action buttons for individual documents and the complete package
9. THE Frontend SHALL be responsive and render correctly on viewports from 320px to 2560px width
10. THE Frontend SHALL meet WCAG 2.1 Level AA accessibility standards including keyboard navigation, screen reader support, and sufficient color contrast ratios (4.5:1 for normal text, 3:1 for large text)

---

### Requirement 15: Privacy and Data Security

**User Story:** As a candidate, I want my personal data protected and never shared or used for model training, so that I can trust the platform with sensitive career information.

#### Acceptance Criteria

1. THE System SHALL encrypt all stored data at rest using AES-256 encryption
2. THE System SHALL transmit all data over TLS 1.2 or higher
3. THE System SHALL NOT share user data with any third party beyond the configured AI provider for processing
4. THE System SHALL NOT permit user data to be used for AI model training
5. THE System SHALL redact PII (names, emails, phone numbers, addresses) from all application logs
6. THE System SHALL enforce rate limiting of 10 analyses per user per hour to prevent abuse and control AI costs
7. WHEN a user requests account deletion, THE System SHALL permanently delete all associated data within 72 hours
8. THE System SHALL obtain explicit user consent before processing resume data through AI services
9. THE System SHALL NOT use protected attributes (age, gender, race, religion, disability, marital status, nationality, sexual orientation) in any scoring computation
10. THE System SHALL sanitize all user-provided text inputs (resume text, JD text, URLs) against prompt injection attacks before passing to AI agents
11. THE System SHALL validate that AI agent outputs conform to expected JSON schemas and reject malformed or suspicious outputs
12. THE System SHALL implement input length guards per AI agent to prevent token budget exhaustion from adversarial inputs
13. THE System SHALL NOT infer protected attributes from proxy signals (e.g., graduation year as proxy for age, name as proxy for ethnicity, university as proxy for socioeconomic status)

---

### Requirement 16: AI Cost Management

**User Story:** As a platform operator, I want AI costs kept below $1 per customization run, so that the service remains economically viable.

#### Acceptance Criteria

1. THE System SHALL track token usage for each AI agent invocation
2. THE System SHALL keep total AI provider cost below $1.00 USD per complete analysis run (parsing + scoring + tailoring + cover letter + interview prep)
3. WHEN token usage approaches 80% of the cost threshold for a run, THE System SHALL log a warning
4. THE System SHALL use the configured Azure OpenAI model specified via environment variables
5. WHERE GPT-5 mini is available in the configured Azure OpenAI deployment, THE System SHALL default to GPT-5 mini for cost efficiency
6. THE System SHALL enforce per-agent token budget caps: Resume_Parser_Agent ≤ 4000 output tokens, JD_Parser_Agent ≤ 3000 output tokens, Match_Scoring_Agent ≤ 2000 output tokens, Resume_Tailoring_Agent ≤ 6000 output tokens, Cover_Letter_Agent ≤ 1500 output tokens, Interview_Prep_Agent ≤ 4000 output tokens, Claim_Verification_Agent ≤ 2000 output tokens
7. IF an agent exceeds its token budget, THEN THE System SHALL truncate the response at a safe boundary and log a budget-exceeded warning
8. THE System SHALL implement a model fallback strategy: if the primary configured model is unavailable or rate-limited, THE System SHALL attempt the request with a configured fallback model before failing

---

### Requirement 17: Observability

**User Story:** As a platform operator, I want comprehensive observability across all operations, so that I can monitor performance, debug issues, and track system health.

#### Acceptance Criteria

1. THE System SHALL emit OpenTelemetry traces for all major operations: resume parsing, JD parsing, scoring, tailoring, cover letter generation, interview prep generation, and document packaging
2. THE System SHALL use a consistent span naming convention: `{agent_name}.{operation}` (e.g., `resume_parser.extract`, `match_scoring.compute`)
3. THE System SHALL attach the following attributes to spans: user_id (hashed), run_id, agent_name, input_token_count, output_token_count, model_name, and duration_ms
4. THE System SHALL emit metrics for: request count, request latency (p50, p95, p99), AI token usage per agent, error count by type, and active user sessions
5. THE System SHALL log errors with correlation IDs linking to the parent trace
6. THE System SHALL redact PII from all trace attributes, metric labels, and log messages

---

### Requirement 18: AI Agent Orchestration

**User Story:** As a developer, I want a modular agent architecture, so that each AI task is isolated, testable, and independently deployable.

#### Acceptance Criteria

1. THE System SHALL implement 10 discrete agents: Resume_Parser_Agent, JD_Parser_Agent, Match_Scoring_Agent, Gap_Analysis_Agent, Resume_Tailoring_Agent, Cover_Letter_Agent, Interview_Prep_Agent, ATS_Check_Agent, Claim_Verification_Agent, and Package_Generation_Agent
2. THE System SHALL execute agents in a defined dependency order: parsing agents first, then scoring and gap analysis, then tailoring, then verification, then cover letter and interview prep in parallel, then package generation
3. WHEN an agent fails, THE System SHALL retry up to 2 times with exponential backoff before reporting failure
4. IF an agent fails after retries, THEN THE System SHALL report the specific failure to the user and allow partial results to be viewed
5. THE System SHALL pass data between agents using a defined schema contract validated at each boundary
6. EACH agent SHALL expose a health check endpoint for monitoring

---

### Requirement 19: Gap Analysis

**User Story:** As a candidate, I want a clear breakdown of what I am missing relative to the JD, so that I can prioritize skill development.

#### Acceptance Criteria

1. WHEN scoring is complete, THE Gap_Analysis_Agent SHALL identify: missing hard skills, missing soft skills, missing certifications, missing domain keywords, experience level gaps, and achievement gaps
2. THE Gap_Analysis_Agent SHALL categorize each gap as critical (must-have requirement) or recommended (nice-to-have requirement)
3. THE Gap_Analysis_Agent SHALL provide actionable suggestions for addressing each gap where applicable
4. FOR ALL gap analyses, every item in the gap list SHALL reference a specific JD requirement that is not met by the Source_Resume

---

### Requirement 20: Performance and Scalability

**User Story:** As a platform operator, I want the system to handle concurrent users with acceptable response times, so that user experience remains smooth.

#### Acceptance Criteria

1. THE System SHALL complete a full analysis run (parsing through package generation) within 60 seconds for 95% of requests
2. THE System SHALL support at least 50 concurrent analysis runs without degradation
3. THE Backend SHALL implement request queuing when concurrent load exceeds capacity
4. WHEN the system is under high load, THE Backend SHALL return estimated wait time to the user
5. THE System SHALL be deployable to Azure App Service, Azure Container Apps, or AKS without architecture changes

---

### Requirement 21: AI Output Validation and Grounding

**User Story:** As a platform operator, I want all AI outputs validated for structural correctness and factual grounding, so that hallucinated or malformed content never reaches the user.

#### Acceptance Criteria

1. EVERY AI agent SHALL return output conforming to a predefined JSON schema; IF output does not conform, THEN THE System SHALL reject it and retry
2. THE System SHALL assign a confidence score (0.0–1.0) to each extracted field; fields below 0.7 confidence SHALL be flagged for user review
3. THE System SHALL validate that every factual statement in generated content (tailored resume, cover letter) can be traced to a specific section of the Source_Resume with a citation reference
4. THE System SHALL detect and reject AI outputs that contain known hallucination patterns: invented company names, fabricated metrics, skills not in source, or dates outside the resume's timeline
5. THE System SHALL log all rejected AI outputs with the rejection reason for prompt improvement feedback loops
6. THE System SHALL enforce structured output mode (JSON mode) for all LLM calls that require structured data extraction

---

### Requirement 22: Bias-Free Scoring and Fair Treatment

**User Story:** As a candidate with a non-traditional career path, I want to be scored fairly regardless of career gaps, job-hopping patterns, or unconventional experience, so that the system does not unfairly disadvantage me.

#### Acceptance Criteria

1. THE Match_Scoring_Agent SHALL NOT penalize resumes for employment gaps of any duration
2. THE Match_Scoring_Agent SHALL NOT penalize resumes for frequent job changes (multiple roles in short periods)
3. THE Match_Scoring_Agent SHALL treat freelance, contract, volunteer, and open-source experience as equivalent to full-time employment for skill-matching purposes
4. THE Match_Scoring_Agent SHALL fairly evaluate career changers by matching transferable skills across domains
5. THE System SHALL NOT use university name, graduation year, or geographic location as scoring signals
6. THE Gap_Analysis_Agent SHALL frame career transitions as "different experience" rather than "missing experience" where transferable skills exist
7. FOR ALL scoring runs, two resumes with identical skills, achievements, and relevant experience SHALL receive equivalent scores regardless of career path linearity

---

### Requirement 23: Semantic Keyword Intelligence

**User Story:** As a candidate, I want the system to recognize that my skills match the JD even when different terminology is used, so that I am not penalized for using industry synonyms.

#### Acceptance Criteria

1. THE Match_Scoring_Agent SHALL maintain a semantic equivalence mapping for common skill synonyms (e.g., "Machine Learning" = "ML", "Amazon Web Services" = "AWS", "Kubernetes" = "K8s")
2. THE Match_Scoring_Agent SHALL recognize contextual skill equivalences (e.g., "managed a distributed team" implies "remote team leadership")
3. THE Match_Scoring_Agent SHALL match abbreviated and expanded forms of certifications (e.g., "PMP" = "Project Management Professional", "AWS SAA" = "AWS Solutions Architect Associate")
4. THE Resume_Tailoring_Agent SHALL expand abbreviations to full forms when the JD uses the full form, and abbreviate when the JD uses abbreviations
5. THE System SHALL allow the semantic mapping to be extended via configuration without code changes

---

## Non-Functional Requirements

### NFR-1: Technology Stack Constraints

1. THE Frontend SHALL be implemented using React, TypeScript, and Tailwind CSS
2. THE Backend SHALL be implemented using Python and FastAPI
3. THE System SHALL use PostgreSQL as the relational database
4. THE System SHALL use Azure Blob Storage for resume file storage
5. THE System SHALL use Azure OpenAI as the AI provider with the model configurable via environment variables
6. THE System SHALL use OpenTelemetry for observability instrumentation
7. THE System SHALL generate DOCX documents using a Python DOCX generation library with ATS-safe formatting

### NFR-2: Deployment

1. THE System SHALL be containerized using Docker
2. THE System SHALL support deployment to Azure App Service, Azure Container Apps, or AKS
3. THE System SHALL use environment variables for all configuration (database URLs, API keys, model names, blob storage connection strings)

### NFR-3: Reliability

1. THE System SHALL maintain 99.5% uptime during business hours (6 AM – 12 AM user local time)
2. THE System SHALL implement graceful degradation: if AI services are unavailable, the system SHALL inform the user and queue the request

---

## Correctness Properties for Property-Based Testing

The following properties are suitable for automated verification using property-based testing:

### P1: Score Computation Integrity
- FOR ALL inputs, overall_score == round(hard_skill_score * 0.40 + title_alignment_score * 0.20 + keyword_match_score * 0.25 + achievement_relevance_score * 0.15), within ±1
- FOR ALL inputs, 0 ≤ category_score ≤ 100
- FOR ALL inputs, 0 ≤ overall_score ≤ 100

### P2: Claim Preservation (No Fabrication)
- FOR ALL tailored resumes, every employer name in tailored output EXISTS in source resume
- FOR ALL tailored resumes, every job title in tailored output EXISTS in source resume
- FOR ALL tailored resumes, every employment date in tailored output EXISTS in source resume
- FOR ALL tailored resumes, every degree in tailored output EXISTS in source resume
- FOR ALL tailored resumes, every certification in tailored output EXISTS in source resume

### P3: Two-Pass Score Monotonicity
- FOR ALL two-pass runs, pass_2_score ≥ pass_1_score

### P4: Cover Letter Constraints
- FOR ALL generated cover letters, 250 ≤ word_count ≤ 350
- FOR ALL generated cover letters, contains(company_name) AND contains(role_title)

### P5: Parser Round-Trip
- FOR ALL valid resume structures R, parse(format(R)) ≡ R
- FOR ALL valid JD structures J, parse(format(J)) ≡ J

### P6: Gap Analysis Completeness
- FOR ALL gap reports, every gap item references a JD requirement not met by the resume
- FOR ALL gap reports, the union of matched_items and gap_items covers all JD must-have requirements

### P7: ATS Check Determinism
- FOR ALL resumes, running ATS checks twice on the same input produces identical results

### P8: Interview Question Count
- FOR ALL interview guides, 11 ≤ total_questions ≤ 14
- FOR ALL interview guides, 8 ≤ behavioral_questions ≤ 10
- FOR ALL interview guides, 3 ≤ technical_questions ≤ 4

### P9: Score Improvement Truthfulness
- FOR ALL two-pass runs, the score delta is achievable only through reordering, rephrasing, and keyword insertion supported by source resume content (no keyword stuffing: every added keyword maps to an existing resume claim)

### P10: PII Redaction in Logs
- FOR ALL log entries, the entry does NOT contain unredacted email addresses, phone numbers, or physical addresses

### P11: Bias-Free Scoring (Career Gap Neutrality)
- FOR ALL pairs of resumes (A, B) where A has employment gaps and B is identical except gaps are filled with placeholder roles, score(A) == score(B) when evaluated against the same JD (gaps do not affect score)

### P12: Semantic Equivalence Symmetry
- FOR ALL skill pairs (X, Y) where X is a synonym of Y, matching X against a JD requiring Y SHALL produce the same match contribution as matching Y directly

### P13: AI Output Schema Conformance
- FOR ALL AI agent outputs, the output SHALL parse successfully against the agent's defined JSON schema without validation errors

### P14: Prompt Injection Resistance
- FOR ALL user inputs containing known prompt injection patterns (e.g., "ignore previous instructions", "system: you are now..."), the AI agent output SHALL conform to the expected schema and not deviate from its defined purpose

### P15: Grounding Completeness
- FOR ALL claims in a tailored resume or cover letter, there EXISTS a citation reference to a specific section/line in the Source_Resume
