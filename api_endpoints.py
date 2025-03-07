"""
Entry point for API endpoints from the dashboard
"""
import streamlit as st
from app.dashboard.api_endpoints import init_endpoints

# Entry point for Streamlit
init_endpoints()
