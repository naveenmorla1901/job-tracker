import streamlit as st
import requests

st.title("API Connection Test")

# Try different API URLs
urls = [
    "http://localhost:8000/api",
    "http://127.0.0.1:8000/api",
    "http://170.9.227.112:8000/api",  # Replace with your actual IP
]

for url in urls:
    st.write(f"## Testing: {url}")
    try:
        response = requests.get(f"{url}/health", timeout=5)
        st.write(f"Status: {response.status_code}")
        st.write(f"Response: {response.json()}")
        st.success(f"✅ Connected to {url}")
    except Exception as e:
        st.error(f"❌ Failed to connect to {url}: {str(e)}")