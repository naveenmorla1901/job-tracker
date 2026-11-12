"""Tests for the idempotent schema sync used at deploy time."""
from sqlalchemy import create_engine, inspect, text

from app.db.models import Base
from update_db import sync_schema


def _engine():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


def test_sync_schema_relaxes_legacy_unique_job_id_index():
    engine = _engine()
    with engine.begin() as connection:
        connection.execute(text("DROP INDEX ix_jobs_job_id"))
        connection.execute(
            text("CREATE UNIQUE INDEX ix_jobs_job_id ON jobs (job_id)")
        )

    inspector = inspect(engine)
    legacy = {index["name"]: index for index in inspector.get_indexes("jobs")}
    assert bool(legacy["ix_jobs_job_id"]["unique"]) is True

    sync_schema(engine)

    indexes = {index["name"]: index for index in inspect(engine).get_indexes("jobs")}
    assert not indexes["ix_jobs_job_id"]["unique"]

    # Running it again must be a no-op rather than an error.
    sync_schema(engine)
    indexes = {index["name"]: index for index in inspect(engine).get_indexes("jobs")}
    assert not indexes["ix_jobs_job_id"]["unique"]


def test_sync_schema_keeps_per_company_unique_constraint():
    engine = _engine()

    sync_schema(engine)

    constraints = {
        constraint["name"]
        for constraint in inspect(engine).get_unique_constraints("jobs")
    }
    assert "uix_job_company" in constraints


def test_job_ids_can_repeat_across_companies_after_sync():
    engine = _engine()
    sync_schema(engine)

    with engine.begin() as connection:
        for company in ("Acme", "Other"):
            connection.execute(
                text(
                    "INSERT INTO jobs (job_id, job_title, job_url, company, "
                    "date_posted, first_seen, last_updated, is_active) "
                    "VALUES ('R13950', 'Data Scientist', "
                    "'https://example.com/j', :company, CURRENT_TIMESTAMP, "
                    "CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 1)"
                ),
                {"company": company},
            )

        count = connection.execute(
            text("SELECT COUNT(*) FROM jobs WHERE job_id = 'R13950'")
        ).scalar_one()
    assert count == 2
