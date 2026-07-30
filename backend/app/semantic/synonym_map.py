"""Semantic synonym map for skill, title, and certification equivalence.

Loads mapping groups from a YAML configuration file and provides lookup
methods for checking if two terms are equivalent, expanding a term to all
its synonyms, and finding the canonical group for a given term.
"""

import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

_DEFAULT_MAPPINGS_PATH = Path(__file__).parent / "mappings.yaml"


class SemanticMapLoadError(Exception):
    """Raised when the semantic mappings file cannot be loaded."""


class SemanticMap:
    """Semantic synonym mapping for equivalence checking.

    Provides fast lookup for determining if two terms (skills, titles,
    certifications) are semantically equivalent based on configured
    synonym groups.

    Example:
        sem_map = SemanticMap()
        sem_map.are_equivalent("ML", "Machine Learning")  # True
        sem_map.expand_term("K8s")  # ["K8s", "Kubernetes", "k8s"]
        sem_map.get_canonical_group("AWS SAA")  # "aws_saa"
    """

    def __init__(self, mappings_path: Path | str | None = None) -> None:
        """Initialize the semantic map by loading the YAML mappings file.

        Args:
            mappings_path: Path to the YAML mappings file.
                Defaults to the bundled mappings.yaml.

        Raises:
            SemanticMapLoadError: If the file cannot be loaded or parsed.
        """
        self._mappings_path = Path(mappings_path) if mappings_path else _DEFAULT_MAPPINGS_PATH
        self._groups: dict[str, list[str]] = {}  # group_id -> list of terms
        self._canonical: dict[str, str] = {}  # group_id -> canonical term
        self._term_to_group: dict[str, str] = {}  # normalized term -> group_id

        self._load_mappings()

    def _load_mappings(self) -> None:
        """Load and index all synonym groups from the YAML file."""
        if not self._mappings_path.exists():
            raise SemanticMapLoadError(
                f"Mappings file not found: {self._mappings_path}"
            )

        try:
            with open(self._mappings_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise SemanticMapLoadError(
                f"Failed to parse mappings YAML: {e}"
            ) from e

        if not isinstance(data, dict):
            raise SemanticMapLoadError(
                "Mappings file must contain a YAML mapping at the top level."
            )

        # Process all mapping categories
        for category in ("skill_synonyms", "title_synonyms", "certification_mappings"):
            groups = data.get(category, [])
            if not isinstance(groups, list):
                continue

            for group in groups:
                group_id = group.get("group_id")
                canonical = group.get("canonical", "")
                terms = group.get("terms", [])

                if not group_id or not terms:
                    continue

                self._groups[group_id] = terms
                self._canonical[group_id] = canonical

                for term in terms:
                    normalized = self._normalize(term)
                    self._term_to_group[normalized] = group_id

        logger.info(
            "Loaded semantic mappings: %d groups, %d total terms",
            len(self._groups),
            len(self._term_to_group),
        )

    @staticmethod
    def _normalize(term: str) -> str:
        """Normalize a term for case-insensitive lookup.

        Strips whitespace and converts to lowercase for matching.

        Args:
            term: The term to normalize.

        Returns:
            Normalized string.
        """
        return term.strip().lower()

    def are_equivalent(self, term_a: str, term_b: str) -> bool:
        """Check if two terms are semantically equivalent.

        Two terms are equivalent if they belong to the same synonym group.

        Args:
            term_a: First term to compare.
            term_b: Second term to compare.

        Returns:
            True if both terms belong to the same synonym group.
        """
        norm_a = self._normalize(term_a)
        norm_b = self._normalize(term_b)

        # Exact match after normalization
        if norm_a == norm_b:
            return True

        group_a = self._term_to_group.get(norm_a)
        group_b = self._term_to_group.get(norm_b)

        if group_a is None or group_b is None:
            return False

        return group_a == group_b

    def expand_term(self, term: str) -> list[str]:
        """Get all equivalent terms for the given term.

        Args:
            term: The term to expand.

        Returns:
            List of all equivalent terms (including the input term).
            Returns a single-element list with the input term if no group is found.
        """
        norm = self._normalize(term)
        group_id = self._term_to_group.get(norm)

        if group_id is None:
            return [term]

        return list(self._groups[group_id])

    def get_canonical_group(self, term: str) -> str | None:
        """Get the group ID for a given term.

        Args:
            term: The term to look up.

        Returns:
            The group_id string if found, or None if the term is not mapped.
        """
        norm = self._normalize(term)
        return self._term_to_group.get(norm)

    def get_canonical_name(self, term: str) -> str | None:
        """Get the canonical (display) name for a term's group.

        Args:
            term: The term to look up.

        Returns:
            The canonical name for the group, or None if not found.
        """
        group_id = self.get_canonical_group(term)
        if group_id is None:
            return None
        return self._canonical.get(group_id)

    def get_all_groups(self) -> dict[str, list[str]]:
        """Get all synonym groups.

        Returns:
            Dictionary mapping group_id to list of terms.
        """
        return dict(self._groups)

    @property
    def group_count(self) -> int:
        """Total number of synonym groups loaded."""
        return len(self._groups)

    @property
    def term_count(self) -> int:
        """Total number of indexed terms across all groups."""
        return len(self._term_to_group)
