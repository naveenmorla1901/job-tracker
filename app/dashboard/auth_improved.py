# app/dashboard/auth.py
import streamlit as st
import requests
import json
from typing import Optional, Dict, Any, Union
from datetime import datetime
import logging
import os

# Configure logging
logger = logging.getLogger("job_tracker.dashboard.auth")

# Get API URL from environment or default
def get_api_url():
    api_url = os.environ.get("JOB_TRACKER_API_URL", "http://localhost:8001/api")
    if api_url.endswith('/'):
        api_url = api_url[:-1]
    return api_url

# Constants
API_URL = get_api_url()

def get_auth_status():
    """Get the current authentication status from session state."""
    if "auth_status" not in st.session_state:
        st.session_state.auth_status = {
            "is_authenticated": False,
            "user": None,
            "token": None
        }
    return st.session_state.auth_status

def get_token() -> Optional[str]:
    """Get the current authentication token if it exists."""
    auth_status = get_auth_status()
    return auth_status.get("token")

def get_current_user() -> Optional[Dict[str, Any]]:
    """Get the current authenticated user if it exists."""
    auth_status = get_auth_status()
    return auth_status.get("user")

def is_authenticated() -> bool:
    """Check if the user is authenticated."""
    auth_status = get_auth_status()
    return auth_status.get("is_authenticated", False)

def is_admin() -> bool:
    """Check if the current user is an admin."""
    user = get_current_user()
    if not user:
        return False
    return user.get("role") == "admin"

def login(email: str, password: str) -> bool:
    """
    Authenticate a user with the API.
    """
    try:
        api_url = get_api_url()
        # Make API request to login
        response = requests.post(
            f"{api_url}/auth/login/json",
            json={"email": email, "password": password}
        )
        
        logger.info(f"Login attempt: {email}, status: {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"Login failed: {response.text}")
            return False
        
        # Parse response
        data = response.json()
        token = data.get("access_token")
        
        if not token:
            logger.error("No token in response")
            return False
            
        # Get user info
        user_response = requests.get(
            f"{api_url}/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if user_response.status_code != 200:
            logger.error(f"Error getting user info: {user_response.text}")
            return False
            
        user_data = user_response.json()
        
        # Update session state
        st.session_state.auth_status = {
            "is_authenticated": True,
            "user": user_data,
            "token": token
        }
        
        # Store token in session cookie for JavaScript to access
        # This is used by the JavaScript to make authenticated API calls
        st.markdown(
            f"""
            <script>
            // Store authentication token for API calls
            localStorage.setItem('job_tracker_token', '{token}');
            console.log('Authentication token stored in localStorage');
            </script>
            """,
            unsafe_allow_html=True
        )
        
        logger.info(f"User authenticated: {user_data.get('email')}")
        return True
        
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return False

def logout():
    """Log the user out by clearing the session state."""
    if "auth_status" in st.session_state:
        user_email = None
        if st.session_state.auth_status.get("user"):
            user_email = st.session_state.auth_status.get("user").get("email")
            
        st.session_state.auth_status = {
            "is_authenticated": False,
            "user": None,
            "token": None
        }
        
        # Clear token from localStorage
        st.markdown(
            """
            <script>
            // Clear authentication token on logout
            localStorage.removeItem('job_tracker_token');
            console.log('Authentication token removed from localStorage');
            </script>
            """,
            unsafe_allow_html=True
        )
        
        if user_email:
            logger.info(f"User logged out: {user_email}")

def register(email: str, password: str) -> bool:
    """
    Register a new user with the API.
    
    Args:
        email: User's email
        password: User's password
        
    Returns:
        True if registration was successful, False otherwise
    """
    try:
        api_url = get_api_url()
        # Make API request to register
        response = requests.post(
            f"{api_url}/auth/register",
            json={"email": email, "password": password}
        )
        
        if response.status_code != 201:
            error_msg = "Unknown error"
            try:
                error_data = response.json()
                if isinstance(error_data, dict) and "detail" in error_data:
                    error_msg = error_data["detail"]
            except:
                pass
            logger.error(f"Registration failed: {error_msg}")
            return False
        
        logger.info(f"User registered: {email}")
        return True
        
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return False

def change_password(current_password: str, new_password: str) -> bool:
    """
    Change the current user's password.
    
    Args:
        current_password: Current password for verification
        new_password: New password to set
        
    Returns:
        True if password change was successful, False otherwise
    """
    if not is_authenticated():
        return False
        
    token = get_token()
    if not token:
        return False
    
    api_url = get_api_url()
    try:
        # First verify current password
        verify_response = requests.post(
            f"{api_url}/auth/login/json",
            json={
                "email": get_current_user().get("email"),
                "password": current_password
            }
        )
        
        if verify_response.status_code != 200:
            logger.error("Current password is incorrect")
            return False
            
        # Change password
        response = requests.put(
            f"{api_url}/auth/me",
            headers={"Authorization": f"Bearer {token}"},
            json={"password": new_password}
        )
        
        if response.status_code != 200:
            error_msg = "Unknown error"
            try:
                error_data = response.json()
                if isinstance(error_data, dict) and "detail" in error_data:
                    error_msg = error_data["detail"]
            except:
                pass
            logger.error(f"Password change failed: {error_msg}")
            return False
            
        logger.info(f"Password changed for user: {get_current_user().get('email')}")
        return True
        
    except Exception as e:
        logger.error(f"Password change error: {str(e)}")
        return False

def api_request(endpoint: str, method: str = "GET", data: Dict = None, params: Dict = None) -> Any:
    """
    Make an authenticated API request.
    
    Args:
        endpoint: API endpoint (without base URL)
        method: HTTP method (GET, POST, PUT, DELETE)
        data: Request body data (for POST/PUT)
        params: Query parameters
        
    Returns:
        Response data if successful, None otherwise
    """
    api_url = get_api_url()
    
    if not is_authenticated():
        logger.error(f"API request failed: User not authenticated")
        return None
        
    token = get_token()
    if not token:
        logger.error(f"API request failed: No token available")
        return None
        
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    url = f"{api_url}/{endpoint.lstrip('/')}"
    
    try:
        logger.info(f"Making {method} request to {url}")
        logger.info(f"Data: {data}")
        
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, params=params)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, json=data, params=params)
        elif method.upper() == "PUT":
            # Make sure boolean values are properly serialized
            if isinstance(data, dict) and "applied" in data:
                # Log the exact value being sent
                logger.info(f"Sending applied value: {data['applied']} (type: {type(data['applied']).__name__})")
                # Convert to string if needed
                if isinstance(data["applied"], bool):
                    data["applied"] = data["applied"]  # Make sure it's a proper boolean
            
            response = requests.put(url, headers=headers, json=data, params=params)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers, params=params)
        else:
            logger.error(f"Invalid method: {method}")
            return None
            
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response text: {response.text}")
        
        if response.status_code not in (200, 201, 204):
            logger.error(f"API request failed: {response.status_code} - {response.text}")
            return None
            
        if response.status_code == 204:
            return {}
            
        if response.text:
            try:
                return response.json()
            except:
                return {"text": response.text}
        return {}
        
    except Exception as e:
        logger.error(f"API request error: {str(e)}")
        return None

