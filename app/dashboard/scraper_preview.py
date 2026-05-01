"""Convert scraper return dicts to JSON snippets for the dashboard."""

from __future__ import annotations

import json
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List

JobDict = Dict[str, Any]


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
