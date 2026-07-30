"""Hypothesis settings and shared strategies for property-based tests."""
import os

from hypothesis import settings

# Register test profiles
settings.register_profile("ci", max_examples=200, deadline=30000)
settings.register_profile("dev", max_examples=100, deadline=10000)
settings.load_profile(os.getenv("HYPOTHESIS_PROFILE", "dev"))
