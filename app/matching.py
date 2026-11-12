"""Personal job matching.

The tracker scrapes broadly, but the user only cares about a narrow set of
roles. This module turns ``config/profile.yaml`` into a deterministic 0-100
score so the API and dashboard can rank and filter postings without an LLM.

Scoring is intentionally explainable:

* 40 points for the title (exact target phrase, or partial keyword credit)
* 40 points for weighted skills found in the description
* 15 points for location (Columbus / remote / US)
* 5 points for seniority fit
* a penalty when a posting asks for materially more experience than the profile

Hard exclusions (director/manager/sales titles, sponsorship restrictions, ...)
always win and return score 0.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import yaml

DEFAULT_PROFILE_PATH = Path(__file__).resolve().parent.parent / "config" / "profile.yaml"

_US_STATES = {
    "al", "ak", "az", "ar", "ca", "co", "ct", "de", "fl", "ga", "hi", "id",
    "il", "in", "ia", "ks", "ky", "la", "me", "md", "ma", "mi", "mn", "ms",
    "mo", "mt", "ne", "nv", "nh", "nj", "nm", "ny", "nc", "nd", "oh", "ok",
    "or", "pa", "ri", "sc", "sd", "tn", "tx", "ut", "vt", "va", "wa", "wv",
    "wi", "wy", "dc",
}
_US_STATE_NAMES = {
    "alabama", "alaska", "arizona", "arkansas", "california", "colorado",
    "connecticut", "delaware", "florida", "georgia", "hawaii", "idaho",
    "illinois", "indiana", "iowa", "kansas", "kentucky", "louisiana", "maine",
    "maryland", "massachusetts", "michigan", "minnesota", "mississippi",
    "missouri", "montana", "nebraska", "nevada", "new hampshire", "new jersey",
    "new mexico", "new york", "north carolina", "north dakota", "ohio",
    "oklahoma", "oregon", "pennsylvania", "rhode island", "south carolina",
    "south dakota", "tennessee", "texas", "utah", "vermont", "virginia",
    "washington", "west virginia", "wisconsin", "wyoming",
}
_NON_US_COUNTRIES = {
    "canada", "mexico", "brazil", "argentina", "chile", "colombia", "peru",
    "united kingdom", "uk", "england", "scotland", "wales", "ireland",
    "germany", "france", "spain", "portugal", "italy", "netherlands", "belgium",
    "switzerland", "austria", "sweden", "norway", "denmark", "finland",
    "poland", "czech republic", "czechia", "hungary", "romania", "greece",
    "turkey", "israel", "united arab emirates", "uae", "dubai", "saudi arabia",
    "qatar", "india", "pakistan", "bangladesh", "singapore", "malaysia",
    "indonesia", "philippines", "vietnam", "thailand", "japan", "south korea",
    "korea", "china", "hong kong", "taiwan", "australia", "new zealand",
    "south africa", "nigeria", "kenya", "egypt", "morocco", "russia",
    "ukraine", "armenia", "georgia country",
    # Regions used in place of a country name on global boards.
    "emea", "apac", "latam", "europe", "european union", "asia",
    "middle east", "africa", "south america",
}

_EXPERIENCE_PATTERNS = (
    re.compile(
        r"(\d{1,2})\s*\+?\s*(?:years?|yrs?)\s+(?:of\s+)?"
        r"(?:relevant\s+|professional\s+|industry\s+|hands[-\s]?on\s+)?experience",
        re.I,
    ),
    re.compile(
        r"experience\s+(?:of\s+)?(?:at\s+least\s+)?(\d{1,2})\s*\+?\s*(?:years?|yrs?)",
        re.I,
    ),
    re.compile(
        r"minimum\s+(?:of\s+)?(\d{1,2})\s*\+?\s*(?:years?|yrs?)",
        re.I,
    ),
)


def _phrase_pattern(phrase: str) -> re.Pattern:
    """Word-boundary pattern that treats spaces/hyphens as interchangeable."""
    parts = [
        re.escape(part)
        for part in re.split(r"[\s\-]+", phrase.strip().lower())
        if part
    ]
    escaped = r"[\s\-]+".join(parts)
    return re.compile(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])", re.I)


def _matches(patterns: Sequence[re.Pattern], text: str) -> bool:
    return any(pattern.search(text) for pattern in patterns)


@dataclass(frozen=True)
class MatchResult:
    score: int
    title_score: int
    skill_score: int
    location_score: int
    seniority_score: int
    matched_skills: Tuple[str, ...] = ()
    reasons: Tuple[str, ...] = ()
    excluded: bool = False
    exclusion_reason: Optional[str] = None
    is_us: bool = False
    required_years: Optional[int] = None

    def as_dict(self) -> Dict[str, Any]:
        return {
            "score": self.score,
            "title_score": self.title_score,
            "skill_score": self.skill_score,
            "location_score": self.location_score,
            "seniority_score": self.seniority_score,
            "matched_skills": list(self.matched_skills),
            "match_reasons": list(self.reasons),
            "excluded": self.excluded,
            "exclusion_reason": self.exclusion_reason,
            "is_us": self.is_us,
            "required_years": self.required_years,
        }


class JobMatcher:
    """Score jobs against a profile dictionary (see config/profile.yaml)."""

    def __init__(self, profile: Dict[str, Any]):
        self.profile = profile or {}
        self.target_titles = [
            str(title).strip().lower()
            for title in self.profile.get("target_titles", [])
            if str(title).strip()
        ]
        self.title_keywords = [
            str(word).strip().lower()
            for word in self.profile.get("title_keywords", [])
            if str(word).strip()
        ]
        self.exclude_titles = [
            str(word).strip().lower()
            for word in self.profile.get("exclude_titles", [])
            if str(word).strip()
        ]
        self.exclude_keywords = [
            str(word).strip().lower()
            for word in self.profile.get("exclude_keywords", [])
            if str(word).strip()
        ]
        self.preferred_locations = [
            str(loc).strip().lower()
            for loc in self.profile.get("preferred_locations", [])
            if str(loc).strip()
        ]
        self.remote_ok = bool(self.profile.get("remote_ok", True))
        self.max_years = int(self.profile.get("max_years_experience", 5) or 5)
        self.min_score = int(self.profile.get("min_score", 55) or 55)

        self._target_patterns = [_phrase_pattern(t) for t in self.target_titles]
        self._keyword_patterns = [_phrase_pattern(k) for k in self.title_keywords]
        self._exclude_title_patterns = [
            _phrase_pattern(t) for t in self.exclude_titles
        ]
        self._exclude_keyword_patterns = [
            _phrase_pattern(k) for k in self.exclude_keywords
        ]
        self._skills = []
        for skill in self.profile.get("skills", []) or []:
            name = str(skill.get("name", "")).strip()
            if not name:
                continue
            aliases = [str(a) for a in skill.get("aliases", []) if str(a).strip()]
            patterns = [_phrase_pattern(a) for a in [name, *aliases]]
            self._skills.append(
                (name, int(skill.get("weight", 1) or 1), patterns)
            )
        # A posting does not need to mention every skill in the profile. Reward
        # the first ~15 points of matched weight, which is roughly the core
        # stack (Python + SQL + ML/LLM + one cloud), then cap the component.
        self._skill_target_weight = min(
            15, sum(weight for _, weight, _ in self._skills) or 1
        )

    # -- title -----------------------------------------------------------
    def _title_score(self, title: str) -> Tuple[int, List[str]]:
        if not title:
            return 0, []
        lowered = title.lower()
        reasons: List[str] = []

        for phrase, pattern in zip(self.target_titles, self._target_patterns):
            if pattern.search(lowered):
                reasons.append(f"title matches “{phrase}”")
                return 40, reasons

        hits = [
            keyword
            for keyword, pattern in zip(self.title_keywords, self._keyword_patterns)
            if pattern.search(lowered)
        ]
        if hits:
            score = min(30, 10 * len(hits))
            reasons.append("title keywords: " + ", ".join(hits[:4]))
            return score, reasons
        return 0, []

    # -- skills ----------------------------------------------------------
    def _skill_score(self, text: str) -> Tuple[int, List[str], List[str]]:
        if not text:
            return 0, [], []
        matched: List[Tuple[int, str]] = []
        for name, weight, patterns in self._skills:
            if _matches(patterns, text):
                matched.append((weight, name))
        if not matched:
            return 0, [], []
        earned = sum(weight for weight, _ in matched)
        score = round(40 * earned / self._skill_target_weight)
        matched.sort(key=lambda item: (-item[0], item[1]))
        names = [name for _, name in matched]
        return min(40, score), names[:8], names

    # -- location --------------------------------------------------------
    def _location(self, location: str) -> Tuple[int, bool, List[str]]:
        text = (location or "").strip().lower()
        if not text or text in {"n/a", "unknown"}:
            return 6, True, []

        non_us = self._is_explicit_non_us(text)
        us_signal = self._is_us(text)

        # "Remote - India" and "Paris, France" must not earn remote/US credit.
        # A posting that lists both a US and a non-US location is treated as US
        # (for example "San Francisco, CA; Toronto, Canada").
        if non_us and not us_signal:
            return 0, False, [f"location outside the US: {location}"]

        if any(pref and pref in text for pref in self.preferred_locations):
            return 15, True, [f"preferred location: {location}"]

        if self.remote_ok and re.search(r"\bremote\b", text):
            return 15, True, ["remote role"]

        if us_signal:
            return 12, True, [f"US location: {location}"]

        # "3 Locations", "Multiple Locations", etc. cannot be resolved from the
        # board summary; keep them, but give them a neutral score.
        return 6, True, []

    def _location_is_us(self, location: str) -> bool:
        """US-only view of a location, keeping unresolved locations visible."""
        text = (location or "").strip().lower()
        if not text or text in {"n/a", "unknown"}:
            return True
        return not self._is_explicit_non_us(text) or self._is_us(text)

    @staticmethod
    def _is_explicit_non_us(text: str) -> bool:
        for country in _NON_US_COUNTRIES:
            if re.search(rf"(?<![a-z]){re.escape(country)}(?![a-z])", text):
                return True
        return False

    @staticmethod
    def _is_us(text: str) -> bool:
        """True when the text names a US place (not merely "remote")."""
        if re.search(r"\b(united states|u\.?s\.?a?|usa)\b", text):
            return True
        if any(state in text for state in _US_STATE_NAMES):
            return True
        # State abbreviations only when they appear as a location suffix,
        # e.g. "Columbus, OH", "New York, NY; Toronto, Canada".
        return bool(re.search(r",\s*([a-z]{2})(?=[\s;,]|$)", text)) and any(
            match.group(1) in _US_STATES
            for match in re.finditer(r",\s*([a-z]{2})(?=[\s;,]|$)", text)
        )

    # -- seniority -------------------------------------------------------
    def _required_years(self, description: str) -> Optional[int]:
        if not description:
            return None
        years = []
        for pattern in _EXPERIENCE_PATTERNS:
            for match in pattern.finditer(description):
                try:
                    value = int(match.group(1))
                except (TypeError, ValueError):
                    continue
                if 0 < value <= 25:
                    years.append(value)
        return max(years) if years else None

    # -- public ----------------------------------------------------------
    def score(
        self,
        title: str,
        description: str = "",
        location: str = "",
        employment_type: str = "",
    ) -> MatchResult:
        title = title or ""
        description = description or ""
        location = location or ""

        lowered_title = title.lower()
        for phrase, pattern in zip(self.exclude_titles, self._exclude_title_patterns):
            if pattern.search(lowered_title):
                return MatchResult(
                    score=0,
                    title_score=0,
                    skill_score=0,
                    location_score=0,
                    seniority_score=0,
                    excluded=True,
                    exclusion_reason=f"excluded title: {phrase}",
                    is_us=self._location_is_us(location),
                )

        lowered_description = description.lower()
        for keyword, pattern in zip(
            self.exclude_keywords, self._exclude_keyword_patterns
        ):
            if pattern.search(lowered_description):
                return MatchResult(
                    score=0,
                    title_score=0,
                    skill_score=0,
                    location_score=0,
                    seniority_score=0,
                    excluded=True,
                    exclusion_reason=f"description mentions “{keyword}”",
                    is_us=self._location_is_us(location),
                )

        title_score, reasons = self._title_score(title)
        location_score, is_us, location_reasons = self._location(location)

        # A title with no target phrase and no title keyword can never pass
        # is_match(), so skip the expensive description scan for it. This keeps
        # /jobs/matches fast on windows with thousands of unrelated postings.
        if title_score == 0:
            reasons.extend(location_reasons)
            return MatchResult(
                score=min(100, location_score + 5),
                title_score=0,
                skill_score=0,
                location_score=location_score,
                seniority_score=5,
                reasons=tuple(reasons),
                is_us=is_us,
            )

        combined = f"{title}\n{description}"
        skill_score, matched_skills, all_skills = self._skill_score(combined)

        required_years = self._required_years(description)
        seniority_score = 5
        penalty = 0
        if required_years is not None and required_years > self.max_years:
            seniority_score = 0
            penalty = min(20, (required_years - self.max_years) * 3)
            reasons.append(
                f"asks for {required_years} years (profile: {self.max_years})"
            )

        if skill_score:
            reasons.append("skills: " + ", ".join(matched_skills[:5]))
        reasons.extend(location_reasons)

        score = max(
            0,
            min(
                100,
                title_score + skill_score + location_score + seniority_score - penalty,
            ),
        )

        return MatchResult(
            score=score,
            title_score=title_score,
            skill_score=skill_score,
            location_score=location_score,
            seniority_score=seniority_score,
            matched_skills=tuple(matched_skills),
            reasons=tuple(reasons),
            excluded=False,
            is_us=is_us,
            required_years=required_years,
        )

    def score_job(self, job: Dict[str, Any]) -> MatchResult:
        return self.score(
            title=job.get("job_title") or job.get("title") or "",
            description=job.get("description") or "",
            location=job.get("location") or "",
            employment_type=job.get("employment_type") or "",
        )

    def is_match(self, result: MatchResult, min_score: Optional[int] = None) -> bool:
        threshold = self.min_score if min_score is None else min_score
        return (
            not result.excluded
            and result.title_score > 0
            and result.score >= threshold
        )


def load_profile(path: Optional[os.PathLike | str] = None) -> Dict[str, Any]:
    profile_path = Path(
        path or os.environ.get("JOB_TRACKER_PROFILE") or DEFAULT_PROFILE_PATH
    )
    if not profile_path.exists():
        return {}
    with profile_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return data if isinstance(data, dict) else {}


@lru_cache(maxsize=4)
def _cached_matcher(path_str: str) -> JobMatcher:
    return JobMatcher(load_profile(path_str))


def get_matcher(path: Optional[os.PathLike | str] = None) -> JobMatcher:
    """Return a cached matcher for the profile (defaults to config/profile.yaml)."""
    profile_path = Path(
        path or os.environ.get("JOB_TRACKER_PROFILE") or DEFAULT_PROFILE_PATH
    )
    return _cached_matcher(str(profile_path.resolve()))


def score_job(job: Dict[str, Any], matcher: Optional[JobMatcher] = None) -> Dict[str, Any]:
    """Convenience wrapper returning a JSON-ready match dictionary."""
    return (matcher or get_matcher()).score_job(job).as_dict()
