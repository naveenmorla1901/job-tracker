"""Tests for the profile-based job matcher."""
from app.matching import JobMatcher, get_matcher, load_profile, score_job


def _matcher():
    return JobMatcher(
        {
            "target_titles": ["data scientist", "machine learning engineer"],
            "title_keywords": ["data", "machine learning", "analytics"],
            "exclude_titles": ["manager", "director", "sales", "intern", "internship"],
            "exclude_keywords": ["no sponsorship", "security clearance", "itar"],
            "skills": [
                {"name": "python", "weight": 3, "aliases": ["py"]},
                {"name": "sql", "weight": 3, "aliases": ["postgresql"]},
                {"name": "llm", "weight": 3, "aliases": ["rag", "langchain"]},
                {"name": "aws", "weight": 2, "aliases": ["sagemaker"]},
            ],
            "preferred_locations": ["columbus, oh", "remote", "united states"],
            "remote_ok": True,
            "max_years_experience": 5,
            "min_score": 55,
        }
    )


def test_target_title_and_skills_score_high():
    result = _matcher().score(
        "Senior Data Scientist",
        "Build Python and SQL models, RAG pipelines, and deploy on AWS SageMaker.",
        "Remote - United States",
    )

    assert not result.excluded
    assert result.score >= 80
    assert result.title_score == 40
    assert result.skill_score > 0
    assert "python" in result.matched_skills
    assert result.is_us is True


def test_excluded_title_is_zero():
    result = _matcher().score(
        "Director of Data Science", "Python SQL", "Columbus, OH"
    )

    assert result.excluded is True
    assert result.score == 0
    assert "director" in result.exclusion_reason


def test_sponsorship_restriction_is_excluded():
    result = _matcher().score(
        "Data Scientist",
        "Python SQL role. Unfortunately we cannot sponsor. No sponsorship available.",
        "Remote",
    )

    assert result.excluded is True
    assert result.score == 0


def test_exclude_keywords_use_word_boundaries():
    humanitarian = _matcher().score(
        "Data Scientist", "Work on humanitarian data products.", "Remote"
    )
    itar = _matcher().score(
        "Data Scientist", "This role is subject to ITAR export rules.", "Remote"
    )

    assert humanitarian.excluded is False
    assert itar.excluded is True
    assert "itar" in itar.exclusion_reason


def test_non_us_location_is_flagged_and_scores_lower():
    us = _matcher().score("Data Scientist", "Python SQL", "Columbus, OH")
    non_us = _matcher().score("Data Scientist", "Python SQL", "Paris, France")

    assert non_us.is_us is False
    assert non_us.location_score < us.location_score
    assert non_us.score < us.score


def test_remote_with_a_non_us_country_is_not_us():
    result = _matcher().score("Data Scientist", "Python SQL", "Remote - India")

    assert result.is_us is False
    assert result.location_score == 0


def test_multi_location_with_a_us_city_stays_us():
    result = _matcher().score(
        "Data Scientist", "Python SQL", "San Francisco, CA; Toronto, Canada"
    )

    assert result.is_us is True
    assert result.location_score > 0


def test_internship_titles_are_excluded():
    assert _matcher().score("Data Science Intern", "Python", "Remote").excluded
    assert _matcher().score("Data Science Internship", "Python", "Remote").excluded
    # Word boundaries must not reject ordinary "internal" titles.
    assert not _matcher().score("Internal Data Scientist", "Python", "Remote").excluded


def test_excess_experience_reduces_score():
    junior = _matcher().score(
        "Data Scientist", "Python SQL. 3+ years of experience.", "Remote"
    )
    senior = _matcher().score(
        "Data Scientist", "Python SQL. 12+ years of experience.", "Remote"
    )

    assert junior.required_years == 3
    assert senior.required_years == 12
    assert senior.score < junior.score
    assert senior.seniority_score == 0


def test_title_without_target_phrase_still_gets_keyword_credit():
    result = _matcher().score("Data Analytics Specialist", "Python SQL", "Remote")

    assert result.title_score == 20
    assert result.score >= 55


def test_shipped_profile_loads_and_scores_a_real_shape():
    profile = load_profile()
    assert "data scientist" in profile["target_titles"]

    matcher = get_matcher()
    result = matcher.score(
        "Machine Learning Engineer, Generative AI",
        "Python, SQL, LLM, RAG, LangChain, AWS and Kubernetes.",
        "Remote",
    )
    assert result.score >= 80
    assert matcher.is_match(result)

    payload = score_job(
        {
            "job_title": "Machine Learning Engineer",
            "description": "Python SQL LLM",
            "location": "Remote",
        },
        matcher,
    )
    assert payload["score"] >= 55
    assert payload["excluded"] is False
