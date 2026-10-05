"""
AI & Data Science Jobs page.

Jobs are classified by title on the API side (app/role_categories.py), not by
the role tag a scraper attached from its search term, so loose matches from
company job boards ("Construction Engineer" for an "AI Engineer" search) stay
out and the counts shown are exact.
"""
import logging
import time
import traceback
from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

from dashboard_components.utils import fetch_data, fetch_data_with_params
from dashboard_components.custom_jobs_table import display_custom_jobs_table

logger = logging.getLogger('job_tracker.dashboard.ai_jobs_page')

DEFAULT_CATEGORIES = ["AI / ML", "Data Science", "Data Engineering", "Data Analytics"]

# label -> (days to request from the API, exact posted-date rule)
TIME_OPTIONS = {
    "Today": (1, "today"),
    "Yesterday": (2, "yesterday"),
    "Last 3 days": (3, 3),
    "Last 7 days": (7, 7),
    "Last 14 days": (14, 14),
}


def _apply_date_rule(df, rule, today):
    posted = pd.to_datetime(df["date_posted"]).dt.normalize()
    if rule == "today":
        return df[posted == pd.Timestamp(today)]
    if rule == "yesterday":
        return df[posted == pd.Timestamp(today - timedelta(days=1))]
    return df[posted >= pd.Timestamp(today - timedelta(days=rule - 1))]


def display_ai_jobs_page():
    """Display AI / data jobs filtered by title category."""
    page_start = time.time()

    st.title("AI & Data Science Jobs")
    st.caption(
        "Jobs are matched on their **title** (e.g. contains *machine learning*, *data scientist*, "
        "*data engineer*), so loose search results from company job boards are left out."
    )

    # -- Sidebar filters -------------------------------------------------
    st.sidebar.header("Filters")
    time_label = st.sidebar.radio("Posted", list(TIME_OPTIONS.keys()), index=0, key="ai_time")
    request_days, date_rule = TIME_OPTIONS[time_label]

    categories_data = fetch_data("jobs/ai-ds/categories") or {}
    all_categories = categories_data.get("categories") or DEFAULT_CATEGORIES
    selected_categories = st.sidebar.multiselect(
        "Categories", all_categories, default=all_categories, key="ai_categories"
    )
    if not selected_categories:
        st.info("Select at least one category in the sidebar.")
        return

    search_term = st.sidebar.text_input("Search title or description", key="ai_search")
    companies = sorted((fetch_data("jobs/companies") or {}).get("companies", []))
    selected_companies = st.sidebar.multiselect("Companies", companies, default=[], key="ai_companies")

    # -- Fetch -----------------------------------------------------------
    params = [("days", request_days)]
    params += [("category", c) for c in selected_categories]
    params += [("company", c) for c in selected_companies]
    if search_term:
        params.append(("search", search_term))

    data = fetch_data_with_params("jobs/ai-ds", params) or {}
    jobs = data.get("jobs", [])
    if not jobs:
        st.subheader("0 jobs")
        st.info("No AI / data jobs for these filters. Try a longer time period or fewer filters.")
        return

    try:
        today = datetime.now().date()
        df = _apply_date_rule(pd.DataFrame(jobs), date_rule, today)

        # Counts are taken after every filter, so they match the table below
        st.subheader(f"{len(df)} jobs · {time_label.lower()}")
        exploded = df.explode("categories")
        counts = exploded["categories"].value_counts()
        metric_cols = st.columns(len(selected_categories))
        for col, name in zip(metric_cols, selected_categories):
            col.metric(name, int(counts.get(name, 0)))

        if df.empty:
            st.info("No jobs in this exact date window.")
            return

        chart_left, chart_right = st.columns(2)
        with chart_left:
            by_day = (
                exploded.assign(date_posted=pd.to_datetime(exploded["date_posted"]))
                .groupby([pd.Grouper(key="date_posted", freq="D"), "categories"])
                .size()
                .reset_index(name="jobs")
            )
            fig = px.bar(
                by_day, x="date_posted", y="jobs", color="categories",
                title="Jobs by category and posted date",
                labels={"date_posted": "Posted", "jobs": "Jobs", "categories": "Category"},
            )
            fig.update_layout(height=350, margin=dict(l=20, r=20, t=40, b=20), xaxis=dict(tickformat="%Y-%m-%d"))
            st.plotly_chart(fig, use_container_width=True)

        with chart_right:
            top = df["company"].value_counts().nlargest(15).reset_index()
            top.columns = ["company", "jobs"]
            fig = px.treemap(
                top, path=["company"], values="jobs", color="jobs",
                color_continuous_scale="blues", title="Top companies",
            )
            fig.update_layout(height=350, margin=dict(l=20, r=20, t=40, b=20))
            fig.update_traces(textinfo="label+value")
            st.plotly_chart(fig, use_container_width=True)

        display_custom_jobs_table(df)

    except Exception as e:
        st.error(f"Error processing job data: {str(e)}")
        logger.error(f"Error processing job data: {str(e)}\n{traceback.format_exc()}")

    st.sidebar.write("---")
    st.sidebar.caption(f"Page loaded in {time.time() - page_start:.2f}s")
