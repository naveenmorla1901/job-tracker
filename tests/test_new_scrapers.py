"""Unit tests for the ATS wrappers added for the last Workday-list companies."""
from datetime import datetime, timedelta, timezone

from bs4 import BeautifulSoup

from app.scrapers import ats_boards, toyota


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


def test_search_phrase_only_strips_trailing_skills():
    assert ats_boards._search_phrase("Data Scientist python SQL") == "Data Scientist"
    assert ats_boards._search_phrase("Data Analyst visualization") == "Data Analyst"
    assert ats_boards._search_phrase("SQL Developer") == "SQL Developer"


def test_role_matcher_keeps_sql_and_stems_engineer():
    sql = ats_boards._role_matcher("SQL Developer")
    assert sql("Senior SQL Developer")
    assert not sql("Salesforce Developer")

    engineer = ats_boards._role_matcher("Data Engineer")
    assert engineer("Senior Engineer - Data Engineering")
    assert not engineer("Skilled Maintenance Team Member")


def test_successfactors_filters_titles_and_dates(monkeypatch):
    now = datetime.now(timezone.utc)
    candidates = [
        {
            "job_title": "Data Scientist",
            "job_id": "1",
            "location": "Remote",
            "job_url": "https://example.com/job/1",
        },
        {
            "job_title": "Accountant",
            "job_id": "2",
            "location": "Remote",
            "job_url": "https://example.com/job/2",
        },
    ]
    monkeypatch.setattr(
        ats_boards, "_successfactors_search", lambda search_url, role: candidates
    )
    monkeypatch.setattr(
        ats_boards,
        "_successfactors_detail",
        lambda url: {
            "posted": now if url.endswith("/1") else now - timedelta(days=30),
            "description": "Test description",
        },
    )

    result = ats_boards.fetch_successfactors_jobs(
        "https://example.com/search/", ["Data Scientist python SQL"], days=7
    )

    jobs = result["Data Scientist python SQL"]
    assert len(jobs) == 1
    assert jobs[0]["job_title"] == "Data Scientist"
    assert jobs[0]["date_posted"] == now.strftime("%Y-%m-%d")


def test_talentbrew_filters_titles_and_dates(monkeypatch):
    now = datetime.now(timezone.utc)
    recent = (now - timedelta(days=1)).strftime("%m/%d/%Y")
    old = (now - timedelta(days=30)).strftime("%m/%d/%Y")
    html = f"""
    <ul>
      <li class="search-results-list__list-item">
        <a class="sr-job-link" data-job-id="111" href="/job/remote/data-engineer/44408/111">
          <h2>Data Engineer</h2>
          <span class="job-location">Remote</span>
          <span class="job-date-posted">Posted: {recent}</span>
        </a>
      </li>
      <li class="search-results-list__list-item">
        <a class="sr-job-link" data-job-id="222" href="/job/remote/accountant/44408/222">
          <h2>Accountant</h2>
          <span class="job-location">Remote</span>
          <span class="job-date-posted">Posted: {old}</span>
        </a>
      </li>
    </ul>
    """
    soup = BeautifulSoup(html, "html.parser")
    monkeypatch.setattr(
        ats_boards, "_talentbrew_page", lambda base_url, role, page: soup
    )
    monkeypatch.setattr(
        ats_boards,
        "_talentbrew_detail",
        lambda url: {"description": "Test description", "employmentType": "Full time"},
    )

    result = ats_boards.fetch_talentbrew_jobs(
        "https://example.com", ["Data Engineer"], days=7
    )

    jobs = result["Data Engineer"]
    assert len(jobs) == 1
    assert jobs[0]["job_title"] == "Data Engineer"
    assert jobs[0]["job_url"] == "https://example.com/job/remote/data-engineer/44408/111"


def test_toyota_only_processes_title_matches(monkeypatch):
    payload = {
        "total": 2,
        "jobPostings": [
            {
                "title": "Data Engineer",
                "externalPath": "/job/Plano/Data-Engineer_1",
                "locationsText": "Plano, Texas",
                "postedOn": "Posted Today",
                "bulletFields": ["1"],
            },
            {
                "title": "Skilled Maintenance Team Member",
                "externalPath": "/job/Liberty/Maintenance_2",
                "locationsText": "Liberty, North Carolina",
                "postedOn": "Posted Today",
                "bulletFields": ["2"],
            },
        ],
    }
    monkeypatch.setattr(
        toyota.requests,
        "post",
        lambda *args, **kwargs: _FakeResponse(payload),
    )
    processed = []

    def fake_process(job, days):
        processed.append(job["title"])
        return {
            "job_title": job["title"],
            "job_id": job["bulletFields"][0],
            "location": job["locationsText"],
            "job_url": "https://example.com" + job["externalPath"],
            "date_posted": "2026-11-10",
            "employment_type": "N/A",
            "description": "Test description",
        }

    monkeypatch.setattr(toyota, "process_toyota_job", fake_process)

    result = toyota.get_toyota_jobs(["Data Engineer"], days=7)

    assert processed == ["Data Engineer"]
    assert [job["job_title"] for job in result["Data Engineer"]] == ["Data Engineer"]
