"""
Custom jobs table component for the dashboard - fixes spacing and checkbox issues
"""
import streamlit as st
import pandas as pd
from dashboard_components.utils import format_job_date, get_api_url
from app.dashboard.auth import is_authenticated, api_request

def display_custom_jobs_table(df_jobs):
    """A custom implementation of the jobs table with better spacing and working checkboxes"""
    
    # Only show authentication status during debugging
    # st.write(f"Authentication status: {is_authenticated()}")
    
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
    
    # Create a clean, simplified DataFrame directly for display
    display_df = pd.DataFrame()
    
    # Add columns from original data
    columns_to_display = ["job_title", "company", "location", "date_posted", "employment_type"]
    
    for col in columns_to_display:
        if col in df_jobs.columns:
            # Clean any HTML from the column
            if df_jobs[col].dtype == 'object':
                display_df[col] = df_jobs[col].astype(str).apply(
                    lambda x: x.replace('<', '&lt;').replace('>', '&gt;') if isinstance(x, str) else x
                )
            else:
                display_df[col] = df_jobs[col]
    
    # Format date for better display
    if "date_posted" in display_df.columns:
        display_df["date_posted"] = display_df["date_posted"].apply(
            lambda x: format_job_date(x) if not pd.isna(x) else ""
        )
    
    # Get job IDs and URLs for apply links
    job_ids = df_jobs["id"].tolist() if "id" in df_jobs.columns else []
    job_urls = df_jobs["job_url"].tolist() if "job_url" in df_jobs.columns else ["#"] * len(job_ids)
    
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
    
    for i, (_, row) in enumerate(display_df.iterrows()):
        if row_count >= max_rows:
            break
            
        row_count += 1
        row_class = "even" if i % 2 == 0 else "odd"
        
        # Get the job ID and URL for this row
        job_id = job_ids[i] if i < len(job_ids) else ""
        job_url = job_urls[i] if i < len(job_urls) else "#"
        
        # Start the row
        table_html += f'<tr class="{row_class}">'
        
        # Add basic columns
        for col in columns_to_display:
            if col in display_df.columns:
                value = row[col] if not pd.isna(row[col]) else ""
                table_html += f'<td>{value}</td>'
            else:
                table_html += '<td></td>'  # Empty cell if column doesn't exist
        
        # Add Applied checkbox if authenticated
        if is_authenticated():
            job_status = tracked_jobs.get(job_id, {'is_tracked': False, 'is_applied': False})
            checked = "checked" if job_status['is_applied'] else ""
            
            checkbox_html = f'''
            <input 
                type="checkbox" 
                id="applied_{job_id}" 
                {checked} 
                onclick="updateJobApplication('{job_id}', this.checked)" 
            />
            '''
            table_html += f'<td style="text-align: center;">{checkbox_html}</td>'
        
        # Always add Apply button
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
                
                // Optional: refresh the page to reflect changes
                // window.location.reload();
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
    if row_count < len(display_df):
        st.info(f"Showing {row_count} of {len(display_df)} jobs. Use filters to narrow results.")
