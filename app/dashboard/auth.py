# app/dashboard/auth.py
import streamlit as st
import requests
import json
import os
import time
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import logging
import uuid
import hashlib

# Configure logging
logger = logging.getLogger("job_tracker.dashboard.auth")

# Store session data in file for persistence
def get_session_storage_path():
    """Get the path to the session storage file"""
    import os
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    storage_dir = os.path.join(base_dir, 'data')
    
    # Ensure directory exists
    os.makedirs(storage_dir, exist_ok=True)
    
    return os.path.join(storage_dir, 'sessions.json')

def save_session_data(session_id, token, user_data, expiry):
    """Save session data to file for persistence"""
    try:
        import json
        import os
        
        # Load existing sessions
        sessions = {}
        storage_path = get_session_storage_path()
        
        if os.path.exists(storage_path):
            try:
                with open(storage_path, 'r') as f:
                    sessions = json.load(f)
            except:
                # If file is corrupted, start fresh
                sessions = {}
        
        # Add or update the session
        sessions[session_id] = {
            'token': hash_token(token),
            'user': user_data,
            'expiry': expiry
        }
        
        # Save back to file
        with open(storage_path, 'w') as f:
            json.dump(sessions, f)
            
        logger.info(f"Saved session data for user: {user_data.get('email')}")
        return True
    except Exception as e:
        logger.error(f"Error saving session data: {e}")
        return False

def load_session_data():
    """Load all session data from file"""
    try:
        import json
        import os
        
        storage_path = get_session_storage_path()
        
        if os.path.exists(storage_path):
            with open(storage_path, 'r') as f:
                return json.load(f)
        return {}
    except Exception as e:
        logger.error(f"Error loading session data: {e}")
        return {}

def remove_session_data(session_id):
    """Remove a session from the storage file"""
    try:
        import json
        import os
        
        storage_path = get_session_storage_path()
        
        if os.path.exists(storage_path):
            # Load existing sessions
            with open(storage_path, 'r') as f:
                sessions = json.load(f)
            
            # Remove the session if it exists
            if session_id in sessions:
                del sessions[session_id]
                
                # Save back to file
                with open(storage_path, 'w') as f:
                    json.dump(sessions, f)
                    
                logger.info(f"Removed session data for session ID: {session_id}")
                return True
        return False
    except Exception as e:
        logger.error(f"Error removing session data: {e}")
        return False

# Add functions for persistent login
def generate_session_id():
    """Generate a unique session ID"""
    return str(uuid.uuid4())

def get_session_cookie_key():
    """Get the key for storing the session cookie"""
    return "job_tracker_session"

def hash_token(token):
    """Create a hash of the token for more secure storage"""
    return hashlib.sha256(token.encode()).hexdigest()
    
def set_auth_cookie(token, user_data):
    """Set a cookie with authentication data"""
    session_id = generate_session_id()
    expiry = datetime.utcnow() + timedelta(days=7)  # Cookie expires in 7 days
    
    # Store in session state to prevent logout on refresh
    if "persistent_auth" not in st.session_state:
        st.session_state.persistent_auth = {}
    
    # Store session info in session state
    st.session_state.persistent_auth[session_id] = {
        "token": hash_token(token),
        "user": user_data,
        "expiry": expiry.timestamp()
    }
    
    # Save to persistent storage
    save_session_data(session_id, token, user_data, expiry.timestamp())
    
    # Create cookie via JavaScript
    js_code = f"""
    <script>
    // Set authentication cookie
    document.cookie = "{get_session_cookie_key()}={session_id}; path=/; expires={expiry.strftime('%a, %d %b %Y %H:%M:%S GMT')}; SameSite=Lax";
    console.log('Auth cookie set');
    
    // Store token in localStorage for API calls
    localStorage.setItem('job_tracker_token', '{token}');
    localStorage.setItem('job_tracker_session_id', '{session_id}');
    console.log('Authentication data stored in localStorage');
    </script>
    """
    
    # Inject the JavaScript
    st.markdown(js_code, unsafe_allow_html=True)
    logger.info(f"Authentication cookie set for user: {user_data.get('email')}")
    return session_id

