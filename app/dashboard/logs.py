"""
Simplified logs page for the Job Tracker dashboard
"""
import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os
import logging

# Add parent directory to path to import log_manager
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from log_manager import get_log_files, read_log_content, cleanup_old_logs
from system_info import get_system_info, get_api_stats, format_system_info

# Configure logging
logger = logging.getLogger('job_tracker.dashboard.logs')

def display_logs_page():
    """Display a simplified logs page in the Streamlit dashboard"""
    st.title("System Logs & Information")

    # Add refresh button at the top
    if st.button("Refresh Data"):
        st.rerun()

    # Clean up old logs
    st.sidebar.title("Log Management")
    if st.sidebar.button("Clean Up Old Logs (> 2 days)"):
        deleted_count = cleanup_old_logs(days=2)
        st.sidebar.success(f"Deleted {deleted_count} old log files")

    # API / dashboard / system / scraper summary / per-scraper lines / nginx / postgres
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "API Logs",
        "Dashboard Logs",
        "System Info",
        "Scraper Runs",
        "Scraper data output",
        "Nginx Logs",
        "Postgres Logs",
    ])

    # Read API logs
    with tab1:
        _display_api_logs()

    # Read Dashboard logs
    with tab2:
        _display_dashboard_logs()

    # System Information
    with tab3:
        _display_system_info()

    # Scraper Runs and Failures
    with tab4:
        _display_scraper_runs()

    # Live scraper return structure + sample JSON (same tab)
    with tab5:
        _display_scraper_output_preview()

    # Nginx Logs
    with tab6:
        _display_nginx_logs()

    # Postgres Logs
    with tab7:
        _display_postgres_logs()

    # Information about logs cleanup
    st.sidebar.info("Logs are automatically cleaned up every 2 days")

def _display_api_logs():
    """Display API logs in a tab"""
    st.subheader("API Logs (job_tracker.log)")

    # Check if main log file exists
    log_files = ["job_tracker.log", "/var/log/job-tracker/api.log", "/home/ubuntu/job-tracker/job_tracker.log"]
    log_content = []

    for log_file in log_files:
        if os.path.exists(log_file):
            log_content.extend(read_log_content(log_file))

    if log_content:
        # Reverse the log content to show most recent logs first
        log_content.reverse()

        # Display logs in a fixed height read-only text area
        st.code("".join(log_content), language="text")
    else:
        st.warning("No API log files found")

def _display_dashboard_logs():
    """Display dashboard logs in a tab"""
    st.subheader("Dashboard Logs (dashboard.log)")

    # Check multiple possible log file locations
    log_files = ["dashboard.log", "/var/log/job-tracker/dashboard.log", "/home/ubuntu/job-tracker/dashboard.log"]
    log_content = []

    for log_file in log_files:
        if os.path.exists(log_file):
            log_content.extend(read_log_content(log_file))

    if log_content:
        # Reverse the log content to show most recent logs first
        log_content.reverse()

        # Display logs in a fixed height read-only text area
        st.code("".join(log_content), language="text")
    else:
        st.warning("No dashboard log files found")

