"""
Custom API endpoints for the dashboard to interact with the API from Streamlit instead of JavaScript
"""
import streamlit as st
from app.dashboard.auth import api_request, is_authenticated

def init_endpoints():
    """Initialize the custom endpoints for tracking jobs"""
    st.set_page_config(page_title="Job Tracker API Endpoint", page_icon="🔄")
    
    if "endpoint" not in st.query_params:
        st.error("No endpoint specified")
        return
    
    endpoint = st.query_params.get("endpoint")
    
    if not is_authenticated():
        st.json({"error": "Not authenticated"})
        return
    
    if endpoint == "track_job":
        handle_track_job()
    elif endpoint == "mark_job_applied":
        handle_mark_job_applied()
    else:
        st.json({"error": f"Unknown endpoint: {endpoint}"})

def handle_track_job():
    """Handle tracking a job"""
    try:
        # Get job_id from form data or query params
        if st.query_params.get("job_id"):
            job_id = st.query_params.get("job_id") 
        else:
            data = st.experimental_get_query_params()
            job_id = data.get("job_id", [""])[0]
        
        if not job_id:
            st.json({"error": "Missing job_id parameter"})
            return
        
        # Track the job using the API
        result = api_request(f"user/jobs/{job_id}/track", method="POST")
        
        # Return the result
        st.json({"success": True, "message": "Job tracked successfully", "job_id": job_id})
    except Exception as e:
        st.json({"error": str(e)})

def handle_mark_job_applied():
    """Handle marking a job as applied"""
    try:
        # Get parameters from form data or query params
        if st.query_params.get("job_id") and "applied" in st.query_params:
            job_id = st.query_params.get("job_id")
            applied = st.query_params.get("applied").lower() == "true"
        else:
            data = st.experimental_get_query_params()
            job_id = data.get("job_id", [""])[0]
            applied_str = data.get("applied", ["false"])[0]
            applied = applied_str.lower() == "true"
        
        if not job_id:
            st.json({"error": "Missing job_id parameter"})
            return
        
        # Mark the job as applied using the API
        result = api_request(
            f"user/jobs/{job_id}/applied", 
            method="PUT",
            data={"applied": applied}
        )
        
        # Return the result
        status = "applied" if applied else "not applied"
        st.json({
            "success": True, 
            "message": f"Job marked as {status} successfully", 
            "job_id": job_id, 
            "applied": applied
        })
    except Exception as e:
        st.json({"error": str(e)})

if __name__ == "__main__":
    init_endpoints()
