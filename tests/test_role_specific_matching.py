import os
import sys

import pytest

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.scrapers.role_specific_matcher import filter_jobs_by_role_specific_matching, is_data_science_job


def test_llm_role_filters_out_non_llm():
    jobs_by_role = {
        "LLM Engineer": [
            {
                "job_id": "1",
                "job_title": "LLM Engineer",
                "description": "Build RAG pipelines with prompt engineering, vector embeddings, and transformers.",
            },
            {
                "job_id": "2",
                "job_title": "Software Engineer",
                "description": "Backend Java API development. No ML/LLM mentioned.",
            },
        ]
    }

    filtered = filter_jobs_by_role_specific_matching(jobs_by_role)
    assert "LLM Engineer" in filtered
    assert len(filtered["LLM Engineer"]) == 1
    assert filtered["LLM Engineer"][0]["job_id"] == "1"


def test_data_scientist_role_filters_out_sales():
    jobs_by_role = {
        "Data Scientist": [
            {
                "job_id": "1",
                "job_title": "Data Scientist",
                "description": "Statistics, experimentation, forecasting, and Python/SQL data analysis.",
            },
            {
                "job_id": "2",
                "job_title": "Account Manager",
                "description": "Sales and customer success responsibilities.",
            },
        ]
    }

    filtered = filter_jobs_by_role_specific_matching(jobs_by_role)
    assert "Data Scientist" in filtered
    assert len(filtered["Data Scientist"]) == 1
    assert filtered["Data Scientist"][0]["job_id"] == "1"


def test_ai_engine_role_allows_llm_evidence_only():
    jobs_by_role = {
        "AI Engineer": [
            {
                "job_id": "1",
                "job_title": "AI Engineer",
                "description": "Work on LLM agents with function calling and retrieval augmented generation (RAG).",
            },
            {
                "job_id": "2",
                "job_title": "AI Talent Recruiter",
                "description": "Recruiting and hiring. No model training or LLM/NLP terms.",
            },
        ]
    }

    filtered = filter_jobs_by_role_specific_matching(jobs_by_role)
    assert "AI Engineer" in filtered
    assert len(filtered["AI Engineer"]) == 1
    assert filtered["AI Engineer"][0]["job_id"] == "1"


def test_is_data_science_job_returns_true_for_llm():
    text = "LLM engineer. Build RAG pipelines with prompt engineering, vector embeddings, and transformers."
    assert is_data_science_job(text) is True


def test_is_data_science_job_returns_false_for_sales():
    text = "Account Manager. Responsible for sales targets and customer success. No ML/LLM mentioned."
    assert is_data_science_job(text) is False