def _display_system_info():
    """Display system information in a tab"""
    st.subheader("System Information")

    # Get system info
    try:
        # Add a timestamp
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.caption(f"Last updated: {current_time}")

        # Get system information
        system_info = get_system_info()
        api_stats = get_api_stats()

        # Create columns for layout
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Server Resources")

            # CPU Usage
            if "cpu" in system_info and "used_percent" in system_info["cpu"]:
                cpu_usage = system_info["cpu"]["used_percent"]
                cores = f"{system_info['cpu'].get('count_physical', 0)} physical, {system_info['cpu'].get('count_logical', 0)} logical"
                st.metric("CPU Usage", f"{cpu_usage:.1f}%", f"{cores} cores")

            # Memory Usage
            if "memory" in system_info and "used_percent" in system_info["memory"]:
                memory_usage = system_info["memory"]["used_percent"]
                memory_total = system_info["memory"].get("total_mb", 0) / 1024  # Convert to GB
                memory_used = system_info["memory"].get("used_mb", 0) / 1024  # Convert to GB
                st.metric("Memory Usage", f"{memory_usage:.1f}%", f"{memory_used:.1f} GB of {memory_total:.1f} GB")

            # Disk Usage
            if "disk" in system_info and "root" in system_info["disk"]:
                disk_usage = system_info["disk"]["root"]["used_percent"]
                disk_total = system_info["disk"]["root"]["total_gb"]
                disk_used = system_info["disk"]["root"]["used_gb"]
                st.metric("Disk Usage", f"{disk_usage:.1f}%", f"{disk_used:.1f} GB of {disk_total:.1f} GB")

            # System Uptime
            if "uptime" in system_info and "uptime_formatted" in system_info["uptime"]:
                st.metric("System Uptime", system_info["uptime"]["uptime_formatted"])

            # Running Processes
            if "processes" in system_info:
                processes = system_info["processes"]
                process_count = processes.get("total_count", 0)

                # Count app-specific processes
                app_process_count = 0
                if "application_processes" in processes:
                    for proc_type, procs in processes["application_processes"].items():
                        app_process_count += len(procs)

                st.metric("Running Processes", f"{process_count}", f"{app_process_count} application processes")

            # Directory Structure
            if "project" in system_info:
                project = system_info["project"]

                # Show comprehensive directory information
                st.markdown("#### Directory Storage Analysis")

                # First, show root directory total storage
                if "size_mb" in project:
                    total_size_mb = project["size_mb"]
                    total_size_gb = total_size_mb / 1024 if total_size_mb else 0
                    st.metric("Total Project Storage", f"{total_size_gb:.2f} GB ({total_size_mb:.2f} MB)")

                # Combine folder and subfolder information with clearer presentation
                if "folder_sizes_mb" in project and "folders_by_size" in project:
                    # Create tabs for different views
                    storage_tabs = st.tabs(["Top-Level Directories", "Subdirectories", "All"])

                    # Prepare the data
                    top_folders = []
                    for folder, size in project["folders_by_size"]:
                        if folder != "root" and size > 0.1:  # Skip very small folders
                            percent = (size / total_size_mb * 100) if total_size_mb > 0 else 0
                            top_folders.append({
                                "Directory": folder,
                                "Size (MB)": size,
                                "Size (GB)": size / 1024,
                                "% of Total": f"{percent:.1f}%"
                            })

                    sub_folders = []
                    if "subfolder_sizes_mb" in project and "subfolders_by_size" in project:
                        for folder, size in project["subfolders_by_size"]:
                            if size > 0.1:  # Skip very small folders
                                percent = (size / total_size_mb * 100) if total_size_mb > 0 else 0
                                sub_folders.append({
                                    "Directory": folder,
                                    "Size (MB)": size,
                                    "Size (GB)": size / 1024,
                                    "% of Total": f"{percent:.1f}%"
                                })

                    # All folders combined
                    all_folders = top_folders + sub_folders

                    # Display in tabs
                    with storage_tabs[0]:
                        if top_folders:
                            # Create a dataframe
                            df_top = pd.DataFrame(top_folders)
                            st.dataframe(df_top, use_container_width=True)

                            # Add a bar chart for visual comparison
                            if len(top_folders) > 1:
                                st.bar_chart(df_top.set_index("Directory")["Size (MB)"])

                    with storage_tabs[1]:
                        if sub_folders:
                            # Create a dataframe
                            df_sub = pd.DataFrame(sub_folders)
                            st.dataframe(df_sub, use_container_width=True)

                    with storage_tabs[2]:
                        if all_folders:
                            # Create a dataframe
                            df_all = pd.DataFrame(all_folders)
                            st.dataframe(df_all, use_container_width=True)

        with col2:
            st.markdown("### Application Stats")

            # Database Stats
            if "database" in api_stats:
                db_stats = api_stats["database"]
                total_jobs = db_stats.get("total_jobs", 0)
                active_jobs = db_stats.get("active_jobs", 0)
                st.metric("Total Jobs", total_jobs)
                st.metric("Active Jobs", active_jobs)
                st.metric("Scrapers Registered", db_stats.get("registered_scrapers", 0))
                st.metric(
                    "Companies With Active Jobs",
                    db_stats.get("companies_active", 0),
                    f"{db_stats.get('companies', 0)} have any jobs in the database",
                    delta_color="off",
                )

                # Share of scrapers whose latest run returned jobs
                if "success_rate" in db_stats:
                    st.metric("Scrapers Working (latest run)", f"{db_stats['success_rate']:.1f}%")

            # Project Information
            if "project" in system_info:
                project_size = system_info["project"].get("size_mb", 0)
                file_count = system_info["project"].get("file_count", 0)

                st.metric("Project Size", f"{project_size:.1f} MB", f"{file_count} files")

                # Log files size
                log_size = 0
                log_count = 0

                if "logs_size_mb" in project:
                    log_size = project["logs_size_mb"]
                    log_count = project["logs_count"]

                if "main_log_files" in project:
                    for log_name, log_info in project["main_log_files"].items():
                        log_size += log_info["size_mb"]
                        log_count += 1

                st.metric("Log Files Size", f"{log_size:.1f} MB", f"{log_count} files")

            # Show running application processes
            if "processes" in system_info and "application_processes" in system_info["processes"]:
                app_processes = system_info["processes"]["application_processes"]

                st.markdown("#### Running Application Processes")

                # Convert to a list for display
                process_list = []
                for proc_type, processes in app_processes.items():
                    for proc in processes:
                        process_list.append({
                            "Type": proc_type,
                            "PID": proc["pid"],
                            "Memory (MB)": proc.get("memory_mb", 0),
                            "CPU (%)": proc.get("cpu_percent", 0)
                        })

                if process_list:
                    process_df = pd.DataFrame(process_list)
                    st.dataframe(process_df, use_container_width=True)
                else:
                    st.info("No application processes detected")

        # Detailed system information
        with st.expander("View Detailed System Information", expanded=False):
            formatted_info = format_system_info(system_info)
            st.text(formatted_info)

    except Exception as e:
        st.error(f"Error getting system information: {str(e)}")