def auth_required(func):
    """
    Decorator to require authentication for a Streamlit page.
    If user is not authenticated, redirects to login page.
    """
    def wrapper(*args, **kwargs):
        if not is_authenticated():
            st.error("Please log in to access this page")
            login_page()
            return
        return func(*args, **kwargs)
    return wrapper

def admin_required(func):
    """
    Decorator to require admin privileges for a Streamlit page.
    If user is not an admin, shows error message.
    """
    def wrapper(*args, **kwargs):
        if not is_authenticated():
            st.error("Please log in to access this page")
            login_page()
            return
        if not is_admin():
            st.error("You do not have permission to access this page")
            return
        return func(*args, **kwargs)
    return wrapper

def login_page():
    """Show login form and handle login/registration"""
    st.title("Login")
    
    # Initialize tab state if not already set
    if 'active_tab' not in st.session_state:
        st.session_state.active_tab = "login"
        
    # Create tabs for login and registration
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    # Login tab
    with tab1:
        login_form = st.form("login_form")
        email = login_form.text_input("Email")
        password = login_form.text_input("Password", type="password")
        submit = login_form.form_submit_button("Login")
        
        if submit:
            if login(email, password):
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Login failed. Please check your email and password.")
    
    # Registration tab
    with tab2:
        register_form = st.form("register_form")
        new_email = register_form.text_input("Email")
        new_password = register_form.text_input("Password", type="password")
        confirm_password = register_form.text_input("Confirm Password", type="password")
        register_submit = register_form.form_submit_button("Register")
        
        if register_submit:
            if new_password != confirm_password:
                st.error("Passwords do not match")
            elif len(new_password) < 8:
                st.error("Password must be at least 8 characters long")
            else:
                if register(new_email, new_password):
                    st.success("Registration successful! Please log in.")
                    # Switch to login tab
                    st.session_state.active_tab = "login"
                    st.rerun()

def user_settings_page():
    """Show user settings page"""
    st.title("User Settings")
    
    if not is_authenticated():
        st.error("Please log in to access this page")
        return
    
    user = get_current_user()
    
    st.write(f"Email: {user.get('email')}")
    st.write(f"Role: {user.get('role')}")
    st.write(f"Registered: {user.get('registration_date')}")
    
    # Change password form
    st.subheader("Change Password")
    
    change_pwd_form = st.form("change_password_form")
    current_pwd = change_pwd_form.text_input("Current Password", type="password")
    new_pwd = change_pwd_form.text_input("New Password", type="password")
    confirm_pwd = change_pwd_form.text_input("Confirm New Password", type="password")
    submit = change_pwd_form.form_submit_button("Change Password")
    
    if submit:
        if new_pwd != confirm_pwd:
            st.error("New passwords do not match")
        elif len(new_pwd) < 8:
            st.error("Password must be at least 8 characters long")
        else:
            if change_password(current_pwd, new_pwd):
                st.success("Password changed successfully")
            else:
                st.error("Failed to change password")

def user_menu():
    """Display user menu in the sidebar"""
    if is_authenticated():
        user = get_current_user()
        st.sidebar.write(f"Logged in as: {user.get('email')}")
        
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("Settings"):
                st.session_state.page = "settings"
                st.rerun()
        with col2:
            if st.button("Logout"):
                logout()
                st.rerun()
                
        # Admin section
        if is_admin():
            st.sidebar.markdown("---")
            st.sidebar.markdown("### Admin")
            if st.sidebar.button("User Management"):
                st.session_state.page = "admin_users"
                st.rerun()
            if st.sidebar.button("System Logs"):
                st.session_state.page = "system_logs"
                st.rerun()
