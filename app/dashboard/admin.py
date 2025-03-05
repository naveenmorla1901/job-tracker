# app/dashboard/admin.py
import streamlit as st
import pandas as pd
from datetime import datetime
import logging

from app.dashboard.auth import api_request, admin_required, get_current_user

# Configure logging
logger = logging.getLogger("job_tracker.dashboard.admin")

@admin_required
def admin_users_page():
    """Display and manage users (admin only)"""
    st.title("User Management")
    
    # Fetch users
    users = api_request("auth/users")
    if not users:
        st.error("Failed to fetch user data")
        return
    
    # Create DataFrame for display
    df = pd.DataFrame(users)
    
    # Display user count
    st.subheader(f"All Users ({len(df)})")
    
    # Create user management table
    st.markdown("""
    <style>
    .user-table {
        width: 100%;
        margin-bottom: 20px;
    }
    .user-table th, .user-table td {
        padding: 8px;
        text-align: left;
        border-bottom: 1px solid #ddd;
    }
    .user-table th {
        background-color: #1E1E1E;
        color: white;
    }
    .user-table tr:hover {
        background-color: rgba(200, 200, 200, 0.2);
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Display users in a table
    cols = st.columns([3, 2, 2, 2, 2])
    cols[0].markdown("<b>Email</b>", unsafe_allow_html=True)
    cols[1].markdown("<b>Role</b>", unsafe_allow_html=True)
    cols[2].markdown("<b>Status</b>", unsafe_allow_html=True)
    cols[3].markdown("<b>Registered</b>", unsafe_allow_html=True)
    cols[4].markdown("<b>Actions</b>", unsafe_allow_html=True)
    
    current_user = get_current_user()
    current_user_id = current_user.get("id") if current_user else None
    
    for _, user in df.iterrows():
        user_id = user["id"]
        cols = st.columns([3, 2, 2, 2, 2])
        
        # Email
        cols[0].markdown(f"{user['email']}")
        
        # Role
        with cols[1]:
            role_options = ["regular", "premium", "admin"]
            role_index = role_options.index(user["role"]) if user["role"] in role_options else 0
            new_role = st.selectbox(
                "Role", 
                role_options, 
                index=role_index,
                key=f"role_{user_id}",
                label_visibility="collapsed"
            )
            if new_role != user["role"]:
                if st.button("Update Role", key=f"update_role_{user_id}", help="Update user role"):
                    if api_request(
                        f"auth/users/{user_id}", 
                        method="PUT", 
                        data={"role": new_role}
                    ):
                        st.success("Role updated")
                        st.rerun()
                    else:
                        st.error("Failed to update role")
        
        # Status
        with cols[2]:
            is_active = user.get("is_active", True)
            status_text = "Active" if is_active else "Inactive"
            new_status = st.checkbox(
                status_text, 
                value=is_active, 
                key=f"status_{user_id}",
                help="Toggle user active status"
            )
            if new_status != is_active:
                if st.button("Update Status", key=f"update_status_{user_id}", help="Update user status"):
                    if api_request(
                        f"auth/users/{user_id}", 
                        method="PUT", 
                        data={"is_active": new_status}
                    ):
                        st.success("Status updated")
                        st.rerun()
                    else:
                        st.error("Failed to update status")
        
        # Registration date
        reg_date = user.get("registration_date", "")
        if reg_date:
            try:
                if isinstance(reg_date, str):
                    reg_date = reg_date.split("T")[0]
                else:
                    reg_date = reg_date.strftime("%Y-%m-%d")
            except:
                pass
        cols[3].markdown(f"{reg_date}")
        
        # Actions
        with cols[4]:
            # Don't allow deleting yourself
            if user_id != current_user_id:
                delete_btn = st.button("Delete", key=f"delete_{user_id}", help="Delete this user")
                if delete_btn:
                    confirm = st.checkbox("Confirm deletion", key=f"confirm_{user_id}")
                    if confirm:
                        if api_request(f"auth/users/{user_id}", method="DELETE"):
                            st.success("User deleted")
                            st.rerun()
                        else:
                            st.error("Failed to delete user")
            else:
                st.markdown("*Current user*")
        
        st.markdown("---")
    
    # Add a section to create a new user
    st.subheader("Create New User")
    with st.form("create_user_form"):
        new_email = st.text_input("Email")
        new_password = st.text_input("Password", type="password")
        new_role = st.selectbox("Role", ["regular", "premium", "admin"])
        
        submitted = st.form_submit_button("Create User")
        if submitted:
            if not new_email or not new_password:
                st.error("Email and password are required")
            elif len(new_password) < 8:
                st.error("Password must be at least 8 characters")
            else:
                # Call registration endpoint
                response = api_request(
                    "auth/register", 
                    method="POST", 
                    data={"email": new_email, "password": new_password}
                )
                
                if response and "id" in response:
                    # Set role if different from default
                    if new_role != "regular":
                        role_update = api_request(
                            f"auth/users/{response['id']}", 
                            method="PUT", 
                            data={"role": new_role}
                        )
                        if not role_update:
                            st.warning("User created but failed to set role")
                    
                    st.success("User created successfully")
                    st.rerun()
                else:
                    st.error("Failed to create user")
