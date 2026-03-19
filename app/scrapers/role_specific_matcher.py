"""
Role-specific job matching used to filter scraped jobs before storing.

Goal: reduce false positives caused by broad scraper search results.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List


def _normalize_text_for_matching(text: str) -> str:
    if not text:
        return ""
    text = str(text).lower()
    text = re.sub(r"[^a-z0-9\s]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _contains_keyword(text: str, keyword: str) -> bool:
    if not keyword:
        return False
    text_norm = _normalize_text_for_matching(text)
    keyword_norm = _normalize_text_for_matching(keyword)
    if not keyword_norm:
        return False

    # Phrase match
    if " " in keyword_norm:
        return keyword_norm in text_norm

    # Word boundary match for single tokens (e.g. ml, llm, rag)
    return re.search(r"\b" + re.escape(keyword_norm) + r"\b", text_norm) is not None


def _compute_category_evidence(
    text: str,
    strong_keywords: List[str],
    medium_keywords: List[str],
) -> Dict[str, int]:
    strong_hits = sum(1 for k in strong_keywords if _contains_keyword(text, k))
    medium_hits = sum(1 for k in medium_keywords if _contains_keyword(text, k))
    score = strong_hits * 2 + medium_hits
    return {"strong_hits": strong_hits, "medium_hits": medium_hits, "score": score}


_ROLE_CATEGORY_KEYWORDS: Dict[str, Dict[str, List[str]]] = {
    "llm": {
        "strong": [
            "llm",
            "large language model",
            "prompt",
            "prompt engineering",
            "retrieval augmented generation",
            "rag",
            "function calling",
            "langchain",
            "vector embeddings",
            "transformers",
            "agents",
            "agent framework",
        ],
        "medium": [
            "chatbot",
            "vector database",
            "embeddings",
            "semantic search",
            "knowledge base",
        ],
    },
    "genai": {
        "strong": [
            "generative ai",
            "genai",
            "foundation model",
            "diffusion",
            "synthetic data",
            "rag",
            "ai agent",
            "agent",
            "agents",
        ],
        "medium": [
            "llm",
            "model serving",
            "prompt",
        ],
    },
    "nlp": {
        "strong": [
            "nlp",
            "natural language processing",
            "tokenization",
            "named entity recognition",
            "ner",
            "sequence labeling",
            "text classification",
            "sentiment analysis",
            "information extraction",
        ],
        "medium": [
            "transformers",
            "entity extraction",
            "topic modeling",
        ],
    },
    "ml": {
        "strong": [
            "machine learning",
            "model training",
            "feature engineering",
            "neural network",
            "deep learning",
            "pytorch",
            "tensorflow",
            "scikit-learn",
            "xgboost",
            "lightgbm",
            "catboost",
        ],
        "medium": [
            "ml",
            "mlops",
            "prediction",
            "classification",
        ],
    },
    "ds": {
        "strong": [
            "data scientist",
            "statistics",
            "hypothesis",
            "experimentation",
            "forecasting",
            "clustering",
            "causal",
        ],
        "medium": [
            "data analysis",
            "analytics",
            "data analyst",
            "python",
            "sql",
            "etl",
            "data pipeline",
        ],
    },
}


def _classify_target_role(role_name: str) -> str:
    role_norm = _normalize_text_for_matching(role_name)

    # Order: more specific first.
    if any(k in role_norm for k in ["llm", "prompt", "rag"]):
        return "llm"
    if any(k in role_norm for k in ["generative ai", "genai", "foundation model", "diffusion"]):
        return "genai"
    if any(k in role_norm for k in ["nlp", "natural language processing"]):
        return "nlp"
    if any(k in role_norm for k in ["machine learning", " ml ", "ml engineer", "mle"]):
        return "ml"
    if any(k in role_norm for k in ["data scientist", "data analyst", "statistics", "analytics"]):
        return "ds"
    if any(k in role_norm for k in ["ai", "artificial intelligence"]):
        return "ai_general"
    return "ai_general"


def job_matches_role_specific(text: str, target_role: str) -> bool:
    """
    Check if `text` (job title + description) matches the bucket role with evidence.
    """
    if not text:
        return False

    role_type = _classify_target_role(target_role)
    text_norm = _normalize_text_for_matching(text)

    evidence = {
        category: _compute_category_evidence(
            text_norm,
            _ROLE_CATEGORY_KEYWORDS[category]["strong"],
            _ROLE_CATEGORY_KEYWORDS[category]["medium"],
        )
        for category in _ROLE_CATEGORY_KEYWORDS.keys()
    }

    # Thresholds: require at least one strong hit + enough overall evidence.
    THRESH_LLM = 5
    THRESH_GENAI = 5
    THRESH_NLP = 4
    THRESH_ML = 4
    THRESH_DS = 4

    if role_type == "llm":
        e = evidence["llm"]
        return e["strong_hits"] >= 1 and e["score"] >= THRESH_LLM
    if role_type == "genai":
        e = evidence["genai"]
        return e["strong_hits"] >= 1 and e["score"] >= THRESH_GENAI
    if role_type == "nlp":
        e = evidence["nlp"]
        return e["strong_hits"] >= 1 and e["score"] >= THRESH_NLP
    if role_type == "ml":
        e = evidence["ml"]
        return e["strong_hits"] >= 1 and e["score"] >= THRESH_ML
    if role_type == "ds":
        e = evidence["ds"]
        return e["strong_hits"] >= 1 and e["score"] >= THRESH_DS

    # ai_general: accept if it matches any category strongly enough.
    return (
        (evidence["llm"]["strong_hits"] >= 1 and evidence["llm"]["score"] >= THRESH_LLM)
        or (evidence["genai"]["strong_hits"] >= 1 and evidence["genai"]["score"] >= THRESH_GENAI)
        or (evidence["nlp"]["strong_hits"] >= 1 and evidence["nlp"]["score"] >= THRESH_NLP)
        or (evidence["ml"]["strong_hits"] >= 1 and evidence["ml"]["score"] >= THRESH_ML)
        or (evidence["ds"]["strong_hits"] >= 1 and evidence["ds"]["score"] >= THRESH_DS)
    )


def filter_jobs_by_role_specific_matching(jobs_by_role: Dict[str, Any]) -> Dict[str, Any]:
    """
    Filter a scraper's `{role_bucket: [jobs...]}` output before storing.
    """
    if not jobs_by_role or not isinstance(jobs_by_role, dict):
        return jobs_by_role

    filtered: Dict[str, Any] = {}
    for role_name, jobs in jobs_by_role.items():
        if not role_name:
            continue
        if str(role_name).lower() == "general":
            continue
        if not isinstance(jobs, list):
            continue

        kept_jobs: List[Dict[str, Any]] = []
        for job in jobs:
            if not isinstance(job, dict):
                continue
            job_title = job.get("job_title", "") or ""
            description = job.get("description", "") or ""
            text = f"{job_title}\n{description}".strip()
            if job_matches_role_specific(text, str(role_name)):
                kept_jobs.append(job)

        if kept_jobs:
            filtered[str(role_name)] = kept_jobs

    return filtered


def is_data_science_job(text: str) -> bool:
    """
    Classify a job as "Data Science / AI related" vs "Non-Data Science"
    using job content only.
    """
    # Passing an "AI" role forces the matcher into the ai_general bucket,
    # which accepts if any target category (llm/genai/nlp/ml/ds) matches strongly.
    return job_matches_role_specific(text, "AI Engineer")

