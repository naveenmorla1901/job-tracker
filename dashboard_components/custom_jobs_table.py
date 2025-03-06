"""
Custom jobs table component for the dashboard - fixes spacing and checkbox issues
"""
import streamlit as st
import pandas as pd
from dashboard_components.utils import format_job_date, get_api_url
from app.dashboard.auth import is_authenticated, api_request

def display_custom_jobs_table(df_jobs):
    """A custom implementation of the jobs table with better spacing and working checkboxes"""
    
    # Inject custom CSS to fix spacing issues
    st.markdown("""
    <style>
    /* Zero margin on job listings header */
    .job-listing-header {
        margin-bottom: 0 !important;
        padding-bottom: 0 !important;
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    
    /* Table styling */
    .job-table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 10px;
    }
    
    .job-table th {
        background-color: #1E1E1E;
        color: white;
        text-align: left;
        padding: 8px;
        border-bottom: 1px solid #ddd;
        position: sticky;
        top: 0;
    }
    
    .job-table td {
        padding: 8px;
        border-bottom: 1px solid #ddd;
        color: white;
        text-overflow: ellipsis;
        max-width: 300px;
        white-space: nowrap;
        overflow: hidden;
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
    
    /* Apply button */
    .apply-btn {
        display: inline-block;
        background-color: #4CAF50;
        color: white;
        text-decoration: none;
        padding: 4px 10px;
        border-radius: 4px;
        text-align: center;
    }
    
    /* Fix checkboxes */
    input[type="checkbox"] {
        width: 18px;
        height: 18px;
        cursor: pointer;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Get user's tracked jobs if authenticated
    tracked_jobs = {}
    if is_authenticated():
        try:
            user_jobs = api_request("user/jobs") or []
            if user_jobs and isinstance(user_jobs, list):
                for job in user_jobs:
                    job_id = job.get('id')
                    if job_id:
                        tracked_jobs[job_id] = {
                            'is_tracked': True,
                            'is_applied': job.get('tracking', {}).get('is_applied', False)
                        }
        except Exception as e:
            # Just log the error but continue
            st.error(f"Error fetching tracked jobs: {str(e)}")
    
    # Display the table using clean HTML
    st.markdown("<h3>Job Listings</h3>", unsafe_allow_html=True)
    
    # Start the table HTML
    table_html = """
    <div style="max-height: 600px; overflow-y: auto; margin-top: 10px;">
        <table class="job-table">
            <thead>
                <tr>
                    <th>Job Title</th>
                    <th>Company</th>
                    <th>Location</th>
                    <th>Posted</th>
                    <th>Type</th>
    """
    
    # Add Applied column if authenticated
    if is_authenticated():
        table_html += "<th>Applied</th>"
    
    # Always add the Action column
    table_html += "<th>Action</th></tr></thead><tbody>"
    
    # Add table rows (limit to 100 to keep HTML size reasonable)
    row_count = 0
    max_rows = 100
    
    for i, row in df_jobs.iterrows():
        if row_count >= max_rows:
            break
            
        row_count += 1
        row_class = "even" if i % 2 == 0 else "odd"
        
        # Get the job ID and URL for this row
        job_id = row.get("id", "")
        job_url = row.get("job_url", "#")
        if isinstance(job_url, str):
            job_url = job_url.strip()
        
        # Start the row
        table_html += f'<tr class="{row_class}">'
        
        # Add basic columns with proper escaping
        for col in ["job_title", "company", "location", "date_posted", "employment_type"]:
            if col in df_jobs.columns:
                value = row.get(col, "")
                
                # Format date if needed
                if col == "date_posted":
                    value = format_job_date(value)
                
                # Escape HTML in string values
                if isinstance(value, str) and ('<' in value or '>' in value):
                    value = value.replace('<', '&lt;').replace('>', '&gt;')
                
                table_html += f'<td>{value}</td>'
            else:
                table_html += '<td></td>'  # Empty cell if column doesn't exist
        
        # Add Applied checkbox if authenticated
        if is_authenticated():
            # Get the checked status based on tracked_jobs
            job_status = tracked_jobs.get(str(job_id), {})
            is_applied = job_status.get('is_applied', False)
            checked = "checked" if is_applied else ""
            
            checkbox_html = f'''
            <input 
                type="checkbox" 
                id="applied_{job_id}" 
                {checked} 
                onclick="updateJobApplication('{job_id}', this.checked)" 
            />
            '''
            table_html += f'<td style="text-align: center;">{checkbox_html}</td>'
        
        # Add Apply button
        apply_btn = f'<a href="{job_url}" target="_blank" class="apply-btn">Apply</a>'
        table_html += f'<td style="text-align: center;">{apply_btn}</td>'
        
        # End the row
        table_html += '</tr>'
    
    # Close the table
    table_html += '</tbody></table></div>'
    
    # Add JavaScript for handling checkbox clicks if authenticated
    if is_authenticated():
        api_url = get_api_url()
        js_code = f"""
        <script>
        // Load tracked jobs on page load
        document.addEventListener('DOMContentLoaded', function() {{
            syncCheckboxes();
        }});
        
        // Function to sync checkboxes with server state
        function syncCheckboxes() {{
            // Get auth token from localStorage
            const token = localStorage.getItem('job_tracker_token');
            if (!token) {{
                console.error('No authentication token found');
                return;
            }}
            
            // API endpoint
            const apiUrl = "{api_url}";
            
            // Fetch user's tracked jobs
            fetch(`${{apiUrl}}/user/jobs`, {{
                method: 'GET',
                headers: {{
                    'Authorization': `Bearer ${{token}}`
                }}
            }})
            .then(response => response.json())
            .then(jobs => {{
                if (Array.isArray(jobs)) {{
                    // Create a map of job IDs to application status
                    const jobStatusMap = {{}};
                    jobs.forEach(job => {{
                        if (job && job.id) {{
                            jobStatusMap[job.id] = job.tracking && job.tracking.is_applied || false;
                        }}
                    }});
                    
                    // Update checkboxes to match database state
                    const checkboxes = document.querySelectorAll('input[type="checkbox"][id^="applied_"]');
                    checkboxes.forEach(checkbox => {{
                        const jobId = checkbox.id.split('_')[1];
                        if (jobStatusMap.hasOwnProperty(jobId)) {{
                            checkbox.checked = jobStatusMap[jobId];
                        }}
                    }});
                }}
            }})
            .catch(error => {{
                console.error('Error syncing checkboxes:', error);
            }});
        }}
        
        function updateJobApplication(jobId, isApplied) {{
            console.log(`Updating job ${{jobId}} application status to ${{isApplied}}`);
            
            // Get auth token from localStorage
            const token = localStorage.getItem('job_tracker_token');
            if (!token) {{
                alert('Please log in again to track jobs');
                return;
            }}
            
            // Disable checkbox during processing
            const checkbox = document.getElementById(`applied_${{jobId}}`);
            if (checkbox) {{
                checkbox.disabled = true;
            }}
            
            // API endpoints
            const apiUrl = "{api_url}";
            const trackUrl = `${{apiUrl}}/user/jobs/${{jobId}}/track`;
            const updateUrl = `${{apiUrl}}/user/jobs/${{jobId}}/applied`;
            
            // First ensure job is tracked
            fetch(trackUrl, {{
                method: 'POST',
                headers: {{
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${{token}}`
                }}
            }})
            .then(response => {{
                if (response.ok) {{
                    // Now update applied status
                    return fetch(updateUrl, {{
                        method: 'PUT',
                        headers: {{
                            'Content-Type': 'application/json',
                            'Authorization': `Bearer ${{token}}`
                        }},
                        body: JSON.stringify({{ applied: isApplied }})
                    }});
                }} else {{
                    throw new Error(`Failed to track job`);
                }}
            }})
            .then(response => {{
                if (!response.ok) {{
                    throw new Error(`Failed to update application status`);
                }}
                
                // Re-enable checkbox
                if (checkbox) {{
                    checkbox.disabled = false;
                }}
            }})
            .catch(error => {{
                console.error('Error:', error);
                alert('Failed to update job status. Please try again.');
                
                // Revert checkbox and re-enable
                if (checkbox) {{
                    checkbox.checked = !isApplied;
                    checkbox.disabled = false;
                }}
            }});
        }}
        </script>
        """
        table_html += js_code
    
    # Display the complete table with JavaScript
    st.markdown(table_html, unsafe_allow_html=True)
    
    # Add a message if we limited the number of displayed rows
    if row_count < len(df_jobs):
        st.info(f"Showing {row_count} of {len(df_jobs)} jobs. Use filters to narrow results.")
