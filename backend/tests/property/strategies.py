"""Reusable Hypothesis strategies for domain objects."""
from hypothesis import strategies as st


def category_scores():
    """Generate a list of 4 category scores with correct weights."""
    return st.fixed_dictionaries({
        "hard_skill_overlap": st.integers(min_value=0, max_value=100),
        "title_seniority_alignment": st.integers(min_value=0, max_value=100),
        "keyword_phrase_match": st.integers(min_value=0, max_value=100),
        "achievement_relevance": st.integers(min_value=0, max_value=100),
    })


def email_addresses():
    """Generate realistic email addresses for PII testing."""
    return st.from_regex(r"[a-z]{3,10}@[a-z]{3,8}\.(com|org|net)", fullmatch=True)


def phone_numbers():
    """Generate phone number patterns."""
    return st.from_regex(r"\+?1?[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", fullmatch=True)


def skill_names():
    """Generate plausible skill names."""
    skills = [
        "Python", "JavaScript", "TypeScript", "React", "SQL", "AWS", "Azure",
        "Docker", "Kubernetes", "Machine Learning", "CI/CD", "Git", "Node.js",
        "PostgreSQL", "MongoDB", "Redis", "FastAPI", "Django", "Flask",
        "Java", "C#", ".NET", "Go", "Rust", "TensorFlow", "PyTorch",
    ]
    return st.sampled_from(skills)


def employer_names():
    """Generate plausible employer names."""
    companies = [
        "Acme Corp", "TechStart Inc", "DataFlow Ltd", "CloudScale Systems",
        "InnovateTech", "DigitalFirst", "CodeCraft", "ByteWorks",
    ]
    return st.sampled_from(companies)


def job_titles():
    """Generate plausible job titles."""
    titles = [
        "Software Engineer", "Senior Developer", "Data Scientist",
        "Product Manager", "DevOps Engineer", "ML Engineer",
        "Frontend Developer", "Backend Engineer", "Full Stack Developer",
    ]
    return st.sampled_from(titles)