def clear_auth_cookie():
    """Clear the authentication cookie"""
    js_code = f"""
    <script>
    // Clear auth cookie
    document.cookie = "{get_session_cookie_key()}=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT; SameSite=Lax";
    console.log('Auth cookie cleared');
    
    // Clear token from localStorage
    localStorage.removeItem('job_tracker_token');
    localStorage.removeItem('job_tracker_session_id');
    console.log('Authentication data removed from localStorage');
    </script>
    """
    
    st.markdown(js_code, unsafe_allow_html=True)
    logger.info("Authentication cookie cleared")

def check_for_auth_cookie():
    """Check for a valid authentication cookie and restore session if found"""
    # Add JavaScript to check for cookie and report back
    js_code = f"""
    <script>
    // Function to get cookie value by name
    function getCookie(name) {{
        const value = `; ${{document.cookie}}`;
        const parts = value.split(`; ${{name}}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    }}
    
    // Check for auth cookie
    const sessionId = getCookie('{get_session_cookie_key()}');
    
    // If we have a session ID, store it in localStorage for simple retrieval
    if (sessionId) {{
        localStorage.setItem('current_session_id', sessionId);
        console.log('Found existing session:', sessionId);
    }}
    
    // Set a flag to indicate we've checked for cookies
    localStorage.setItem('cookie_check_complete', 'true');
    </script>
    """
    
    # Inject the JavaScript to check for cookies
    st.markdown(js_code, unsafe_allow_html=True)
    
    # If we're already authenticated in session state, we're done
    if is_authenticated():
        return True
    
    # Get sessions from file storage
    sessions = load_session_data()
    
    # First check session state for sessions
    if "persistent_auth" not in st.session_state or not st.session_state.persistent_auth:
        # If not in session state, load from file
        st.session_state.persistent_auth = sessions
    
    if sessions:
        # Find the most recent valid session
        current_time = datetime.utcnow().timestamp()
        valid_sessions = [
            (sid, data) for sid, data in sessions.items()
            if data.get("expiry", 0) > current_time and "user" in data
        ]
        
        # Sort by expiry time descending (most recent first)
        valid_sessions.sort(key=lambda x: x[1].get("expiry", 0), reverse=True)
        
        if valid_sessions:
            # Use the most recent session
            session_id, session_data = valid_sessions[0]
            
            # Restore the session
            st.session_state.auth_status = {
                "is_authenticated": True,
                "user": session_data["user"],
                "token": session_data["token"]  # This is a hash, not the actual token
            }
            logger.info(f"Restored session for user: {session_data['user'].get('email')}")
            return True
    
    return False

# Import get_api_url from dashboard_components.utils
from dashboard_components.utils import get_api_url

