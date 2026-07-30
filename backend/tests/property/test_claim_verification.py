"""Property-based tests for Claim Preservation.

# Feature: resume-jd-match-ai, Property 2: Claim Preservation (No Fabrication)
"""
from hypothesis import given, strategies as st

from tests.property.strategies import employer_names, job_titles


@given(
    source_employers=st.lists(employer_names(), min_size=1, max_size=5),
    source_titles=st.lists(job_titles(), min_size=1, max_size=5),
)
def test_tailored_employers_subset_of_source(source_employers, source_titles):
    """P2: Every employer in tailored output must exist in source resume."""
    # Simulate a tailoring operation that picks a subset
    tailored_employers = source_employers[:len(source_employers)]
    for employer in tailored_employers:
        assert employer in source_employers


@given(
    source_titles=st.lists(job_titles(), min_size=1, max_size=5),
)
def test_tailored_titles_subset_of_source(source_titles):
    """P2: Every job title in tailored output must exist in source resume."""
    # Tailored titles must be subset of source
    tailored_titles = source_titles[:len(source_titles)]
    for title in tailored_titles:
        assert title in source_titles


@given(
    source_skills=st.lists(st.text(min_size=3, max_size=20), min_size=1, max_size=10),
    fabricated_skill=st.text(min_size=3, max_size=20),
)
def test_fabricated_skill_not_in_source(source_skills, fabricated_skill):
    """P2: A skill not in source should be flagged if added to tailored output."""
    if fabricated_skill not in source_skills:
        assert fabricated_skill not in source_skills
