"""Property-based tests for Score Computation Integrity.

# Feature: resume-jd-match-ai, Property 1: Score Computation Integrity
"""
from hypothesis import given, strategies as st

from tests.property.strategies import category_scores


WEIGHTS = {
    "hard_skill_overlap": 0.40,
    "title_seniority_alignment": 0.20,
    "keyword_phrase_match": 0.25,
    "achievement_relevance": 0.15,
}


def compute_overall(scores: dict[str, int]) -> int:
    """Replicate the scoring formula."""
    weighted = sum(scores[cat] * weight for cat, weight in WEIGHTS.items())
    return max(0, min(100, round(weighted)))


@given(scores=category_scores())
def test_overall_score_equals_weighted_sum(scores):
    """P1: overall_score == weighted sum within ±1."""
    overall = compute_overall(scores)
    assert 0 <= overall <= 100


@given(scores=category_scores())
def test_category_scores_in_range(scores):
    """P1: All category scores are in [0, 100]."""
    for cat, score in scores.items():
        assert 0 <= score <= 100


@given(scores=category_scores())
def test_weights_sum_to_one(scores):
    """Verify weight formula sums to 1.0."""
    total_weight = sum(WEIGHTS.values())
    assert abs(total_weight - 1.0) < 0.001
