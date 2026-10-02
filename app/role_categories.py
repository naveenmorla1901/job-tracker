"""
Classify job titles into AI / data categories.

Scrapers tag each job with the search term that found it ("AI Engineer python
SQL"), but company job boards answer searches loosely, so a "Construction
Engineer" can come back tagged "AI Engineer". The title is the only reliable
signal, so the AI & DS page filters on these patterns instead of role tags.
"""
import re
from typing import Dict, List

# Order matters only for display; a title can belong to several categories.
CATEGORY_PATTERNS: Dict[str, List[str]] = {
    "AI / ML": [
        r"machine[\s-]+learning",
        r"\bml\b",
        r"\bai\b",
        r"\ba\.i\.",
        r"artificial\s+intelligence",
        r"deep\s+learning",
        r"\bnlp\b",
        r"natural\s+language",
        r"computer\s+vision",
        r"\bllms?\b",
        r"large\s+language",
        r"gen(erative)?[\s-]?ai",
        r"foundation\s+models?",
        r"\brag\b",
        r"prompt\s+engineer",
        r"\bmlops\b",
        r"reinforcement\s+learning",
        r"neural\s+net",
        r"applied\s+scientist",
        r"ai/ml|ml/ai",
    ],
    "Data Science": [
        r"data\s+scien",
        r"decision\s+scien",
        r"\bstatistician\b",
        r"quantitative\s+(analyst|researcher|scientist)",
        r"\bquant\b",
    ],
    "Data Engineering": [
        r"data\s+engineer",
        r"analytics\s+engineer",
        r"big\s+data",
        r"\betl\b",
        r"data\s+(platform|pipeline|warehouse)",
        r"data\s+architect",
        r"data\s+integration\s+engineer",
    ],
    "Data Analytics": [
        r"data\s+analy",
        r"analytics\s+(analyst|manager|consultant|specialist|lead)",
        r"business\s+intelligence",
        r"\bbi\s+(developer|analyst|engineer)",
        r"reporting\s+analyst",
        r"sql\s+developer",
        r"power\s+bi|tableau",
        r"insights\s+analyst",
    ],
}

# Titles that mention AI/data but are not hands-on technical roles.
EXCLUDE_PATTERNS = [
    r"\bsales\b",
    r"account\s+(executive|manager)",
    r"\brecruit",
    r"talent\s+acquisition",
    r"\bsourcer\b",
]

_CATEGORY_RE = {
    name: re.compile("|".join(patterns), re.IGNORECASE)
    for name, patterns in CATEGORY_PATTERNS.items()
}
_EXCLUDE_RE = re.compile("|".join(EXCLUDE_PATTERNS), re.IGNORECASE)

CATEGORIES = list(CATEGORY_PATTERNS.keys())


def classify_title(title: str) -> List[str]:
    """Return the categories a job title belongs to (empty when none)."""
    if not title or _EXCLUDE_RE.search(title):
        return []
    return [name for name, pattern in _CATEGORY_RE.items() if pattern.search(title)]