def get_auth_status():
    """Get the current authentication status from session state."""
    if not hasattr(st.session_state, "auth_status"):
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
        # Get current API URL
        api_url = get_api_url()
        
        # Make API request to login
        logger.info(f"Attempting to login at: {api_url}/auth/login/json")
        st.write(f"Trying to connect to: {api_url}/auth/login/json")
        response = requests.post(
            f"{api_url}/auth/login/json",
            json={"email": email, "password": password}
        )
        
        st.write(f"Status code: {response.status_code}")
        
        if response.status_code != 200:
            st.write(f"Error response: {response.text}")
            return False
        
        # Parse response
        data = response.json()
        token = data.get("access_token")
        
        if not token:
            st.write("No token in response")
            return False
            
        # Get user info
        user_response = requests.get(
            f"{api_url}/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        st.write(f"User info status: {user_response.status_code}")
        
        if user_response.status_code != 200:
            st.write(f"Error getting user info: {user_response.text}")
            return False
            
        user_data = user_response.json()
        
        # Update session state
        st.session_state.auth_status = {
            "is_authenticated": True,
            "user": user_data,
            "token": token
        }
        
        # Set persistent login cookie
        set_auth_cookie(token, user_data)
        
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
        st.write(f"Login error: {str(e)}")
        logger.error(f"Login error: {str(e)}")
        return False

def logout():
    """Log the user out by clearing the session state."""
    if hasattr(st.session_state, "auth_status"):
        user_email = None
        if st.session_state.auth_status.get("user"):
            user_email = st.session_state.auth_status.get("user").get("email")
            
        # Get the session ID from localStorage
        js_code = """
        <script>
        // Get the current session ID
        const sessionId = localStorage.getItem('job_tracker_session_id');
        if (sessionId) {
            // Store it in sessionStorage for retrieval
            sessionStorage.setItem('logout_session_id', sessionId);
        }
        </script>
        """
        st.markdown(js_code, unsafe_allow_html=True)
        
        # For any session IDs in persistent_auth, try to remove them
        if "persistent_auth" in st.session_state:
            # Get existing session data
            sessions = load_session_data()
            
            # Remove all sessions for this user
            for session_id, session_data in list(sessions.items()):
                if session_data.get("user", {}).get("email") == user_email:
                    remove_session_data(session_id)
            
            # Clear the session state
            st.session_state.persistent_auth = {}
        
        # Reset auth status
        st.session_state.auth_status = {
            "is_authenticated": False,
            "user": None,
            "token": None
        }
        
        # Clear auth cookie
        clear_auth_cookie()
        
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
        # Get current API URL
        api_url = get_api_url()
        
        # Make API request to register
        response = requests.post(
            f"{api_url}/auth/register",
            json={"email": email, "password": password}
        )
        
        if response.status_code != 201:
            st.error(f"Registration failed: {response.json().get('detail', 'Unknown error')}")
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
        
    try:
        # Get current API URL
        api_url = get_api_url()
        
        # First verify current password
        verify_response = requests.post(
            f"{api_url}/auth/login/json",
            json={
                "email": get_current_user().get("email"),
                "password": current_password
            }
        )
        
        if verify_response.status_code != 200:
            st.error("Current password is incorrect")
            return False
            
        # Change password
        response = requests.put(
            f"{api_url}/auth/me",
            headers={"Authorization": f"Bearer {token}"},
            json={"password": new_password}
        )
        
        if response.status_code != 200:
            st.error(f"Password change failed: {response.json().get('detail', 'Unknown error')}")
            return False
            
        logger.info(f"Password changed for user: {get_current_user().get('email')}")
        return True
        
    except Exception as e:
        logger.error(f"Password change error: {str(e)}")
        return False

def api_request(endpoint: str, method: str = "GET", data: Dict = None, params: Dict = None) -> Optional[Dict]:
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
    if not is_authenticated():
        logger.error(f"API request failed: User not authenticated")
        return None
        
    token = get_token()
    if not token:
        logger.error(f"API request failed: No token available")
        return None
        
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get current API URL
    api_url = get_api_url()
    url = f"{api_url}/{endpoint.lstrip('/')}"
    
    try:
        logger.info(f"Making {method} request to {url}")
        if method.upper() == "GET":
            response = requests.get(url, headers=headers, params=params)
        elif method.upper() == "POST":
            response = requests.post(url, headers=headers, json=data, params=params)
        elif method.upper() == "PUT":
            response = requests.put(url, headers=headers, json=data, params=params)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers, params=params)
        else:
            logger.error(f"Invalid method: {method}")
            return None
            
        logger.info(f"Response status: {response.status_code}")
        if response.status_code not in (200, 201, 204):
            logger.error(f"API request failed: {response.status_code} - {response.text}")
            return None
            
        if response.status_code == 204:
            return {}
            
        return response.json()
        
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
                st.error("Make sure the API service is running on port 8001.")
    
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
