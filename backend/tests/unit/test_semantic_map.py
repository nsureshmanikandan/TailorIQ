"""Unit tests for the SemanticMap class."""

import pytest

from app.semantic.synonym_map import SemanticMap, SemanticMapLoadError


@pytest.fixture
def semantic_map():
    """Create a SemanticMap instance with the default mappings."""
    return SemanticMap()


class TestAreEquivalent:
    """Tests for SemanticMap.are_equivalent."""

    def test_same_term(self, semantic_map: SemanticMap):
        """Identical terms are equivalent."""
        assert semantic_map.are_equivalent("Python", "Python") is True

    def test_abbreviation_to_full(self, semantic_map: SemanticMap):
        """Abbreviation and full name are equivalent."""
        assert semantic_map.are_equivalent("ML", "Machine Learning") is True

    def test_case_insensitive(self, semantic_map: SemanticMap):
        """Matching is case-insensitive."""
        assert semantic_map.are_equivalent("aws", "Amazon Web Services") is True

    def test_kubernetes_alias(self, semantic_map: SemanticMap):
        """K8s and Kubernetes are equivalent."""
        assert semantic_map.are_equivalent("K8s", "Kubernetes") is True

    def test_title_synonyms(self, semantic_map: SemanticMap):
        """Job title variations are equivalent."""
        assert semantic_map.are_equivalent("Software Engineer", "SDE") is True
        assert semantic_map.are_equivalent("Software Developer", "Programmer") is True

    def test_certification_synonyms(self, semantic_map: SemanticMap):
        """Certification abbreviations are equivalent."""
        assert semantic_map.are_equivalent("PMP", "Project Management Professional") is True
        assert semantic_map.are_equivalent("AWS SAA", "AWS Solutions Architect Associate") is True

    def test_non_equivalent_terms(self, semantic_map: SemanticMap):
        """Terms from different groups are not equivalent."""
        assert semantic_map.are_equivalent("Python", "JavaScript") is False

    def test_unknown_term(self, semantic_map: SemanticMap):
        """Unknown terms are not equivalent to anything."""
        assert semantic_map.are_equivalent("UnknownSkill", "Python") is False

    def test_ci_cd_equivalence(self, semantic_map: SemanticMap):
        """CI/CD and Continuous Integration are equivalent."""
        assert semantic_map.are_equivalent("CI/CD", "Continuous Integration") is True


class TestExpandTerm:
    """Tests for SemanticMap.expand_term."""

    def test_known_term(self, semantic_map: SemanticMap):
        """Expanding a known term returns all synonyms."""
        terms = semantic_map.expand_term("ML")
        assert "ML" in terms
        assert "Machine Learning" in terms

    def test_unknown_term(self, semantic_map: SemanticMap):
        """Expanding an unknown term returns just the term."""
        terms = semantic_map.expand_term("UnknownSkill123")
        assert terms == ["UnknownSkill123"]

    def test_kubernetes_expansion(self, semantic_map: SemanticMap):
        """Expanding K8s returns all Kubernetes synonyms."""
        terms = semantic_map.expand_term("K8s")
        assert "Kubernetes" in terms
        assert "K8s" in terms
        assert "k8s" in terms


class TestGetCanonicalGroup:
    """Tests for SemanticMap.get_canonical_group."""

    def test_known_term(self, semantic_map: SemanticMap):
        """Returns group_id for known terms."""
        assert semantic_map.get_canonical_group("ML") == "machine_learning"
        assert semantic_map.get_canonical_group("AWS") == "amazon_web_services"

    def test_unknown_term(self, semantic_map: SemanticMap):
        """Returns None for unknown terms."""
        assert semantic_map.get_canonical_group("UnknownSkill") is None

    def test_case_insensitive(self, semantic_map: SemanticMap):
        """Group lookup is case-insensitive."""
        assert semantic_map.get_canonical_group("kubernetes") == "kubernetes"
        assert semantic_map.get_canonical_group("KUBERNETES") == "kubernetes"


class TestGetCanonicalName:
    """Tests for SemanticMap.get_canonical_name."""

    def test_returns_canonical(self, semantic_map: SemanticMap):
        """Returns canonical name for a mapped term."""
        assert semantic_map.get_canonical_name("ML") == "Machine Learning"
        assert semantic_map.get_canonical_name("K8s") == "Kubernetes"

    def test_unknown_returns_none(self, semantic_map: SemanticMap):
        """Unknown terms return None."""
        assert semantic_map.get_canonical_name("FakeSkill") is None


class TestSemanticMapLoading:
    """Tests for mapping file loading."""

    def test_loads_successfully(self, semantic_map: SemanticMap):
        """Default mappings load without errors."""
        assert semantic_map.group_count > 0
        assert semantic_map.term_count > 0

    def test_invalid_path_raises(self):
        """Loading from nonexistent file raises error."""
        with pytest.raises(SemanticMapLoadError):
            SemanticMap(mappings_path="/nonexistent/path.yaml")