STATUS_LABELS = {
    "success": "✅ Success",
    "partial": "⚠️ Partial",
    "empty": "➖ Empty",
    "failure": "❌ Failure",
    "interrupted": "⏹️ Interrupted",
    "running": "⏳ Running",
    "never_run": "⚪ Never run",
}


def _display_scraper_runs():
    """Latest run of every registered scraper, with what each status means."""
    st.subheader("Scraper Runs (latest run per scraper)")

    try:
        import requests
        from dashboard_components.utils import get_api_url

        response = requests.get(f"{get_api_url()}/stats/scraper-runs", timeout=30)
        if response.status_code != 200:
            st.error(f"Error fetching scraper runs data: {response.status_code}")
            return
        data = response.json()
        if data.get("error"):
            st.error(data["error"])
            return

        summary = data.get("summary", {})
        counts = summary.get("by_status", {})

        if summary.get("last_run"):
            st.caption(f"Last scraper finished: {summary['last_run'][:19].replace('T', ' ')} (server time)")

        row1 = st.columns(4)
        row1[0].metric("Scrapers Registered", summary.get("registered", 0))
        row1[1].metric("Have Run", summary.get("ran", 0))
        row1[2].metric("Working", summary.get("working", 0), "success + partial", delta_color="off")
        row1[3].metric("Working Rate", f"{summary.get('working_rate', 0):.1f}%")

        row2 = st.columns(6)
        for col, key in zip(row2, ("success", "partial", "empty", "failure", "interrupted", "never_run")):
            col.metric(STATUS_LABELS[key], counts.get(key, 0))

        with st.expander("What each status means", expanded=False):
            st.markdown(
                "- **Success**: returned jobs and printed no errors.\n"
                "- **Partial**: returned jobs, but some requests errored (e.g. one job page timed out).\n"
                "- **Empty**: ran cleanly but no postings matched the searched roles in the date window.\n"
                "- **Failure**: returned nothing *and* errored, or crashed: blocked, URL changed, API changed.\n"
                "- **Interrupted**: the process restarted while the scraper was running.\n"
                "- **Never run**: registered but no run recorded yet (new scrapers wait for the next scheduled cycle)."
            )

        scrapers = data.get("scrapers", [])
        if not scrapers:
            st.info("No scrapers registered.")
            return

        df = pd.DataFrame([
            {
                "Company": s["company"],
                "Scraper": s["scraper_name"],
                "Status": STATUS_LABELS.get(s["status"], s["status"]),
                "Added": s["jobs_added"] or 0,
                "Updated": s["jobs_updated"] or 0,
                "Finished": (s["end_time"] or "")[:19].replace("T", " "),
                "Details": (s["error_message"] or "").splitlines()[0] if s["error_message"] else "",
                "_status": s["status"],
            }
            for s in scrapers
        ])

        options = [STATUS_LABELS[k] for k in STATUS_LABELS if counts.get(k)]
        default = [STATUS_LABELS[k] for k in ("failure", "partial", "interrupted") if counts.get(k)]
        chosen = st.multiselect("Show statuses", options, default=default or options)
        view = df[df["Status"].isin(chosen)] if chosen else df
        st.dataframe(view.drop(columns=["_status"]), use_container_width=True, hide_index=True)

        problems = [s for s in scrapers if s["status"] in ("failure", "partial") and s["error_message"]]
        if problems:
            with st.expander(f"Error details ({len(problems)})", expanded=False):
                for s in problems:
                    st.markdown(f"**{s['company']}** (`{s['scraper_name']}`): {STATUS_LABELS[s['status']]}")
                    st.code(s["error_message"], language="text")

        all_time = summary.get("all_time", {})
        if all_time:
            st.caption(
                f"All-time runs: {summary.get('total_all_time', 0)} ("
                + ", ".join(f"{k}: {v}" for k, v in sorted(all_time.items()))
                + "). Runs recorded before this change were labelled 'success' whenever the scraper didn't crash."
            )

    except Exception as e:
        st.error(f"Error displaying scraper runs: {str(e)}")


