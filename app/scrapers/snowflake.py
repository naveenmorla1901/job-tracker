"""Snowflake jobs from its Ashby board."""
from app.scrapers.ats_boards import fetch_ashby_jobs


def get_snowflake_jobs(roles, days=7):
    """Return Snowflake jobs posted in the last `days` days, grouped by role."""
    return fetch_ashby_jobs("snowflake", roles, days)
