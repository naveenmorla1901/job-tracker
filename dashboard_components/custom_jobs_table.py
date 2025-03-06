"""
Custom jobs table component for the dashboard - fixes spacing and checkbox issues
"""
import streamlit as st
import pandas as pd
from dashboard_components.utils import format_job_date
from app.dashboard.auth import is_authenticated, api_request

def display_custom_jobs_table(df_jobs):
    """A custom implementation of the jobs table with better spacing and working checkboxes"""
    
    # Inject custom CSS to fix spacing issues
    st.markdown("""
    <style>
    /* Zero margin on job listings header */
    .job-listings-header {
        margin: 0 !important;
        padding: 0 !important;
        margin-bottom: 0 !important;
        padding-bottom: 0 !important;
    }
    
    /* Remove spacing from table container */
    .table-container {
        margin-top: 0 !important;
        padding-top: 0 !important;
    }
    
    /* Fix spacing between container elements */
    .element-container {
        margin: 0 !important;
        padding: 0 !important;
    }
    
    /* Streamlit styling overrides */
    .block-container {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }
    
    /* Override specific element causing spacing */
    iframe {
        margin: 0 !important;
        padding: 0 !important;
        height: auto !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Display the job listings header with zero margin
    st.markdown("<h3 class='job-listings-header'>Job Listings</h3>", unsafe_allow_html=True)
    
    # Prepare display columns
    display_columns = []
    for col in ["job_title", "company", "location", "date_posted", "employment_type"]:
        if col in df_jobs.columns:
            display_columns.append(col)
    
    # Create display DataFrame
    if display_columns:
        df_display = df_jobs[display_columns].copy()
        
        # Format date column with human-friendly display
        if "date_posted" in df_display.columns:
            df_display["date_posted"] = df_display["date_posted"].apply(format_job_date)
        
        # Rename columns for display
        column_mapping = {
            "job_title": "Job Title",
            "company": "Company",
            "location": "Location",
            "date_posted": "Posted",
            "employment_type": "Type",
        }
        df_display = df_display.rename(columns=column_mapping)
        
        # Get user's tracked jobs if authenticated
        tracked_jobs = {}
        if is_authenticated():
            user_jobs = api_request("user/jobs") or []
            for job in user_jobs:
                tracked_jobs[job['id']] = {
                    'is_tracked': True,
                    'is_applied': job['tracking'].get('is_applied', False)
                }
        
        # Add Applied column if user is authenticated
        if is_authenticated():
            # Add an Applied column with checkboxes
            df_display["Applied"] = ""  # Placeholder
        
        # Add Actions column
        df_display["Actions"] = ""  # Placeholder
        
        # HTML table generation with direct styling
        html_table = """
        <div class="table-container" style="height:600px; overflow-y:auto; margin-top:0; padding-top:0;">
            <table style="width:100%; border-collapse:collapse;">
                <thead>
                    <tr>
        """
        
        # Add table headers
        for col in df_display.columns:
            html_table += f'<th style="background-color:#1E1E1E; color:white; position:sticky; top:0; padding:8px; text-align:left;">{col}</th>'
        
        html_table += """
                    </tr>
                </thead>
                <tbody>
        """
        
        # Add table rows
        for i, row in df_jobs.iterrows():
            row_style = 'background-color:rgba(240,240,240,0.1);' if i % 2 == 0 else 'background-color:rgba(255,255,255,0.05);'
            html_table += f'<tr style="{row_style}">'
            
            # Basic columns
            for col in display_columns:
                formatted_value = format_job_date(row[col]) if col == 'date_posted' else row[col]
                html_table += f'<td style="padding:8px; border-bottom:1px solid #ddd; color:white;">{formatted_value}</td>'
            
            # Applied column (if authenticated)
            if is_authenticated():
                job_id = row['id']
                job_status = tracked_jobs.get(job_id, {'is_tracked': False, 'is_applied': False})
                checked_attr = "checked" if job_status['is_applied'] else ""
                
                # Create a checkbox for applied status with clear style
                checkbox_html = f'''
                <div style="text-align:center; display:flex; justify-content:center; align-items:center;">
                    <input 
                        type="checkbox" 
                        id="applied_{job_id}" 
                        {checked_attr} 
                        onclick="updateJobApplication({job_id}, this.checked)" 
                        style="width:18px; height:18px; cursor:pointer;"
                    />
                </div>
                '''
                html_table += f'<td style="padding:8px; border-bottom:1px solid #ddd; text-align:center;">{checkbox_html}</td>'
            
            # Actions column
            job_url = row["job_url"].strip() if isinstance(row["job_url"], str) else "#"
            action_html = f'<a href="{job_url}" target="_blank" style="padding:5px 10px; background-color:#4CAF50; color:white; text-decoration:none; border-radius:4px; display:inline-block;">Apply</a>'
            html_table += f'<td style="padding:8px; border-bottom:1px solid #ddd; text-align:center;">{action_html}</td>'
            
            html_table += '</tr>'
        
        html_table += """
                </tbody>
            </table>
        </div>
        """
        
        # Add JavaScript for checkbox functionality
        js_code = """
        <script>
        // Function to update job application status
        function updateJobApplication(jobId, isApplied) {
            console.log(`Updating job ${jobId} application status to ${isApplied}`);
            
            // Get auth token from localStorage
            const token = localStorage.getItem('job_tracker_token');
            if (!token) {
                console.error('No authentication token found');
                alert('Please log in again to track jobs');
                return;
            }
            
            // We need to ensure that we modify the checkbox appearance immediately so the user gets feedback
            const checkbox = document.getElementById(`applied_${jobId}`);
            if (checkbox) {
                checkbox.disabled = true; // Disable during processing
            }
            
            // First ensure the job is tracked
            fetch(`/api/user/jobs/${jobId}/track`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                }
            })
            .then(response => {
                if (response.ok) {
                    // Now update applied status
                    return fetch(`/api/user/jobs/${jobId}/applied`, {
                        method: 'PUT',
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': `Bearer ${token}`
                        },
                        body: JSON.stringify({ applied: isApplied })
                    });
                } else {
                    throw new Error('Failed to track job');
                }
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to update application status');
                }
                console.log('Successfully updated application status');
                
                // Re-enable the checkbox
                if (checkbox) {
                    checkbox.disabled = false;
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Failed to update job status. Please try again.');
                
                // Revert checkbox state and re-enable it
                const checkbox = document.getElementById(`applied_${jobId}`);
                if (checkbox) {
                    checkbox.checked = !isApplied;
                    checkbox.disabled = false;
                }
            });
        }
        
        // Initialize checkboxes on page load
        document.addEventListener('DOMContentLoaded', function() {
            console.log('Initializing job application checkboxes');
            
            // Get auth token from localStorage
            const token = localStorage.getItem('job_tracker_token');
            if (!token) {
                console.error('No authentication token found');
                return;
            }
            
            // Fetch current tracked jobs to sync checkboxes
            fetch('/api/user/jobs', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            })
            .then(response => response.json())
            .then(jobs => {
                if (Array.isArray(jobs)) {
                    // Create a map of job IDs to application status
                    const jobStatusMap = {};
                    jobs.forEach(job => {
                        jobStatusMap[job.id] = job.tracking && job.tracking.is_applied || false;
                    });
                    
                    // Update checkbox states
                    const checkboxes = document.querySelectorAll('input[type="checkbox"][id^="applied_"]');
                    checkboxes.forEach(checkbox => {
                        const jobId = checkbox.id.split('_')[1];
                        if (jobStatusMap.hasOwnProperty(jobId)) {
                            checkbox.checked = jobStatusMap[jobId];
                        }
                    });
                }
            })
            .catch(error => {
                console.error('Error syncing checkboxes:', error);
            });
        });
        </script>
        """
        
        # Display the complete HTML with JavaScript
        st.markdown(html_table + js_code, unsafe_allow_html=True)
    else:
        st.warning("No data available to display.")
