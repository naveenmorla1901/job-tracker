"""
Analytics debug routes for Streamlit
"""
import os
import streamlit as st
from pathlib import Path

def render_analytics_debug_page():
    """
    Renders the analytics debug page in Streamlit
    """
    st.title("Google Analytics Debug Page")
    
    # Get the path to the analytics_debug.html file
    static_dir = Path(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))) / "static"
    debug_file_path = static_dir / "analytics_debug.html"
    
    if debug_file_path.exists():
        # Load the HTML file
        with open(debug_file_path, "r") as f:
            html_content = f.read()
        
        # Create an iframe to render the HTML file
        iframe_height = 800
        st.markdown(
            f"""
            <iframe src="data:text/html;charset=utf-8,{html_content}" 
                    width="100%" height="{iframe_height}" 
                    style="border: 1px solid #ddd; border-radius: 5px;">
            </iframe>
            """,
            unsafe_allow_html=True
        )
        
        st.markdown("---")
        
        st.subheader("Google Analytics Troubleshooting")
        
        st.markdown("""
        ### Common Issues with Google Analytics
        
        1. **Not using HTTPS**: Google Analytics works best on secure (HTTPS) sites. Some browsers block tracking on non-secure sites.
        
        2. **Using IP Address instead of Domain**: Using a direct IP address instead of a proper domain name can affect tracking.
        
        3. **Content Security Policy (CSP)**: Check if your site has CSP headers that might be blocking Google Analytics scripts.
        
        4. **Ad Blockers**: Many ad blockers and privacy extensions block Google Analytics by default.
        
        5. **Cookies Disabled**: Google Analytics relies on cookies for tracking.
        
        ### Solutions
        
        1. **Set up HTTPS**: Follow the guide in `docs/ORACLE_HTTPS_SETUP.md` to configure HTTPS for your deployment.
        
        2. **Register a Domain**: Consider registering a domain name and pointing it to your Oracle Cloud instance.
        
        3. **Use Enhanced Transport**: The updated analytics code uses 'transport_url' and 'transport_type' to improve reliability.
        
        4. **Debug Mode**: The analytics implementation now includes debug mode for easier troubleshooting.
        
        5. **Test Events**: Use the test buttons above to verify if events are being sent successfully.
        """)
        
        st.markdown("### HTTPS Setup Guide")
        
        # Link to the HTTPS setup guide
        https_guide_path = Path(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))) / "docs" / "ORACLE_HTTPS_SETUP.md"
        
        if https_guide_path.exists():
            with open(https_guide_path, "r") as f:
                guide_content = f.read()
            
            with st.expander("View HTTPS Setup Guide"):
                st.markdown(guide_content)
    else:
        st.error(f"Could not find analytics debug file at {debug_file_path}")

def render_analytics_dashboard():
    """
    Renders the analytics dashboard in Streamlit
    """
    st.title("Google Analytics Dashboard")
    
    st.markdown("""
    This page provides tools to monitor and troubleshoot your Google Analytics implementation.
    
    ### Available Tools
    
    1. **Analytics Debug Page**: Use this to check if Google Analytics is properly configured
    2. **Test Events**: Send test events to verify tracking is working
    3. **HTTPS Setup Guide**: Instructions for setting up HTTPS on Oracle Cloud
    """)
    
    # Add buttons to navigate to different tools
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Analytics Debug Page"):
            st.session_state.analytics_page = "debug"
            st.rerun()
    
    with col2:
        if st.button("Test Events"):
            st.session_state.analytics_page = "test"
            st.rerun()
    
    with col3:
        if st.button("HTTPS Setup Guide"):
            st.session_state.analytics_page = "https_guide"
            st.rerun()
    
    # Initialize session state
    if "analytics_page" not in st.session_state:
        st.session_state.analytics_page = "dashboard"
    
    # Display the selected page
    if st.session_state.analytics_page == "debug":
        render_analytics_debug_page()
    elif st.session_state.analytics_page == "test":
        render_analytics_test_page()
    elif st.session_state.analytics_page == "https_guide":
        render_https_guide()

def render_analytics_test_page():
    """
    Renders a page to test Google Analytics events
    """
    st.subheader("Google Analytics Event Testing")
    
    st.markdown("""
    Use the buttons below to send test events to Google Analytics.
    Check your Google Analytics real-time events dashboard to verify they are being received.
    """)
    
    # Add JavaScript to send events when buttons are clicked
    st.markdown("""
    <script>
    function sendTestPageView() {
        if (typeof window.trackPageView === 'function') {
            window.trackPageView('Test Page View');
            return true;
        }
        return false;
    }
    
    function sendTestEvent() {
        if (typeof window.trackEvent === 'function') {
            window.trackEvent('Test', 'test_action', 'Test Label', null, {
                'test_property': 'test_value',
                'timestamp': new Date().toISOString()
            });
            return true;
        }
        return false;
    }
    </script>
    """, unsafe_allow_html=True)
    
    # Create buttons with on-click JavaScript
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <button 
            onclick="if(sendTestPageView()) { this.innerText = 'Page View Event Sent!'; this.style.backgroundColor = '#4CAF50'; } else { this.innerText = 'Error: Analytics Not Loaded'; this.style.backgroundColor = '#f44336'; }"
            style="background-color: #2196F3; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer;">
            Send Test Page View
        </button>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <button 
            onclick="if(sendTestEvent()) { this.innerText = 'Custom Event Sent!'; this.style.backgroundColor = '#4CAF50'; } else { this.innerText = 'Error: Analytics Not Loaded'; this.style.backgroundColor = '#f44336'; }"
            style="background-color: #2196F3; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer;">
            Send Test Custom Event
        </button>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown("""
    ### Check Real-time Events
    
    After sending test events, check your Google Analytics real-time events dashboard to verify they are being received:
    
    1. Log in to your Google Analytics account
    2. Navigate to "Reports" > "Realtime" > "Events"
    3. Look for events with the "Test" category
    
    If events are not showing up, check the following:
    
    - Make sure your Google Analytics tracking ID is correct (currently using G-EGVJQG5M34)
    - Check that you're looking at the correct Google Analytics property
    - Verify that HTTPS and other requirements are met
    """)

def render_https_guide():
    """
    Renders the HTTPS setup guide
    """
    st.subheader("HTTPS Setup Guide for Oracle Cloud")
    
    # Link to the HTTPS setup guide
    https_guide_path = Path(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))) / "docs" / "ORACLE_HTTPS_SETUP.md"
    
    if https_guide_path.exists():
        with open(https_guide_path, "r") as f:
            guide_content = f.read()
        
        st.markdown(guide_content)
    else:
        st.error(f"Could not find HTTPS setup guide at {https_guide_path}")
        
        # Provide a basic guide if the file doesn't exist
        st.markdown("""
        ## Setting up HTTPS for Oracle Cloud
        
        To set up HTTPS for your application:
        
        1. Register a domain name (you can use Freenom for a free domain)
        2. Point your domain to your Oracle Cloud instance's IP address
        3. Install and configure Nginx as a reverse proxy
        4. Use Let's Encrypt and Certbot to obtain a free SSL certificate
        5. Configure Nginx to use the SSL certificate
        
        For detailed instructions, please refer to the Oracle Cloud documentation.
        """)

# Main function to integrate with the dashboard
def display_analytics_page():
    """
    Main function to display analytics pages
    """
    render_analytics_dashboard()
