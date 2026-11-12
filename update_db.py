"""
Idempotent database schema sync used by ``python run.py update_db``.

Alembic is intentionally not used here: the repository has several independent
migration heads, and this script runs on every deploy. Every step is safe to
repeat and is a no-op once the schema is current.

Current change: ``jobs.job_id`` used to be globally unique, which made two
companies posting the same numeric requisition ID (for example ``R13950``)
collide. Uniqueness is now per company via ``uix_job_company``.
"""
import logging

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

from app.db.database import engine
from app.db.models import Base

logger = logging.getLogger("job_tracker.schema")


def _indexes(inspector, table):
    return {index["name"]: index for index in inspector.get_indexes(table)}


def _unique_constraints(inspector, table):
    return {
        constraint["name"]
        for constraint in inspector.get_unique_constraints(table)
        if constraint.get("name")
    }


def _relax_job_id_index(connection, is_constraint):
    """Replace the old globally-unique job_id index with a plain lookup index."""
    if is_constraint:
        connection.execute(
            text("ALTER TABLE jobs DROP CONSTRAINT ix_jobs_job_id")
        )
    else:
        connection.execute(text("DROP INDEX ix_jobs_job_id"))
    connection.execute(text("CREATE INDEX ix_jobs_job_id ON jobs (job_id)"))
    print("Relaxed ix_jobs_job_id: job_id is unique per company, not globally.")


def _ensure_company_unique_constraint(connection, dialect, unique_constraints):
    if "uix_job_company" in unique_constraints:
        return
    if dialect != "postgresql":
        # SQLite cannot add a table constraint after creation. Fresh test
        # databases get it from Base.metadata.create_all.
        print("Skipping uix_job_company on SQLite; recreate the database to add it.")
        return

    duplicates = connection.execute(
        text(
            "SELECT job_id, company, COUNT(*) AS n FROM jobs "
            "GROUP BY job_id, company HAVING COUNT(*) > 1 LIMIT 5"
        )
    ).fetchall()
    if duplicates:
        sample = ", ".join(
            f"{row.job_id}/{row.company} x{row.n}" for row in duplicates
        )
        raise RuntimeError(
            "Cannot add uix_job_company; duplicate (job_id, company) rows: " + sample
        )

    connection.execute(
        text(
            "ALTER TABLE jobs ADD CONSTRAINT uix_job_company "
            "UNIQUE (job_id, company)"
        )
    )
    print("Added uix_job_company (job_id, company).")


def sync_schema(engine: Engine) -> None:
    """Bring an existing database up to the schema the models expect."""
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    if "jobs" not in inspector.get_table_names():
        return

    dialect = engine.dialect.name
    indexes = _indexes(inspector, "jobs")
    unique_constraints = _unique_constraints(inspector, "jobs")
    job_id_index = indexes.get("ix_jobs_job_id")

    with engine.begin() as connection:
        if "ix_jobs_job_id" in unique_constraints:
            # The legacy uniqueness is a table constraint, not an index.
            _relax_job_id_index(connection, is_constraint=True)
        elif job_id_index is None:
            connection.execute(text("CREATE INDEX ix_jobs_job_id ON jobs (job_id)"))
            print("Added ix_jobs_job_id.")
        elif job_id_index.get("unique"):
            _relax_job_id_index(connection, is_constraint=False)

        _ensure_company_unique_constraint(connection, dialect, unique_constraints)


def run_migration_update():
    """Run the schema sync and report the outcome."""
    print("Starting database schema update...")
    try:
        sync_schema(engine)
    except Exception as exc:
        print(f"Error updating database schema: {exc}")
        logger.exception("Database schema update failed")
        return False
    print("Database schema updated successfully!")
    return True


if __name__ == "__main__":
    run_migration_update()
