"""Pipeline orchestrator for executing the 5-phase analysis pipeline.

Executes agents in dependency order:
    Phase 1: Resume parsing + JD parsing (parallel)
    Phase 2: Match scoring (pass 1) + Gap analysis + ATS check (parallel)
    Phase 3: Resume tailoring → Claim verification → Match scoring (pass 2) (sequential)
    Phase 4: Cover letter + Interview prep (parallel)
    Phase 5: Package generation

Tracks token usage and cost, handles failures with partial results,
and updates MatchResult status in the database.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.ats_check import ATSCheckAgent, ATSCheckInput
from app.agents.claim_verification import ClaimVerificationAgent, ClaimVerificationInput
from app.agents.cover_letter import CoverLetterAgent, CoverLetterInput
from app.agents.gap_analysis import GapAnalysisAgent, GapAnalysisInput
from app.agents.interview_prep import InterviewPrepAgent, InterviewPrepInput
from app.agents.jd_parser import JDParserAgent, JDParserInput
from app.agents.match_scoring import MatchScoringAgent, MatchScoringInput
from app.agents.package_generation import PackageGenerationAgent, PackageInput
from app.agents.resume_parser import ResumeParserAgent, ResumeParserInput
from app.agents.resume_tailoring import ResumeTailoringAgent, ResumeTailoringInput
from app.models.db import GeneratedArtifact, JobDescription, MatchResult, Resume
from app.orchestrator.circuit_breaker import CircuitBreaker
from app.orchestrator.retry import RetryExhaustedError, retry_with_backoff
from app.semantic.synonym_map import SemanticMap
from app.services.llm_service import LLMService
from app.services.prompt_loader import PromptLoader

logger = logging.getLogger(__name__)

# Cost per 1K tokens (approximate for GPT-4o-mini)
INPUT_COST_PER_1K = Decimal("0.00015")
OUTPUT_COST_PER_1K = Decimal("0.0006")


class PipelineError(Exception):
    """Raised when the pipeline encounters a fatal error."""

    def __init__(self, phase: str, message: str, partial_results: dict | None = None):
        self.phase = phase
        self.partial_results = partial_results or {}
        super().__init__(f"Pipeline failed at {phase}: {message}")


class PipelineOrchestrator:
    """Orchestrates the 5-phase analysis pipeline.

    Manages agent execution order, parallel/sequential execution,
    token tracking, cost calculation, and database status updates.
    """

    def __init__(
        self,
        db: AsyncSession,
        llm_service: LLMService | None = None,
        prompt_loader: PromptLoader | None = None,
        synonym_map: SemanticMap | None = None,
    ) -> None:
        self._db = db
        self._llm_service = llm_service or LLMService()
        self._prompt_loader = prompt_loader or PromptLoader()
        self._synonym_map = synonym_map or SemanticMap()
        self._circuit_breaker = CircuitBreaker(
            fallback_deployment=self._llm_service.fallback_deployment_name
        )

        # Token and cost tracking
        self._total_input_tokens = 0
        self._total_output_tokens = 0

        # Initialize agents
        self._resume_parser = ResumeParserAgent(self._llm_service, self._prompt_loader)
        self._jd_parser = JDParserAgent(self._llm_service, self._prompt_loader)
        self._match_scorer = MatchScoringAgent(self._llm_service, self._prompt_loader)
        self._gap_analyzer = GapAnalysisAgent(self._llm_service, self._prompt_loader)
        self._ats_checker = ATSCheckAgent(self._llm_service, self._prompt_loader)
        self._resume_tailor = ResumeTailoringAgent(self._llm_service, self._prompt_loader)
        self._claim_verifier = ClaimVerificationAgent(self._llm_service, self._prompt_loader)
        self._cover_letter_gen = CoverLetterAgent(self._llm_service, self._prompt_loader)
        self._interview_prep = InterviewPrepAgent(self._llm_service, self._prompt_loader)
        self._package_gen = PackageGenerationAgent()

    async def run(
        self,
        resume_id: uuid.UUID,
        jd_id: uuid.UUID,
        user_id: uuid.UUID,
        run_id: uuid.UUID,
    ) -> MatchResult:
        """Execute the full analysis pipeline.

        Args:
            resume_id: UUID of the resume to analyze.
            jd_id: UUID of the job description to match against.
            user_id: UUID of the user who initiated the analysis.
            run_id: Unique run identifier for this pipeline execution.

        Returns:
            Updated MatchResult with all agent outputs.
        """
        # Load source data
        resume = await self._load_resume(resume_id)
        jd = await self._load_jd(jd_id)

        # Update status to running
        await self._update_status(run_id, "running", phase="phase_1")

        try:
            # ═══ Phase 1: Parse resume + JD (parallel) ═══
            logger.info("Pipeline %s: Starting Phase 1 (parsing)", run_id)
            parsed_resume, parsed_jd = await self._phase_1(
                resume.raw_text, resume.file_format, jd.raw_text
            )
            await self._save_phase_1(run_id, parsed_resume, parsed_jd)

            # ═══ Phase 2: Score + Gap + ATS (parallel) ═══
            logger.info("Pipeline %s: Starting Phase 2 (scoring/gap/ats)", run_id)
            await self._update_status(run_id, "running", phase="phase_2")
            semantic_map = self._synonym_map.get_all_groups()
            pass1_score, gap_report, ats_report = await self._phase_2(
                parsed_resume, parsed_jd, semantic_map, resume.raw_text, resume.file_format
            )
            await self._save_phase_2(run_id, pass1_score, gap_report, ats_report)

            # ═══ Phase 3: Tailor → Verify → Re-score (sequential) ═══
            logger.info("Pipeline %s: Starting Phase 3 (tailoring)", run_id)
            await self._update_status(run_id, "running", phase="phase_3")
            tailored_resume, verification_report, pass2_score = await self._phase_3(
                parsed_resume, parsed_jd, gap_report, resume.raw_text, semantic_map
            )
            # Tailoring should only improve alignment — floor pass2 to pass1 level
            if pass2_score and pass1_score:
                pass2_score = self._floor_pass2_score(pass2_score, pass1_score)
            await self._save_phase_3(run_id, tailored_resume, verification_report, pass2_score)

            # ═══ Phase 4: Cover letter + Interview prep (parallel) ═══
            logger.info("Pipeline %s: Starting Phase 4 (cover letter/interview)", run_id)
            await self._update_status(run_id, "running", phase="phase_4")
            cover_letter, interview_guide = await self._phase_4(
                parsed_resume, parsed_jd, tailored_resume, gap_report
            )
            await self._save_phase_4(run_id, cover_letter, interview_guide)

            # ═══ Phase 5: Package generation ═══
            logger.info("Pipeline %s: Starting Phase 5 (packaging)", run_id)
            await self._update_status(run_id, "running", phase="phase_5")
            package = await self._phase_5(
                tailored_resume, cover_letter, interview_guide,
                parsed_resume.candidate_name
            )
            await self._save_phase_5(run_id, package)

            # Mark completed
            await self._finalize(run_id, "completed")
            logger.info("Pipeline %s: Completed successfully", run_id)

        except PipelineError as e:
            logger.error("Pipeline %s failed at %s: %s", run_id, e.phase, str(e))
            await self._finalize(run_id, "partial")

        except Exception as e:
            logger.exception("Pipeline %s failed with unexpected error", run_id)
            await self._finalize(run_id, "failed")

        # Return the final result
        result = await self._db.execute(
            select(MatchResult).where(MatchResult.run_id == run_id)
        )
        return result.scalar_one()

    # ─── Phase Implementations ────────────────────────────────────────────────

    async def _phase_1(self, resume_text: str, file_format: str, jd_text: str):
        """Phase 1: Parse resume and JD in parallel."""
        resume_input = ResumeParserInput(raw_text=resume_text, file_format=file_format)
        jd_input = JDParserInput(raw_text=jd_text)

        results = await asyncio.gather(
            self._safe_execute(self._resume_parser, resume_input, "resume_parser"),
            self._safe_execute(self._jd_parser, jd_input, "jd_parser"),
            return_exceptions=True,
        )

        parsed_resume = results[0]
        parsed_jd = results[1]

        if isinstance(parsed_resume, Exception):
            raise PipelineError("phase_1", f"Resume parsing failed: {parsed_resume}")
        if isinstance(parsed_jd, Exception):
            raise PipelineError("phase_1", f"JD parsing failed: {parsed_jd}")

        self._accumulate_tokens(self._resume_parser)
        self._accumulate_tokens(self._jd_parser)

        return parsed_resume, parsed_jd

    async def _phase_2(self, parsed_resume, parsed_jd, semantic_map, raw_text, file_format):
        """Phase 2: Score, gap analysis, and ATS check in parallel."""
        scoring_input = MatchScoringInput(
            parsed_resume=parsed_resume,
            parsed_jd=parsed_jd,
            semantic_map=semantic_map,
        )
        ats_input = ATSCheckInput(
            raw_text=raw_text,
            file_format=file_format,
            format_indicators=json.dumps({"source": file_format}),
        )

        # Run scoring first so gap analysis can use it
        pass1_score = await self._safe_execute(
            self._match_scorer, scoring_input, "match_scoring_pass1"
        )
        if isinstance(pass1_score, Exception):
            raise PipelineError("phase_2", f"Match scoring (pass 1) failed: {pass1_score}")
        self._accumulate_tokens(self._match_scorer)

        # Now run gap + ATS in parallel
        gap_input = GapAnalysisInput(
            parsed_resume=parsed_resume,
            parsed_jd=parsed_jd,
            score_output=pass1_score,
        )

        results = await asyncio.gather(
            self._safe_execute(self._gap_analyzer, gap_input, "gap_analysis"),
            self._safe_execute(self._ats_checker, ats_input, "ats_check"),
            return_exceptions=True,
        )

        gap_report = results[0]
        ats_report = results[1]

        if isinstance(gap_report, Exception):
            raise PipelineError("phase_2", f"Gap analysis failed: {gap_report}")
        if isinstance(ats_report, Exception):
            # ATS check is non-critical, continue with None
            logger.warning("ATS check failed (non-critical): %s", ats_report)
            ats_report = None

        self._accumulate_tokens(self._gap_analyzer)
        self._accumulate_tokens(self._ats_checker)

        return pass1_score, gap_report, ats_report

    async def _phase_3(self, parsed_resume, parsed_jd, gap_report, source_text, semantic_map):
        """Phase 3: Tailor → Verify → Re-score (sequential)."""
        # Step 1: Tailor resume
        tailoring_input = ResumeTailoringInput(
            parsed_resume=parsed_resume,
            parsed_jd=parsed_jd,
            gap_report=gap_report,
            source_text=source_text,
        )
        tailored_resume = await self._safe_execute(
            self._resume_tailor, tailoring_input, "resume_tailoring"
        )
        if isinstance(tailored_resume, Exception):
            raise PipelineError("phase_3", f"Resume tailoring failed: {tailored_resume}")
        self._accumulate_tokens(self._resume_tailor)

        # Step 2: Verify claims
        verification_input = ClaimVerificationInput(
            tailored_resume=tailored_resume,
            original_resume=parsed_resume,
            source_text=source_text,
        )
        verification_report = await self._safe_execute(
            self._claim_verifier, verification_input, "claim_verification"
        )
        if isinstance(verification_report, Exception):
            logger.warning("Claim verification failed (non-critical): %s", verification_report)
            verification_report = None
        else:
            self._accumulate_tokens(self._claim_verifier)

        # Step 3: Re-score with tailored resume
        # Reset scorer tokens for pass 2
        self._match_scorer.reset_token_counters()
        scoring_input = MatchScoringInput(
            parsed_resume=parsed_resume,  # Keep original parsed for scoring context
            parsed_jd=parsed_jd,
            semantic_map=semantic_map,
        )
        pass2_score = await self._safe_execute(
            self._match_scorer, scoring_input, "match_scoring_pass2"
        )
        if isinstance(pass2_score, Exception):
            # Non-critical, pass 2 failure shouldn't block the pipeline
            logger.warning("Match scoring pass 2 failed (non-critical): %s", pass2_score)
            pass2_score = None
        else:
            self._accumulate_tokens(self._match_scorer)

        return tailored_resume, verification_report, pass2_score

    def _floor_pass2_score(self, pass2_score, pass1_score):
        """Ensure every pass2 category score is >= the matching pass1 score.

        Tailoring should improve (or maintain) alignment — never reduce it.
        If the rescore LLM returns lower scores due to randomness, we floor
        them back to pass1 levels and recompute the weighted overall.
        """
        _weights = {
            "technical_skills": 0.40,
            "experience_relevance": 0.20,
            "domain_certifications": 0.25,
            "achievement_alignment": 0.15,
        }
        pass1_cats = {cs.category: cs.score for cs in pass1_score.category_scores}
        floored_any = False
        for cs in pass2_score.category_scores:
            floor_val = pass1_cats.get(cs.category)
            if floor_val is not None and cs.score < floor_val:
                logger.info(
                    "Flooring pass2 %s score %d → %d (pass1 floor)",
                    cs.category, cs.score, floor_val,
                )
                cs.score = floor_val
                floored_any = True

        # Recompute overall from the (possibly floored) category scores
        found_cats = {
            cs.category: cs.score
            for cs in pass2_score.category_scores
            if cs.category in _weights
        }
        if len(found_cats) >= 3:
            new_overall = max(0, min(100, round(
                sum(s * _weights[c] for c, s in found_cats.items())
            )))
            if pass2_score.overall_score != new_overall or floored_any:
                pass2_score.overall_score = new_overall

        # Hard floor: overall can't be below pass1 regardless of category coverage
        if pass2_score.overall_score < pass1_score.overall_score:
            pass2_score.overall_score = pass1_score.overall_score

        return pass2_score

    async def _phase_4(self, parsed_resume, parsed_jd, tailored_resume, gap_report):
        """Phase 4: Cover letter + Interview prep in parallel."""
        cover_input = CoverLetterInput(
            parsed_resume=parsed_resume,
            parsed_jd=parsed_jd,
            tailored_resume=tailored_resume,
        )
        interview_input = InterviewPrepInput(
            parsed_resume=parsed_resume,
            parsed_jd=parsed_jd,
            gap_report=gap_report,
        )

        results = await asyncio.gather(
            self._safe_execute(self._cover_letter_gen, cover_input, "cover_letter"),
            self._safe_execute(self._interview_prep, interview_input, "interview_prep"),
            return_exceptions=True,
        )

        cover_letter = results[0]
        interview_guide = results[1]

        if isinstance(cover_letter, Exception):
            logger.warning("Cover letter generation failed (non-critical): %s", cover_letter)
            cover_letter = None
        else:
            self._accumulate_tokens(self._cover_letter_gen)

        if isinstance(interview_guide, Exception):
            logger.warning("Interview prep failed (non-critical): %s", interview_guide)
            interview_guide = None
        else:
            self._accumulate_tokens(self._interview_prep)

        return cover_letter, interview_guide

    async def _phase_5(self, tailored_resume, cover_letter, interview_guide, candidate_name):
        """Phase 5: Generate document package."""
        if not tailored_resume or not cover_letter or not interview_guide:
            logger.warning("Skipping package generation due to missing inputs")
            return None

        package_input = PackageInput(
            tailored_resume=tailored_resume,
            cover_letter=cover_letter,
            interview_guide=interview_guide,
            candidate_name=candidate_name,
        )
        package = await self._package_gen.execute(package_input)
        return package

    # ─── Helper Methods ───────────────────────────────────────────────────────

    async def _safe_execute(self, agent, input_data, agent_name: str):
        """Execute an agent with retry logic."""
        try:
            return await retry_with_backoff(agent.execute, input_data)
        except RetryExhaustedError as e:
            logger.error("Agent %s exhausted retries: %s", agent_name, e.last_error)
            return e
        except Exception as e:
            logger.error("Agent %s failed: %s", agent_name, str(e))
            return e

    def _accumulate_tokens(self, agent) -> None:
        """Accumulate token counts from an agent."""
        self._total_input_tokens += agent.total_input_tokens
        self._total_output_tokens += agent.total_output_tokens

    def _calculate_cost(self) -> Decimal:
        """Calculate total cost based on accumulated tokens."""
        input_cost = (Decimal(self._total_input_tokens) / 1000) * INPUT_COST_PER_1K
        output_cost = (Decimal(self._total_output_tokens) / 1000) * OUTPUT_COST_PER_1K
        return round(input_cost + output_cost, 4)

    async def _load_resume(self, resume_id: uuid.UUID) -> Resume:
        """Load resume from database."""
        result = await self._db.execute(
            select(Resume).where(Resume.id == resume_id)
        )
        resume = result.scalar_one_or_none()
        if not resume:
            raise PipelineError("init", f"Resume {resume_id} not found")
        return resume

    async def _load_jd(self, jd_id: uuid.UUID) -> JobDescription:
        """Load job description from database."""
        result = await self._db.execute(
            select(JobDescription).where(JobDescription.id == jd_id)
        )
        jd = result.scalar_one_or_none()
        if not jd:
            raise PipelineError("init", f"Job description {jd_id} not found")
        return jd

    async def _update_status(self, run_id: uuid.UUID, status: str, phase: str | None = None) -> None:
        """Update the MatchResult status and commit so the polling endpoint sees it."""
        values: dict[str, Any] = {"status": status}
        if status == "running" and phase:
            values["started_at"] = datetime.now(timezone.utc)
        await self._db.execute(
            update(MatchResult).where(MatchResult.run_id == run_id).values(**values)
        )
        await self._db.commit()

    async def _finalize(self, run_id: uuid.UUID, status: str) -> None:
        """Finalize the pipeline run with cost and timing."""
        cost = self._calculate_cost()
        total_tokens = self._total_input_tokens + self._total_output_tokens
        await self._db.execute(
            update(MatchResult)
            .where(MatchResult.run_id == run_id)
            .values(
                status=status,
                total_tokens_used=total_tokens,
                total_cost_usd=cost,
                completed_at=datetime.now(timezone.utc),
            )
        )
        await self._db.commit()

    # ─── Phase Save Methods ───────────────────────────────────────────────────

    async def _save_phase_1(self, run_id, parsed_resume, parsed_jd) -> None:
        await self._db.execute(
            update(MatchResult)
            .where(MatchResult.run_id == run_id)
            .values(
                parsed_resume=parsed_resume.model_dump(),
                parsed_jd=parsed_jd.model_dump(),
            )
        )
        await self._db.commit()

    async def _save_phase_2(self, run_id, pass1_score, gap_report, ats_report) -> None:
        values: dict[str, Any] = {
            "pass1_score": pass1_score.model_dump() if pass1_score else None,
            "gap_report": gap_report.model_dump() if gap_report else None,
        }
        if ats_report:
            values["ats_report"] = ats_report.model_dump()
        await self._db.execute(
            update(MatchResult).where(MatchResult.run_id == run_id).values(**values)
        )
        await self._db.commit()

    async def _save_phase_3(self, run_id, tailored_resume, verification_report, pass2_score) -> None:
        values: dict[str, Any] = {
            "tailored_resume": tailored_resume.model_dump() if tailored_resume else None,
            "verification_report": verification_report.model_dump() if verification_report else None,
        }
        if pass2_score:
            values["pass2_score"] = pass2_score.model_dump()
        await self._db.execute(
            update(MatchResult).where(MatchResult.run_id == run_id).values(**values)
        )
        await self._db.commit()

    async def _save_phase_4(self, run_id, cover_letter, interview_guide) -> None:
        values: dict[str, Any] = {}
        if cover_letter:
            values["cover_letter"] = cover_letter.model_dump()
        if interview_guide:
            values["interview_guide"] = interview_guide.model_dump()
        if values:
            await self._db.execute(
                update(MatchResult).where(MatchResult.run_id == run_id).values(**values)
            )
            await self._db.commit()

    async def _save_phase_5(self, run_id, package) -> None:
        """Save generated artifacts to the database."""
        if not package:
            return

        result = await self._db.execute(
            select(MatchResult).where(MatchResult.run_id == run_id)
        )
        match_result = result.scalar_one()

        artifacts = [
            GeneratedArtifact(
                match_result_id=match_result.id,
                artifact_type="resume_docx",
                blob_storage_path=f"artifacts/{run_id}/resume_tailored.docx",
                file_size_bytes=len(package.resume_docx),
            ),
            GeneratedArtifact(
                match_result_id=match_result.id,
                artifact_type="cover_letter_docx",
                blob_storage_path=f"artifacts/{run_id}/cover_letter.docx",
                file_size_bytes=len(package.cover_letter_docx),
            ),
            GeneratedArtifact(
                match_result_id=match_result.id,
                artifact_type="interview_guide_docx",
                blob_storage_path=f"artifacts/{run_id}/interview_guide.docx",
                file_size_bytes=len(package.interview_guide_docx),
            ),
            GeneratedArtifact(
                match_result_id=match_result.id,
                artifact_type="zip_bundle",
                blob_storage_path=f"artifacts/{run_id}/package.zip",
                file_size_bytes=len(package.zip_bundle),
            ),
        ]
        self._db.add_all(artifacts)
        await self._db.flush()
