"""Best Matches page: jobs ranked against the user's profile."""
import logging
import time

import pandas as pd
import plotly.express as px
import streamlit as st

from dashboard_components.custom_jobs_table import display_custom_jobs_table
from dashboard_components.utils import fetch_data, fetch_data_with_params

logger = logging.getLogger("job_tracker.dashboard.matches_page")

TIME_OPTIONS = {
    "Today": 1,
    "Last 3 days": 3,
    "Last 7 days": 7,
    "Last 14 days": 14,
}
DEFAULT_CATEGORIES = ["AI / ML", "Data Science", "Data Engineering", "Data Analytics"]


def display_matches_page():
    """Render profile-ranked jobs with score and skill explanations."""
    page_start = time.time()

    st.title("Best Matches")
    st.caption(
        "Every active posting in the selected window is scored against "
        "`config/profile.yaml` on title, skills, location, and seniority. "
        "Hard requirements (manager/director titles, no-sponsorship language) "
        "are rejected automatically."
    )

    profile = fetch_data("jobs/profile") or {}
    categories_data = fetch_data("jobs/ai-ds/categories") or {}
    all_categories = categories_data.get("categories") or DEFAULT_CATEGORIES

    st.sidebar.header("Match filters")
    time_label = st.sidebar.radio(
        "Posted", list(TIME_OPTIONS), index=2, key="match_time"
    )
    days = TIME_OPTIONS[time_label]

    default_score = int(profile.get("min_score", 55) or 55)
    min_score = st.sidebar.slider(
        "Minimum match score", 0, 100, default_score, key="match_min_score"
    )
    us_only = st.sidebar.checkbox(
        "US / remote only", value=True, key="match_us_only"
    )

    selected_categories = st.sidebar.multiselect(
        "Categories", all_categories, default=all_categories, key="match_categories"
    )
    search_term = st.sidebar.text_input(
        "Search title or description", key="match_search"
    )
    companies = sorted((fetch_data("jobs/companies") or {}).get("companies", []))
    selected_companies = st.sidebar.multiselect(
        "Companies", companies, default=[], key="match_companies"
    )

    if not selected_categories:
        st.info("Select at least one category in the sidebar.")
        return

    params = [
        ("days", days),
        ("min_score", min_score),
        ("us_only", "true" if us_only else "false"),
        ("limit", 1000),
    ]
    params += [("category", category) for category in selected_categories]
    params += [("company", company) for company in selected_companies]
    if search_term:
        params.append(("search", search_term))

    data = fetch_data_with_params("jobs/matches", params, timeout=60) or {}
    jobs = data.get("jobs", [])
    stats = data.get("stats", {}) or {}

    total = data.get("total", len(jobs))
    metric_cols = st.columns(4)
    metric_cols[0].metric("Matches", total)
    metric_cols[1].metric("Strong (80+)", stats.get("strong_matches", 0))
    metric_cols[2].metric("Average score", stats.get("average_score", 0))
    metric_cols[3].metric("Scanned", stats.get("scanned", 0))

    if not jobs:
        st.info(
            "No jobs clear this score. Try a lower minimum, a longer time window, "
            "or turn off the US/remote filter."
        )
        _render_profile(profile)
        return

    df = pd.DataFrame(jobs)

    chart_left, chart_right = st.columns(2)
    with chart_left:
        skills = pd.DataFrame(stats.get("top_skills", []))
        if not skills.empty:
            fig = px.bar(
                skills.sort_values("count"),
                x="count",
                y="skill",
                orientation="h",
                title="Skills most often matched",
                labels={"count": "Jobs", "skill": "Skill"},
            )
            fig.update_layout(height=340, margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No skill matches in this selection.")

    with chart_right:
        top_companies = pd.DataFrame(stats.get("top_companies", []))
        if not top_companies.empty:
            fig = px.treemap(
                top_companies,
                path=["company"],
                values="count",
                color="count",
                color_continuous_scale="blues",
                title="Companies with the most matches",
            )
            fig.update_layout(height=340, margin=dict(l=10, r=10, t=40, b=10))
            fig.update_traces(textinfo="label+value")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No company data for this selection.")

    display_custom_jobs_table(df)
    _render_profile(profile)

    st.sidebar.write("---")
    st.sidebar.caption(f"Page loaded in {time.time() - page_start:.2f}s")


def _render_profile(profile):
    if not profile:
        return
    with st.expander("Matching profile"):
        st.markdown(
            f"**{profile.get('name') or 'Profile'}** · "
            f"minimum score **{profile.get('min_score', 55)}** · "
            f"experience cap **{profile.get('max_years_experience', 5)} years**"
        )
        st.markdown("**Target titles**")
        st.write(", ".join(profile.get("target_titles", [])))
        st.markdown("**Preferred locations**")
        st.write(", ".join(profile.get("preferred_locations", [])))
        st.caption(
            "Edit `config/profile.yaml` and redeploy to change the ranking. "
            "The API exposes the same data at `/api/jobs/matches`."
        )
