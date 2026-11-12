"""Tests for the profile-ranked /api/jobs/matches endpoint."""
from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.endpoints.jobs import get_matching_jobs
from app.db.models import Base, Job


def _session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def _job(**overrides):
    values = {
        "job_id": "R1",
        "job_title": "Machine Learning Engineer",
        "location": "Remote",
        "job_url": "https://example.com/jobs/1",
        "company": "Acme",
        "date_posted": datetime.utcnow(),
        "employment_type": "Full-time",
        "description": "Python SQL LLM RAG AWS Kubernetes.",
        "is_active": True,
    }
    values.update(overrides)
    return Job(**values)


def test_matches_ranks_and_filters_jobs():
    db = _session()
    db.add_all(
        [
            _job(job_id="R1"),
            _job(
                job_id="R2",
                job_title="Director of Data Science",
                description="Python SQL",
            ),
            _job(
                job_id="R3",
                job_title="Data Scientist",
                location="Paris, France",
                description="Python SQL LLM",
            ),
            _job(
                job_id="R4",
                job_title="Business Analyst",
                location="Columbus, OH",
                description="Excel reporting.",
            ),
            _job(
                job_id="R5",
                job_title="Data Scientist",
                date_posted=datetime.utcnow() - timedelta(days=30),
            ),
        ]
    )
    db.commit()

    response = get_matching_jobs(
        db=db,
        days=7,
        min_score=None,
        us_only=True,
        include_excluded=False,
        company=None,
        category=None,
        search=None,
        limit=200,
        offset=0,
    )

    ids = [job["job_id"] for job in response["jobs"]]
    assert ids == ["R1"]
    assert response["total"] == 1
    assert response["jobs"][0]["match_score"] >= 80
    assert "python" in response["jobs"][0]["matched_skills"]
    assert response["stats"]["scanned"] == 4
    assert response["stats"]["excluded"] == 1
    assert response["stats"]["strong_matches"] == 1
    assert any(skill["skill"] == "python" for skill in response["stats"]["top_skills"])
    db.close()


def test_matches_us_only_off_keeps_non_us_roles():
    db = _session()
    db.add(
        _job(
            job_id="R3",
            job_title="Data Scientist",
            location="Paris, France",
            description="Python SQL LLM",
        )
    )
    db.commit()

    response = get_matching_jobs(
        db=db,
        days=7,
        min_score=0,
        us_only=False,
        include_excluded=False,
        company=None,
        category=None,
        search=None,
        limit=200,
        offset=0,
    )

    assert response["total"] == 1
    assert response["jobs"][0]["is_us"] is False
    db.close()


def test_matches_min_score_hides_weak_titles():
    db = _session()
    db.add(
        _job(
            job_id="R4",
            job_title="Data Analyst",
            location="Columbus, OH",
            description="Excel reporting.",
        )
    )
    db.commit()

    response = get_matching_jobs(
        db=db,
        days=7,
        min_score=90,
        us_only=True,
        include_excluded=False,
        company=None,
        category=None,
        search=None,
        limit=200,
        offset=0,
    )

    assert response["total"] == 0
    assert response["jobs"] == []
    db.close()
