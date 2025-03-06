"""
Custom jobs table component for the dashboard - fixes spacing and checkbox issues
"""
import streamlit as st
import pandas as pd
from dashboard_components.utils import format_job_date, get_api_url
from app.dashboard.auth import is_authenticated, api_request

def display_custom_jobs_table(df_jobs):
    """A clean, simplified implementation of the jobs table with proper checkbox handling"""
    
    # Get user's tracked jobs if authenticated
    tracked_jobs = {}
    if is_authenticated():
        try:
            user_jobs = api_request("user/jobs") or []
            if isinstance(user_jobs, list):
                for job in user_jobs:
                    if job and isinstance(job, dict) and 'id' in job:
                        job_id = job['id']
                        is_applied = job.get('tracking', {}).get('is_applied', False)
                        tracked_jobs[str(job_id)] = is_applied
        except Exception as e:
            st.error(f"Error fetching tracked jobs: {str(e)}")
    
    # Create a simplified DataFrame for display
    display_columns = ["job_title", "company", "location", "date_posted", "employment_type"]
    
    # Make sure DataFrame has all needed columns
    for col in display_columns:
        if col not in df_jobs.columns:
            df_jobs[col] = ""  # Add empty column if missing
    
    # Create a clean DataFrame for Streamlit's native table
    clean_df = df_jobs[display_columns].copy()
    
    # Format date posted
    if "date_posted" in clean_df.columns:
        clean_df["date_posted"] = clean_df["date_posted"].apply(
            lambda x: format_job_date(x) if not pd.isna(x) else ""
        )
    
    # Rename columns for display
    clean_df = clean_df.rename(columns={
        "job_title": "Job Title",
        "company": "Company",
        "location": "Location",
        "date_posted": "Posted",
        "employment_type": "Type"
    })
    
    # Display standard table using Streamlit's native table
    if not is_authenticated():
        # Add Apply URL column for non-authenticated users
        clean_df["Apply"] = df_jobs.apply(
            lambda row: f"<a href='{row.get('job_url', '#')}' target='_blank'>Apply</a>" 
            if pd.notna(row.get('job_url')) else "", 
            axis=1
        )
        
        st.write("### Job Listings")
        st.dataframe(clean_df, use_container_width=True)
    else:
        # For authenticated users, we'll use a custom HTML table to handle the checkboxes properly
        st.write("### Job Listings")
        
        # Add buttons in Streamlit
        col1, col2 = st.columns([1, 5])
        with col1:
            if st.button("Save Job Status"):
                st.success("Job statuses saved!")
                st.rerun()
        
        # Create HTML table
        html = """
        <style>
        .job-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }
        .job-table th {
            background-color: #1E1E1E;
            padding: 10px;
            text-align: left;
            color: white;
            position: sticky;
            top: 0;
            z-index: 10;
        }
        .job-table td {
            padding: 8px;
            border-bottom: 1px solid #ddd;
            color: white;
        }
        .job-table tr:nth-child(even) {
            background-color: rgba(240, 240, 240, 0.1);
        }
        .job-table tr:nth-child(odd) {
            background-color: rgba(255, 255, 255, 0.05);
        }
        .job-table tr:hover {
            background-color: rgba(200, 200, 200, 0.2);
        }
        .apply-btn {
            padding: 5px 10px;
            background-color: #4CAF50;
            color: white;
            text-decoration: none;
            border-radius: 4px;
        }
        </style>
        
        <div style="max-height: 600px; overflow-y: auto;">
        <table class="job-table">
            <thead>
                <tr>
                    <th>Job Title</th>
                    <th>Company</th>
                    <th>Location</th>
                    <th>Posted</th>
                    <th>Type</th>
                    <th>Applied</th>
                    <th>Action</th>
                </tr>
            </thead>
            <tbody>
        """
        
        # Add table rows
        for i, row in df_jobs.iterrows():
            # Limit rows for performance
            if i >= 100:
                break
                
            # Get basic job info
            job_id = str(row.get('id', ''))
            job_title = str(row.get('job_title', '')).replace('<', '&lt;').replace('>', '&gt;')
            company = str(row.get('company', '')).replace('<', '&lt;').replace('>', '&gt;')
            location = str(row.get('location', '')).replace('<', '&lt;').replace('>', '&gt;')
            date_posted = format_job_date(row.get('date_posted', ''))
            job_type = str(row.get('employment_type', '')).replace('<', '&lt;').replace('>', '&gt;')
            job_url = row.get('job_url', '#')
            
            # Check if job is applied
            is_applied = tracked_jobs.get(job_id, False)
            checked = "checked" if is_applied else ""
            
            # Create HTML row
            html += f"""
            <tr>
                <td>{job_title}</td>
                <td>{company}</td>
                <td>{location}</td>
                <td>{date_posted}</td>
                <td>{job_type}</td>
                <td align="center">
                    <input type="checkbox" id="job_{job_id}" {checked} 
                           onchange="updateJob('{job_id}', this.checked)" 
                           style="width:20px; height:20px;">
                </td>
                <td align="center">
                    <a href="{job_url}" target="_blank" class="apply-btn">Apply</a>
                </td>
            </tr>
            """
        
        # Close table
        html += """
            </tbody>
        </table>
        </div>
        """
        
        # Add JavaScript for tracking job applications
        api_url = get_api_url()
        html += f"""
        <script>
        // Create a map to track changes
        const jobChanges = {{}};
        
        // Function to update job application status
        function updateJob(jobId, isApplied) {{
            console.log(`Job ${{jobId}} application status: ${{isApplied}}`);
            jobChanges[jobId] = isApplied;
            
            // Get auth token
            const token = localStorage.getItem('job_tracker_token');
            if (!token) {{
                alert('Please log in again to track jobs');
                return;
            }}
            
            // Submit the change immediately
            const apiUrl = "{api_url}";
            
            // First make sure job is tracked
            fetch(`${{apiUrl}}/user/jobs/${{jobId}}/track`, {{
                method: 'POST',
                headers: {{
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${{token}}`
                }}
            }})
            .then(response => {{
                if (!response.ok) throw new Error('Failed to track job');
                
                // Now update applied status
                return fetch(`${{apiUrl}}/user/jobs/${{jobId}}/applied`, {{
                    method: 'PUT',
                    headers: {{
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${{token}}`
                    }},
                    body: JSON.stringify({{ applied: isApplied }})
                }});
            }})
            .then(response => {{
                if (!response.ok) throw new Error('Failed to update application status');
                console.log('Job application status updated successfully');
            }})
            .catch(error => {{
                console.error('Error updating job:', error);
                // Don't show alert as it's annoying - just log error
            }});
        }}
        </script>
        """
        
        # Display the HTML table
        st.components.v1.html(html, height=700, scrolling=True)
