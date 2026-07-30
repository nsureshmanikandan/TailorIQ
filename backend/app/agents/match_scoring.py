"""Match scoring agent — computes weighted alignment score between resume and JD.

Implements the weighted scoring formula (40/20/25/15) and uses semantic
matching for keyword equivalence. Does NOT penalize career gaps, job-hopping,
or non-traditional experience.
"""

import json
import logging
from string import Template

from pydantic import BaseModel

from app.agents.base import BaseAgent
from app.schemas.jd_parsed import ParsedJD
from app.schemas.resume_parsed import ParsedResume
from app.schemas.scoring import ScoreOutput
from app.services.llm_service import LLMService
from app.services.prompt_loader import PromptLoader

logger = logging.getLogger(__name__)


class MatchScoringInput(BaseModel):
    """Input schema for the match scoring agent."""

    parsed_resume: ParsedResume
    parsed_jd: ParsedJD
    semantic_map: dict  # Semantic equivalence mapping


class MatchScoringAgent(BaseAgent[MatchScoringInput, ScoreOutput]):
    """Scores resume-to-JD alignment using weighted categories.

    Scoring weights:
    - Technical Skills: 40%
    - Experience Relevance: 20%
    - Domain & Certifications: 25%
    - Achievement Alignment: 15%

    Uses semantic matching to identify keyword equivalences (e.g., ML = Machine Learning).
    Does NOT penalize career gaps, job-hopping, or non-traditional experience paths.
    """

    agent_name = "match_scoring"
    max_output_tokens = 2000
    temperature = 0.2

    def __init__(
        self,
        llm_service: LLMService,
        prompt_loader: PromptLoader,
    ) -> None:
        super().__init__(llm_service=llm_service, prompt_loader=prompt_loader)

    async def execute(self, input_data: MatchScoringInput) -> ScoreOutput:
        """Compute weighted match score between resume and JD.

        Args:
            input_data: Parsed resume, parsed JD, and semantic equivalence map.

        Returns:
            ScoreOutput with overall score, category breakdowns, and gap details.
        """
        templates = self._load_prompt_template()
        system_prompt = templates["system_prompt"]

        # Serialize inputs to JSON for the prompt
        resume_json = input_data.parsed_resume.model_dump_json(indent=2)
        jd_json = input_data.parsed_jd.model_dump_json(indent=2)
        semantic_map_str = json.dumps(input_data.semantic_map, indent=2)

        user_template = Template(templates["user_prompt_template"])
        user_prompt = user_template.safe_substitute(
            resume_json=resume_json,
            jd_json=jd_json,
            semantic_map=semantic_map_str,
        )

        response_schema = ScoreOutput.model_json_schema()

        response = await self._call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            response_schema=response_schema,
        )

        score_output = ScoreOutput.model_validate(response.content)

        # Enforce weighted scoring formula validation
        score_output = self._validate_weighted_score(score_output)

        is_valid = await self.validate_output(score_output)
        if not is_valid:
            logger.warning("Match scoring output failed validation, returning as-is")

        return score_output

    def _validate_weighted_score(self, score: ScoreOutput) -> ScoreOutput:
        """Validate and correct the weighted overall score.

        Only overrides the LLM's overall_score when we have sufficient named
        category coverage (≥3 of the 4 expected categories).  If categories
        are missing or use different names we trust the LLM's own overall_score
        rather than blindly computing 0.
        """
        weights = {
            "technical_skills": 0.40,
            "experience_relevance": 0.20,
            "domain_certifications": 0.25,
            "achievement_alignment": 0.15,
        }

        if not score.category_scores:
            logger.debug("No category_scores — trusting LLM overall_score=%d", score.overall_score)
            return score

        # Only recompute when ≥3 expected category names are present
        found_named = {
            cs.category: cs.score
            for cs in score.category_scores
            if cs.category in weights
        }

        if len(found_named) < 3:
            logger.info(
                "Only %d of 4 expected category names found — trusting LLM overall_score=%d",
                len(found_named),
                score.overall_score,
            )
            return score

        computed_score = sum(
            score_val * weights[cat]
            for cat, score_val in found_named.items()
        )
        expected_overall = max(0, min(100, round(computed_score)))

        # Always use the weighted formula when all 4 categories are present.
        # When only 3 are found, apply a 2-point tolerance.
        if len(found_named) == 4 or abs(expected_overall - score.overall_score) > 2:
            if score.overall_score != expected_overall:
                logger.info(
                    "Correcting overall_score from %d to %d (weighted formula 40/20/25/15)",
                    score.overall_score,
                    expected_overall,
                )
                score.overall_score = expected_overall

        return score
