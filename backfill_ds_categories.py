"""
One-time backfill: attach 'Data Science' or 'Non Data Science' category role
to every active job already in the database, based on job_title + description.

Run once after deploying the categorization changes:
    python backfill_ds_categories.py
"""

import logging
import sys
import os

# Make sure project root is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("backfill_ds_categories")

from app.db.database import get_db
from app.db.models import Job, Role
from app.db.crud import get_or_create_role, add_role_to_job
from app.scrapers.role_specific_matcher import is_data_science_job

CATEGORY_DS = "Data Science"
CATEGORY_NON_DS = "Non Data Science"
BATCH_SIZE = 200


def backfill():
    db = next(get_db())

    try:
        total_active = db.query(Job).filter(Job.is_active == True).count()
        logger.info(f"Active jobs to backfill: {total_active}")

        # Pre-create both category roles so we don't hit DB for every job
        cat_ds = get_or_create_role(db, CATEGORY_DS)
        cat_non_ds = get_or_create_role(db, CATEGORY_NON_DS)

        tagged_ds = 0
        tagged_non_ds = 0
        skipped = 0
        offset = 0

        while True:
            batch = (
                db.query(Job)
                .filter(Job.is_active == True)
                .order_by(Job.id)
                .offset(offset)
                .limit(BATCH_SIZE)
                .all()
            )
            if not batch:
                break

            for job in batch:
                existing_role_names = {r.name for r in job.roles}

                # Skip if already categorized
                if CATEGORY_DS in existing_role_names or CATEGORY_NON_DS in existing_role_names:
                    skipped += 1
                    continue

                title = job.job_title or ""
                desc = job.description or ""
                text = f"{title}\n{desc}".strip()

                if is_data_science_job(text):
                    add_role_to_job(db, job, cat_ds)
                    tagged_ds += 1
                else:
                    add_role_to_job(db, job, cat_non_ds)
                    tagged_non_ds += 1

            db.commit()
            offset += BATCH_SIZE
            logger.info(
                f"Progress: {min(offset, total_active)}/{total_active} — "
                f"DS={tagged_ds}, Non-DS={tagged_non_ds}, already-tagged={skipped}"
            )

        logger.info(
            f"Backfill complete. "
            f"Tagged as DS: {tagged_ds}, Non-DS: {tagged_non_ds}, already had category: {skipped}"
        )

    except Exception as e:
        logger.error(f"Backfill failed: {e}", exc_info=True)
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    backfill()
