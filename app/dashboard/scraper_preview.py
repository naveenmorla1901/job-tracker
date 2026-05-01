"""Summarize scraper return values (dict of role -> job dicts) for dashboard inspection."""

from __future__ import annotations

import json
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List

JobDict = Dict[str, Any]
JobsByRole = Dict[str, List[JobDict]]


def _json_safe_value(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    if isinstance(value, dict):
        return {k: _json_safe_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe_value(v) for v in value]
    return value


def summarize_jobs_by_role(data: Any) -> Dict[str, Any]:
    """Describe the structure returned by get_*_jobs."""
    if not isinstance(data, dict):
        return {"error": f"Expected dict[str, list], got {type(data).__name__}"}

    job_counts: Dict[str, Any] = {}
    bad_roles: List[str] = []
    field_types: Dict[str, set] = {}
    total = 0

    for role, jobs in data.items():
        key = str(role)
        if not isinstance(jobs, list):
            bad_roles.append(key)
            job_counts[key] = None
            continue
        job_counts[key] = len(jobs)
        total += len(jobs)
        for job in jobs:
            if not isinstance(job, dict):
                continue
            for fkey, val in job.items():
                field_types.setdefault(fkey, set()).add(type(val).__name__)

    field_types_out = {k: sorted(v) for k, v in sorted(field_types.items())}

    return {
        "python_type": "dict[str, list[dict]]",
        "num_roles": len(data),
        "total_job_dicts": total,
        "roles_with_non_list_value": bad_roles,
        "job_counts_per_role": job_counts,
        "keys_seen_on_job_dicts": list(field_types_out.keys()),
        "value_types_per_key": field_types_out,
        "expected_for_upsert": [
            "job_id",
            "job_title",
            "job_url",
            "location",
            "date_posted",
        ],
    }


def build_sample_json(data: Any, max_jobs: int = 5) -> str:
    """Pretty-print a small slice of the scraper output."""
    if not isinstance(data, dict):
        return json.dumps({"error": "Expected dict[str, list]"}, indent=2, ensure_ascii=False)

    sample: Dict[str, List[JobDict]] = {}
    remaining = max_jobs
    for role, jobs in data.items():
        if not isinstance(jobs, list) or remaining <= 0:
            continue
        chunk = jobs[:remaining]
        sample[str(role)] = _json_safe_value(chunk)
        remaining -= len(chunk)
        if remaining <= 0:
            break
    return json.dumps(sample, indent=2, ensure_ascii=False)