def _display_scraper_output_preview():
    """Fetch all scrapers once and show sample JSON per module (no DB writes)."""
    st.subheader("Sample scraper output (JSON)")
    st.caption(
        "One run loads every `get_<name>_jobs` with the same role rules as the scheduler. "
        "Nothing is written to the database. "
        "Use a Max roles cap if loading all companies is too slow."
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        days_back = st.number_input("days", min_value=1, max_value=90, value=7, step=1)
    with c2:
        max_roles = st.number_input("Max roles (0 = all)", min_value=0, max_value=80, value=0, step=1)
    with c3:
        sample_jobs = st.number_input("Job dicts per scraper", min_value=1, max_value=20, value=5, step=1)

    st.caption("days / max roles apply the next time you fetch all. Changing job dict count updates display immediately.")

    btn_cols = st.columns(2)
    with btn_cols[0]:
        fetch_all = st.button("Fetch sample JSON for all scrapers", type="primary")
    with btn_cols[1]:
        if st.button("Clear cached previews"):
            st.session_state.pop("scraper_preview_cache", None)
            st.rerun()

    try:
        from app.scrapers import get_all_scrapers
        from app.scheduler.jobs import COMPANY_NAMES, resolve_roles_for_scraper, fetch_scraper_jobs_raw
        from app.dashboard.scraper_preview import build_sample_json

        scraper_names = sorted(get_all_scrapers().keys())
        if not scraper_names:
            st.info("No scrapers registered (check ENVIRONMENT / imports).")
            return

        if fetch_all:
            progress = st.progress(0.0)
            status = st.empty()
            new_cache = {}
            n = len(scraper_names)
            for idx, name in enumerate(scraper_names):
                status.text(f"Fetching {name} ({idx + 1} / {n})…")
                try:
                    roles = resolve_roles_for_scraper(name)
                    if max_roles > 0:
                        roles = roles[:max_roles]
                    data = fetch_scraper_jobs_raw(name, roles=roles, days_back=int(days_back))
                    new_cache[name] = {"data": data, "error": None}
                except Exception as e:
                    logger.exception("Scraper preview fetch failed for %s", name)
                    new_cache[name] = {"data": None, "error": str(e)}
                progress.progress((idx + 1) / n if n else 1.0)
            st.session_state["scraper_preview_cache"] = new_cache
            status.empty()
            progress.empty()
            st.success(f"Loaded samples for {n} scrapers.")

        cache = st.session_state.get("scraper_preview_cache") or {}

        if not cache:
            st.info('Click **Fetch sample JSON for all scrapers** to load every module.')
            return

        for name in scraper_names:
            label = COMPANY_NAMES.get(name, name)
            with st.expander(f"{label} (`{name}`)", expanded=False):
                entry = cache.get(name)
                if not entry:
                    st.caption("Missing from cache; run **Fetch sample JSON for all scrapers** again.")
                    continue
                if entry.get("error"):
                    st.error(entry["error"])
                    continue
                data = entry.get("data")
                if data is None:
                    continue
                st.code(build_sample_json(data, max_jobs=int(sample_jobs)), language="json")

    except Exception as e:
        logger.exception("Scraper output preview failed")
        st.error(f"Could not load scraper output preview: {e}")


def _tail_file(path, lines=1000):
    """Return the last `lines` lines of a log file, or raise with a clear reason.

    Reads directly first (on Ubuntu, /var/log/nginx and /var/log/postgresql are
    readable by the adm group). Falls back to passwordless sudo only when it
    exists, so a missing sudo binary no longer surfaces as an error.
    """
    import shutil
    import subprocess
    from collections import deque

    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return "".join(deque(f, maxlen=lines))
    except PermissionError:
        sudo = shutil.which("sudo") or ("/usr/bin/sudo" if os.path.exists("/usr/bin/sudo") else None)
        if not sudo:
            raise PermissionError(
                f"No read permission for {path}. Run `sudo usermod -aG adm ubuntu` on the server "
                "and restart the dashboard service."
            )
        result = subprocess.run(
            [sudo, "-n", "tail", "-n", str(lines), path], capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            raise PermissionError(
                f"No read permission for {path} and passwordless sudo is not allowed for tail. "
                "Run `sudo usermod -aG adm ubuntu` on the server and restart the dashboard service."
            )
        return result.stdout


def _display_nginx_logs():
    """Display Nginx logs in a tab"""
    st.subheader("Nginx Logs")

    log_type = st.radio("Select Nginx log type:", ["Error Log", "Access Log"], horizontal=True)
    log_file = "/var/log/nginx/error.log" if log_type == "Error Log" else "/var/log/nginx/access.log"

    if not os.path.exists(log_file):
        st.warning(f"Nginx log file {log_file} not found")
        return
    try:
        content = _tail_file(log_file)
        if content.strip():
            st.code(content, language="text")
        else:
            st.info(f"{log_file} is empty")
    except Exception as e:
        st.warning(str(e))


def _display_postgres_logs():
    """Display PostgreSQL logs in a tab"""
    st.subheader("PostgreSQL Logs")

    import glob
    log_paths = [
        "/var/log/postgresql/postgresql-*.log",  # Debian/Ubuntu
        "/var/lib/pgsql/data/log/*.log",         # RHEL/CentOS
        "/usr/local/var/postgres/server.log"     # macOS Homebrew
    ]
    all_logs = sorted({p for pattern in log_paths for p in glob.glob(pattern)})

    if not all_logs:
        st.warning("No PostgreSQL log files found at common locations")
        return

    selected_log = st.selectbox("Select PostgreSQL log file:", all_logs)
    try:
        content = _tail_file(selected_log)
        if content.strip():
            st.code(content, language="text")
        else:
            st.info(f"{selected_log} is empty")
    except Exception as e:
        st.warning(str(e))
