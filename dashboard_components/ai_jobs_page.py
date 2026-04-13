"""
AI & Data Science Jobs page - pre-filtered to show only AI/ML/DS engineering roles
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import time
import logging
import traceback

from dashboard_components.utils import (
    fetch_data,
    fetch_data_with_params,
    get_api_url
)
from app.dashboard.auth import is_authenticated
from dashboard_components.custom_jobs_table import display_custom_jobs_table

logger = logging.getLogger('job_tracker.dashboard.ai_jobs_page')

# ---------------------------------------------------------------------------
# Title-level keyword filter (applied client-side after the API response).
# Scrapers sometimes return loosely-matched results from company job boards
# (e.g. "Construction Engineer" when searching "AI Engineer").
# Any job whose title does NOT match at least one pattern below is excluded.
# ---------------------------------------------------------------------------
import re

AI_TITLE_PATTERNS = [
    r"data\s+scien",           # data scientist, data science
    r"machine\s+learning",
    r"\bml\b",                 # ML Engineer, ML Ops …
    r"\bai\b",                 # AI Engineer, AI Researcher …
    r"\bartificial\s+intelligence\b",
    r"natural\s+language",
    r"\bnlp\b",
    r"computer\s+vision",
    r"generative\s+ai",
    r"\bllm\b",
    r"large\s+language\s+model",
    r"foundation\s+model",
    r"\brag\b",                # RAG Engineer
    r"prompt\s+engineer",
    r"\bmlops\b",
    r"deep\s+learning",
    r"neural\s+network",
    r"reinforcement\s+learning",
    r"data\s+engineer",
    r"ai/ml",
    r"ml/ai",
    r"ai\s+architect",
    r"ml\s+architect",
    r"ai\s+agent",
    r"ai\s+platform",
    r"ai\s+infrastructure",
    r"ai\s+research",
    r"applied\s+scientist",
    r"research\s+scientist",   # common AI/ML job title
    r"quantitative\s+researcher",
]

_AI_PATTERN = re.compile("|".join(AI_TITLE_PATTERNS), re.IGNORECASE)


def _is_ai_ds_title(title: str) -> bool:
    """Return True if the job title looks like an AI/DS role."""
    return bool(_AI_PATTERN.search(title or ""))


# ---------------------------------------------------------------------------
# Target roles – these are the exact Role.name values stored in the database
# (after crud.clean_role_name() normalisation).
# ---------------------------------------------------------------------------
AI_DS_ROLES = [
    # Core AI / ML engineering
    "AI Engineer",
    "Machine Learning Engineer",
    "AI Research Engineer python",
    "AI Infrastructure Engineer",
    "AI/ML Architect",
    "AI Agent Engineer",
    # Data Science
    "Data Science",
    "Data Scientist",
    # Specialised AI
    "Natural Language Processing Engineer AI python",
    "Computer Vision Engineer AI python",
    "Generative AI Engineer python",
    "Generative AI Architect",
    # LLM / Foundation Models
    "LLM Engineer",
    "AI/LLM Researcher",
    "Foundation Model Engineer",
    "RAG Engineer",
    # Operations & tooling
    "MLOps Engineer",
    "Prompt Engineer",
]

# Human-friendly display labels for each role
ROLE_DISPLAY_LABELS = {
    "AI Engineer": "AI Engineer",
    "Machine Learning Engineer": "ML Engineer",
    "AI Research Engineer python": "AI Research Engineer",
    "AI Infrastructure Engineer": "AI Infrastructure Engineer",
    "AI/ML Architect": "AI/ML Architect",
    "AI Agent Engineer": "AI Agent Engineer",
    "Data Science": "Data Science",
    "Data Scientist": "Data Scientist",
    "Natural Language Processing Engineer AI python": "NLP Engineer",
    "Computer Vision Engineer AI python": "Computer Vision Engineer",
    "Generative AI Engineer python": "Generative AI Engineer",
    "Generative AI Architect": "Generative AI Architect",
    "LLM Engineer": "LLM Engineer",
    "AI/LLM Researcher": "AI / LLM Researcher",
    "Foundation Model Engineer": "Foundation Model Engineer",
    "RAG Engineer": "RAG Engineer",
    "MLOps Engineer": "MLOps Engineer",
    "Prompt Engineer": "Prompt Engineer",
}


def display_ai_jobs_page():
    """Display the AI & Data Science jobs page with pre-applied role filters."""
    dashboard_start = time.time()

    st.title("AI & Data Science Jobs")
    st.markdown(
        "This page shows **only AI, ML, and Data Science engineering roles** — "
        "filtered automatically so you can focus on what matters."
    )

    # -- Stats row -------------------------------------------------------
    try:
        stats = fetch_data("jobs/stats") or {}
        if stats and not stats.get("error"):
            metrics_cols = st.columns(3)
            metrics_cols[0].metric("Total Active Jobs (all)", stats.get("total_active_jobs", 0))
            metrics_cols[1].metric("Added Today (all)", stats.get("added_today", 0))
            jobs_by_date = stats.get("jobs_by_date", [])
            recent_count = sum(item.get("count", 0) for item in jobs_by_date[:3]) if jobs_by_date else 0
            metrics_cols[2].metric("Last 3 Days (all)", recent_count)
    except Exception as e:
        logger.error(f"Error displaying job statistics: {str(e)}")

    # -- Included roles expander -----------------------------------------
    with st.expander("Roles included in this view", expanded=False):
        label_cols = st.columns(3)
        labels = [ROLE_DISPLAY_LABELS.get(r, r) for r in AI_DS_ROLES]
        for idx, label in enumerate(labels):
            label_cols[idx % 3].markdown(f"✅ {label}")

    # -- Sidebar filters -------------------------------------------------
    st.sidebar.header("Filters")

    # Time period
    st.sidebar.subheader("Time Period")
    time_options = [
        {"label": "Today",       "days": 1, "key": "today"},
        {"label": "Yesterday",   "days": 1, "key": "yesterday"},
        {"label": "Last 3 days", "days": 3, "key": "days_3"},
        {"label": "Last 4 days", "days": 4, "key": "days_4"},
        {"label": "Last 5 days", "days": 5, "key": "days_5"},
        {"label": "Last 6 days", "days": 6, "key": "days_6"},
        {"label": "Last 7 days", "days": 7, "key": "days_7"},
    ]

    if "ai_time_filters" not in st.session_state:
        st.session_state.ai_time_filters = {"days_7": True}

    selected_time_keys = []
    for option in time_options:
        key = f"ai_time_{option['key']}"
        is_checked = st.sidebar.checkbox(
            option["label"],
            value=st.session_state.ai_time_filters.get(option["key"], False),
            key=key,
        )
        st.session_state.ai_time_filters[option["key"]] = is_checked
        if is_checked:
            selected_time_keys.append(option["key"])

    if not selected_time_keys:
        selected_time_keys = ["days_7"]
        st.session_state.ai_time_filters = {"days_7": True}
        st.rerun()

    max_days = 1
    for option in time_options:
        if option["key"] in selected_time_keys:
            if option["key"] == "today":
                max_days = max(max_days, 1)
            elif option["key"] == "yesterday":
                max_days = max(max_days, 2)
            else:
                max_days = max(max_days, option["days"])

    selected_days = max_days
    today = datetime.now().date()
    start_date = today - timedelta(days=selected_days)
    selected_time_labels = [o["label"] for o in time_options if o["key"] in selected_time_keys]
    st.markdown(f"Showing jobs for: **{', '.join(selected_time_labels)}**")
    st.markdown(f"Date range: **{start_date.strftime('%Y-%m-%d')}** to **{today.strftime('%Y-%m-%d')}**")

    # Search and company filters
    search_term = st.sidebar.text_input("Search by Keyword", key="ai_search")

    companies_data = fetch_data("jobs/companies") or {"companies": []}
    companies = sorted(companies_data["companies"])
    selected_companies = st.sidebar.multiselect(
        "Companies (select multiple)", companies, default=[], key="ai_companies"
    )

    if search_term or selected_companies:
        if st.sidebar.button("Clear Filters", key="ai_clear"):
            for k in list(st.session_state.keys()):
                if k.startswith("ai_") and k != "ai_time_filters":
                    del st.session_state[k]
            st.rerun()

    # -- Build API request params ----------------------------------------
    request_params = [("days", selected_days), ("limit", 1000)]
    for role in AI_DS_ROLES:
        request_params.append(("role", role))
    if selected_companies:
        for company in selected_companies:
            request_params.append(("company", company))
    if search_term:
        request_params.append(("search", search_term))

    # -- Fetch jobs ------------------------------------------------------
    jobs_data = fetch_data_with_params("jobs", request_params) or {"jobs": [], "total": 0}
    # Note: total shown after client-side title filter is applied below
    api_total = jobs_data.get("total", 0)

    # -- Process & display -----------------------------------------------
    if jobs_data.get("jobs"):
        try:
            df_jobs = pd.DataFrame(jobs_data["jobs"])

            # ---------------------------------------------------------------
            # Client-side title filter – remove jobs whose titles don't match
            # any AI/DS keyword, regardless of which role tag the scraper
            # assigned them.
            # ---------------------------------------------------------------
            if "job_title" in df_jobs.columns:
                before = len(df_jobs)
                df_jobs = df_jobs[df_jobs["job_title"].apply(_is_ai_ds_title)]
                removed = before - len(df_jobs)
                if removed:
                    logger.info(f"Title filter removed {removed} non-AI/DS jobs from display")

            st.markdown(
                f"<h4 style='margin-bottom:0; padding-bottom:0;'>"
                f"Found {len(df_jobs)} AI/DS jobs matching your criteria</h4>",
                unsafe_allow_html=True,
            )

            # Client-side date filtering
            if "date_posted" in df_jobs.columns:
                df_jobs["date_posted"] = pd.to_datetime(df_jobs["date_posted"])
                date_masks = []
                for key in selected_time_keys:
                    if key == "today":
                        date_masks.append(df_jobs["date_posted"].dt.normalize() == pd.Timestamp(today))
                    elif key == "yesterday":
                        date_masks.append(
                            df_jobs["date_posted"].dt.normalize()
                            == pd.Timestamp(today - timedelta(days=1))
                        )
                    elif key.startswith("days_"):
                        days = int(key.split("_")[1])
                        cutoff = pd.Timestamp(today - timedelta(days=days - 1))
                        date_masks.append(df_jobs["date_posted"].dt.normalize() >= cutoff)
                if date_masks:
                    combined = date_masks[0]
                    for m in date_masks[1:]:
                        combined = combined | m
                    df_jobs = df_jobs[combined]

            # Charts
            if "date_posted" in df_jobs.columns and len(df_jobs) > 0:
                df_jobs["date_posted"] = pd.to_datetime(df_jobs["date_posted"])
                viz_col1, viz_col2 = st.columns(2)

                with viz_col1:
                    if "roles" in df_jobs.columns:
                        roles_df = df_jobs.explode("roles")
                        # Replace long internal names with display labels
                        roles_df["roles"] = roles_df["roles"].map(
                            lambda r: ROLE_DISPLAY_LABELS.get(r, r) if r else r
                        )
                        roles_df["count"] = 1
                        roles_viz_df = (
                            roles_df.groupby(
                                [pd.Grouper(key="date_posted", freq="D"), "roles"]
                            )["count"]
                            .sum()
                            .reset_index()
                        )
                        top_roles = roles_df["roles"].value_counts().nlargest(10).index.tolist()
                        roles_viz_df = roles_viz_df[roles_viz_df["roles"].isin(top_roles)]

                        fig1 = px.bar(
                            roles_viz_df,
                            x="date_posted",
                            y="count",
                            color="roles",
                            title="AI/DS Jobs by Role Over Time",
                            labels={
                                "date_posted": "Date Posted",
                                "count": "Number of Jobs",
                                "roles": "Role",
                            },
                        )
                        min_date = df_jobs["date_posted"].min()
                        max_date = df_jobs["date_posted"].max()
                        fig1.update_layout(
                            height=350,
                            margin=dict(l=20, r=20, t=40, b=20),
                            xaxis=dict(
                                range=[
                                    min_date - pd.Timedelta(hours=12),
                                    max_date + pd.Timedelta(hours=12),
                                ],
                                tickformat="%Y-%m-%d",
                            ),
                        )
                        st.plotly_chart(fig1, use_container_width=True)
                    else:
                        st.info("Role data not available for visualization")

                with viz_col2:
                    if "company" in df_jobs.columns:
                        company_counts = df_jobs["company"].value_counts().reset_index()
                        company_counts.columns = ["company", "count"]
                        top_companies = company_counts.nlargest(15, "count")

                        fig2 = px.treemap(
                            top_companies,
                            path=["company"],
                            values="count",
                            color="count",
                            color_continuous_scale="blues",
                            title="Top Companies Hiring for AI/DS Roles",
                        )
                        fig2.update_layout(height=350, margin=dict(l=20, r=20, t=40, b=20))
                        fig2.update_traces(
                            textinfo="label+value",
                            hovertemplate="<b>%{label}</b><br>Jobs: %{value}<extra></extra>",
                        )
                        st.plotly_chart(fig2, use_container_width=True)
                    else:
                        st.info("Company data not available for visualization")

            display_custom_jobs_table(df_jobs)

        except Exception as e:
            st.error(f"Error processing job data: {str(e)}")
            logger.error(f"Error processing job data: {str(e)}")
            logger.error(traceback.format_exc())
    else:
        st.markdown(
            "<h4 style='margin-bottom:0; padding-bottom:0;'>Found 0 AI/DS jobs matching your criteria</h4>",
            unsafe_allow_html=True,
        )
        st.info(
            "No AI/DS jobs found for the selected filters. "
            "Try extending the time period or clearing extra filters."
        )

    # -- Footer info -----------------------------------------------------
    dashboard_time = time.time() - dashboard_start
    st.sidebar.write("---")
    st.sidebar.info(f"Page loaded in {dashboard_time:.2f}s")
