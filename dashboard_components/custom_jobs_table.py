"""
Custom jobs table component for the dashboard - fixes spacing and checkbox issues
"""
import streamlit as st
import pandas as pd
from dashboard_components.utils import format_job_date, get_api_url
from app.dashboard.auth import is_authenticated, api_request, get_token

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
    
    # Display table header
    st.write("### Job Listings")
    
    # Define common CSS for both tables
    common_css = """
    <style>
    .job-table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 10px;
        font-size: 14px;
    }
    .job-table th {
        background-color: #1E1E1E;
        padding: 10px;
        text-align: left;
        color: white;
        position: sticky;
        top: 0;
        z-index: 10;
        font-weight: bold;
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
        display: inline-block;
    }
    </style>
    """
    
    # Different implementations for authenticated vs non-authenticated users
    if is_authenticated():
        # For authenticated users: HTML table with checkboxes
        
        # Table headers
        html = common_css + """
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
        token = get_token() or ""  # Get token from session state
        
        html += f"""
        <script>
        // Store the auth token directly in a variable
        const AUTH_TOKEN = "{token}";
        const API_URL = "{api_url}";
        
        // Function to update job application status
        function updateJob(jobId, isApplied) {{
            console.log(`Job ${{jobId}} application status: ${{isApplied}}`);
            
            // Disable checkbox during update
            const checkbox = document.getElementById(`job_${{jobId}}`);
            if (checkbox) {{
                checkbox.disabled = true;
            }}
            
            // First ensure job is tracked
            fetch(`${{API_URL}}/user/jobs/${{jobId}}/track`, {{
                method: 'POST',
                headers: {{
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${{AUTH_TOKEN}}`
                }}
            }})
            .then(response => {{
                if (!response.ok) {{
                    console.error(`Error tracking job: ${{response.status}}`, response);
                    throw new Error('Failed to track job');
                }}
                console.log('Successfully tracked job');
                
                // Now update applied status
                return fetch(`${{API_URL}}/user/jobs/${{jobId}}/applied`, {{
                    method: 'PUT',
                    headers: {{
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${{AUTH_TOKEN}}`
                    }},
                    body: JSON.stringify({{ applied: isApplied }})
                }});
            }})
            .then(response => {{
                if (!response.ok) {{
                    console.error(`Error updating application status: ${{response.status}}`, response);
                    throw new Error('Failed to update application status');
                }}
                console.log('Successfully updated job application status');
                
                // Re-enable checkbox
                if (checkbox) {{
                    checkbox.disabled = false;
                }}
            }})
            .catch(error => {{
                console.error('Error:', error);
                
                // Re-enable checkbox and revert state
                if (checkbox) {{
                    checkbox.disabled = false;
                    checkbox.checked = !isApplied;
                }}
                
                // Display subtle notification instead of alert
                const notification = document.createElement('div');
                notification.style.position = 'fixed';
                notification.style.bottom = '20px';
                notification.style.right = '20px';
                notification.style.backgroundColor = '#f44336';
                notification.style.color = 'white';
                notification.style.padding = '10px';
                notification.style.borderRadius = '5px';
                notification.style.zIndex = '1000';
                notification.textContent = 'Error updating job status. Please try again.';
                document.body.appendChild(notification);
                
                // Remove notification after 3 seconds
                setTimeout(() => {{
                    document.body.removeChild(notification);
                }}, 3000);
            }});
        }}
        </script>
        """
        
        # Display the HTML table
        st.components.v1.html(html, height=700, scrolling=True)
        
        # Show message if we limited the number of rows
        if len(df_jobs) > 100:
            st.info(f"Showing 100 of {len(df_jobs)} jobs. Use filters to narrow results.")
    else:
        # For non-authenticated users: HTML table without checkboxes
        
        # Table headers
        html = common_css + """
        <div style="max-height: 600px; overflow-y: auto;">
        <table class="job-table">
            <thead>
                <tr>
                    <th>Job Title</th>
                    <th>Company</th>
                    <th>Location</th>
                    <th>Posted</th>
                    <th>Type</th>
                    <th>Action</th>
                </tr>
            </thead>
            <tbody>
        """
        
        # Add table rows
        for i, row in df_jobs.iterrows():
            # Get basic job info
            job_title = str(row.get('job_title', '')).replace('<', '&lt;').replace('>', '&gt;')
            company = str(row.get('company', '')).replace('<', '&lt;').replace('>', '&gt;')
            location = str(row.get('location', '')).replace('<', '&lt;').replace('>', '&gt;')
            date_posted = format_job_date(row.get('date_posted', ''))
            job_type = str(row.get('employment_type', '')).replace('<', '&lt;').replace('>', '&gt;')
            job_url = row.get('job_url', '#')
            
            # Create HTML row
            html += f"""
            <tr>
                <td>{job_title}</td>
                <td>{company}</td>
                <td>{location}</td>
                <td>{date_posted}</td>
                <td>{job_type}</td>
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
        
        # Display the HTML table
        st.components.v1.html(html, height=700, scrolling=True)
