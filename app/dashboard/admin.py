# app/dashboard/admin.py
import os
import logging

import requests
import streamlit as st

from app.dashboard.auth import api_request, admin_required, get_current_user, get_token, logout

# Configure logging
logger = logging.getLogger("job_tracker.dashboard.admin")

ROLE_OPTIONS = ["regular", "premium", "admin"]


def _short_date(value):
    """'2026-10-02T21:15:38' -> '2026-10-02'; empty for missing values."""
    if not value:
        return "—"
    return str(value).split("T")[0]


def _confirm_key(user_id):
    return f"admin_confirm_delete_{user_id}"


def _apply_change(user, field, value, flash):
    """PUT one field once. A failed value is remembered so reruns don't retry it in a loop."""
    failed_key = f"admin_failed_{field}_{user['id']}"
    if st.session_state.get(failed_key) == value:
        return
    if api_request(f"auth/users/{user['id']}", method="PUT", data={field: value}):
        st.session_state.pop(failed_key, None)
        st.session_state["admin_flash"] = flash
        st.rerun()
    else:
        st.session_state[failed_key] = value


@admin_required
def admin_users_page():
    """Display and manage users (admin only)"""
    st.title("User Management")

    from dashboard_components.utils import check_api_status, get_api_url
    api_connected, api_status_msg = check_api_status()
    if not api_connected:
        st.error(api_status_msg)
        st.info("The API server should be running on port 8001. Try running: `python run.py api`")
        return

    token = get_token()
    if not token:
        st.error("No authentication token found. Please log out and back in.")
        if st.button("Go to Login Page"):
            st.session_state.page = 'login'
            st.rerun()
        return

    # Verify the token is still valid before showing anything editable
    try:
        me = requests.get(
            f"{get_api_url()}/auth/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        if me.status_code != 200:
            st.error("Your session has expired. Please log out and log back in.")
            if st.button("Logout"):
                logout()
                st.rerun()
            return
    except Exception as e:
        st.error(f"Error verifying authentication: {str(e)}")
        return

    users = api_request("auth/users")
    if users is None:
        st.error("Failed to fetch users from the API (see the API logs for details).")
        return

    # Flash message from the previous action survives the rerun
    flash = st.session_state.pop("admin_flash", None)
    if flash:
        st.success(flash)

    current_user = get_current_user()
    current_user_id = current_user.get("id") if current_user else None

    active_count = sum(1 for u in users if u.get("is_active", True))
    admin_count = sum(1 for u in users if u.get("role") == "admin")
    stats = st.columns(3)
    stats[0].metric("Users", len(users))
    stats[1].metric("Active", active_count)
    stats[2].metric("Admins", admin_count)

    css_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "static", "css", "compact.css",
    )
    if os.path.exists(css_path):
        with open(css_path, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

    widths = [3, 2, 1.5, 1.5, 1.5, 2]
    header = st.columns(widths)
    for col, label in zip(header, ["Email", "Role", "Active", "Registered", "Last login", "Actions"]):
        col.markdown(f"<b>{label}</b>", unsafe_allow_html=True)

    for user in sorted(users, key=lambda u: u["id"]):
        user_id = user["id"]
        is_self = user_id == current_user_id
        cols = st.columns(widths)

        cols[0].markdown(user["email"] + (" *(you)*" if is_self else ""))

        # Role: change takes effect when the selection changes; no extra button
        with cols[1]:
            current_role = user.get("role") if user.get("role") in ROLE_OPTIONS else "regular"
            new_role = st.selectbox(
                "Role", ROLE_OPTIONS, index=ROLE_OPTIONS.index(current_role),
                key=f"role_{user_id}", label_visibility="collapsed", disabled=is_self,
                help="You can't change your own role" if is_self else None,
            )
            if new_role != current_role:
                _apply_change(user, "role", new_role, f"{user['email']} is now {new_role}")

        # Active toggle: same pattern
        with cols[2]:
            is_active = bool(user.get("is_active", True))
            new_active = st.toggle(
                "Active", value=is_active, key=f"active_{user_id}",
                label_visibility="collapsed", disabled=is_self,
            ) if hasattr(st, "toggle") else st.checkbox(
                "Active", value=is_active, key=f"active_{user_id}",
                label_visibility="collapsed", disabled=is_self,
            )
            if new_active != is_active:
                state = "activated" if new_active else "deactivated"
                _apply_change(user, "is_active", new_active, f"{user['email']} {state}")

        cols[3].markdown(_short_date(user.get("registration_date")))
        cols[4].markdown(_short_date(user.get("last_login")))

        # Delete: two clicks, remembered in session_state across the rerun.
        # (A checkbox shown only after a button click never sees the click again.)
        with cols[5]:
            if is_self:
                st.markdown("—")
            elif st.session_state.get(_confirm_key(user_id)):
                yes, no = st.columns(2)
                if yes.button("Confirm", key=f"confirm_{user_id}", type="primary"):
                    st.session_state.pop(_confirm_key(user_id), None)
                    if api_request(f"auth/users/{user_id}", method="DELETE"):
                        st.session_state["admin_flash"] = f"Deleted {user['email']}"
                    st.rerun()
                if no.button("Cancel", key=f"cancel_{user_id}"):
                    st.session_state.pop(_confirm_key(user_id), None)
                    st.rerun()
            elif st.button("Delete", key=f"delete_{user_id}"):
                st.session_state[_confirm_key(user_id)] = True
                st.rerun()

    st.markdown("---")
    st.subheader("Create New User")
    with st.form("create_user_form", clear_on_submit=True):
        new_email = st.text_input("Email")
        new_password = st.text_input("Password", type="password")
        new_role = st.selectbox("Role", ROLE_OPTIONS)

        if st.form_submit_button("Create User"):
            if not new_email or not new_password:
                st.error("Email and password are required")
            elif len(new_password) < 8:
                st.error("Password must be at least 8 characters")
            else:
                created = api_request(
                    "auth/register", method="POST",
                    data={"email": new_email, "password": new_password},
                )
                if created and "id" in created:
                    message = f"Created {new_email}"
                    if new_role != "regular":
                        if api_request(f"auth/users/{created['id']}", method="PUT", data={"role": new_role}):
                            message += f" as {new_role}"
                        else:
                            message += " (role could not be set; still regular)"
                    st.session_state["admin_flash"] = message
                    st.rerun()
