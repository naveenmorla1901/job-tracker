"""Unit tests for the ATS wrappers added for the last Workday-list companies."""
from datetime import datetime, timedelta, timezone

from bs4 import BeautifulSoup

from app.job_window import filter_jobs_to_window
from app.scrapers import ats_boards, nxp, sedgwick, toyota, xpanse


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


def test_role_matcher_adds_synonyms_without_business_titles():
    assert ats_boards._role_matcher("Data Engineer")("Analytics Engineer")
    assert ats_boards._role_matcher("Data Science")(
        "Principal Decision Scientist, Client Analytics"
    )
    assert ats_boards._role_matcher("AI Engineer")("Machine Learning Engineer")
    assert not ats_boards._role_matcher("AI Engineer")("AI Product Manager")
    assert not ats_boards._role_matcher("Data Engineer")("Data Platform Product Manager")
    assert not ats_boards._role_matcher("Data Science")(
        "Principal Product Manager, Applied AI & Data Science"
    )


def test_job_window_includes_date_only_boundary_and_keeps_unknown_dates():
    now = datetime(2026, 11, 11, 15, 0, tzinfo=timezone.utc)
    jobs = {
        "role": [
            {"job_title": "boundary", "date_posted": "2026-11-04"},
            {"job_title": "old", "date_posted": "2026-11-03"},
            {"job_title": "missing", "date_posted": None},
            {"job_title": "unknown", "date_posted": "N/A"},
        ]
    }

    result = filter_jobs_to_window(jobs, 7, now=now)

    assert [job["job_title"] for job in result["role"]] == [
        "boundary", "missing", "unknown",
    ]


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


def test_eightfold_fetcher_matches_synonyms_and_filters_dates(monkeypatch):
    now = datetime.now(timezone.utc)
    recent = int(now.timestamp())
    old = int((now - timedelta(days=30)).timestamp())
    positions = [
        {
            "id": 1,
            "displayJobId": "26WD1",
            "name": "Analytics Engineer",
            "locations": ["Remote"],
            "postedTs": recent,
            "positionUrl": "/careers/job/1",
        },
        {
            "id": 2,
            "displayJobId": "26WD2",
            "name": "AI Product Manager",
            "locations": ["Remote"],
            "postedTs": recent,
            "positionUrl": "/careers/job/2",
        },
        {
            "id": 3,
            "displayJobId": "26WD3",
            "name": "Data Engineer",
            "locations": ["Remote"],
            "postedTs": old,
            "positionUrl": "/careers/job/3",
        },
    ]

    def fake_get(url, params=None, headers=None, timeout=None):
        if url.endswith("/api/pcsx/search"):
            return _FakeResponse({
                "data": {"count": len(positions), "positions": positions},
            })
        if url.endswith("/api/pcsx/position_details"):
            position = next(p for p in positions if p["id"] == params["position_id"])
            return _FakeResponse({
                "data": {
                    **position,
                    "jobDescription": "<p>Build data pipelines</p>",
                },
            })
        raise AssertionError(url)

    monkeypatch.setattr(ats_boards.requests, "get", fake_get)

    result = ats_boards.fetch_eightfold_jobs(
        "https://jobs.example.com", "example.com", ["Data Engineer", "AI Engineer"], days=7
    )

    assert [job["job_title"] for job in result["Data Engineer"]] == ["Analytics Engineer"]
    assert [job["job_title"] for job in result["AI Engineer"]] == []
    job = result["Data Engineer"][0]
    assert job["job_url"] == "https://jobs.example.com/careers/job/1"
    assert job["description"] == "Build data pipelines"


def test_xpanse_uses_current_careers_board(monkeypatch):
    captured = {}

    def fake_post(url, json=None, headers=None, timeout=None):
        captured["url"] = url
        captured["referer"] = headers.get("Referer")
        return _FakeResponse({"jobPostings": []})

    monkeypatch.setattr(xpanse.requests, "post", fake_post)

    xpanse.get_xpanse_jobs(["Data Engineer"], days=7)

    assert captured["url"].endswith("/archwellessentials/Careers/jobs")
    assert captured["referer"].endswith("/Careers")


def test_sedgwick_uses_posted_on_for_boundary_job(monkeypatch):
    payload = {
        "jobPostings": [
            {
                "title": "Data Engineer",
                "externalPath": "/job/Telecommuter-TX/Data-Engineer_R75957",
                "locationsText": "Telecommuter-TX",
                "postedOn": "Posted 7 Days Ago",
                "bulletFields": ["R75957"],
            },
        ],
    }
    monkeypatch.setattr(
        sedgwick.requests, "post", lambda *args, **kwargs: _FakeResponse(payload)
    )
    monkeypatch.setattr(
        sedgwick,
        "get_sedgwick_job_details",
        lambda url: {
            "datePosted": "2026-11-04",
            "employmentType": "FULL_TIME",
            "description": "Test description",
        },
    )

    result = sedgwick.get_sedgwick_jobs(["Data Engineer"], days=7)

    assert [job["job_id"] for job in result["Data Engineer"]] == ["R75957"]


def test_nxp_reports_upstream_outage(monkeypatch, capsys):
    class _OutageResponse:
        status_code = 422

        def raise_for_status(self):
            raise AssertionError("422 should be handled as an outage")

    monkeypatch.setattr(
        nxp.requests, "post", lambda *args, **kwargs: _OutageResponse()
    )

    result = nxp.get_nxp_jobs(["Data Engineer"], days=7)

    assert result["Data Engineer"] == []
    assert "SCRAPER_UNAVAILABLE" in capsys.readouterr().out
