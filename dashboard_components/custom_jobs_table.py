"""
Custom jobs table component for the dashboard - fixes spacing and checkbox issues
"""
import streamlit as st
import pandas as pd
from dashboard_components.utils import format_job_date, get_api_url
from app.dashboard.auth import is_authenticated, api_request

def display_custom_jobs_table(df_jobs):
    """A custom implementation of the jobs table with better spacing and working checkboxes"""
    
    # Debugging - show authentication status
    st.write(f"Authentication status: {is_authenticated()}")
    
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
    
    # Add server info for debugging
    api_url = get_api_url()
    st.markdown(f"<p class='debug-marker'>API URL: {api_url}</p>", unsafe_allow_html=True)
    
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
                # Debug info
                st.write(f"Debug - Found {len(tracked_jobs)} tracked jobs")
            except Exception as e:
                st.error(f"Error fetching tracked jobs: {str(e)}")
                # Continue without tracked jobs
        
        # Add Applied column if user is authenticated
        if is_authenticated():
            # Add an Applied column with checkboxes
            df_display["Applied"] = ""  # Placeholder
        
        # Add Actions column
        df_display["Actions"] = ""  # Placeholder
        
        # HTML table generation with direct styling
        html_table = f"""
        <div class="table-container" style="height:600px; overflow-y:auto; margin-top:0; padding-top:0;">
            <table id="job-listings-table" style="width:100%; border-collapse:collapse;">
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
        job_count = 0
        for i, row in df_jobs.iterrows():
            # Limit to maximum rows to avoid excessive HTML size
            job_count += 1
            if job_count > 100:  # Set a reasonable limit to avoid exceeding HTML size limits
                break
                
            row_style = 'background-color:rgba(240,240,240,0.1);' if i % 2 == 0 else 'background-color:rgba(255,255,255,0.05);'
            html_table += f'<tr style="{row_style}">'
            
            # Basic columns
            for col in display_columns:
                value = row[col]
                # Ensure proper escaping and handling of HTML
                if isinstance(value, str) and ('<' in value or '>' in value):
                    # Replace HTML tags with their escaped versions
                    value = value.replace('<', '&lt;').replace('>', '&gt;')
                formatted_value = format_job_date(value) if col == 'date_posted' else value
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
        api_url = get_api_url()
        js_code = f"""
        <script>
        // Function to update job application status
        function updateJobApplication(jobId, isApplied) {{
            console.log(`Updating job ${{jobId}} application status to ${{isApplied}}`);
            
            // Get auth token from localStorage
            const token = localStorage.getItem('job_tracker_token');
            if (!token) {{
                console.error('No authentication token found');
                alert('Please log in again to track jobs');
                return;
            }}
            
            // We need to ensure that we modify the checkbox appearance immediately so the user gets feedback
            const checkbox = document.getElementById(`applied_${{jobId}}`);
            if (checkbox) {{
                checkbox.disabled = true; // Disable during processing
            }}
            
            // First ensure the job is tracked
            const apiUrl = "{api_url}";
            const trackUrl = `${{apiUrl}}/user/jobs/${{jobId}}/track`;
            console.log(`API URL: ${{apiUrl}}`);
            console.log(`Tracking job at: ${{trackUrl}}`);
            
            fetch(trackUrl, {{
                method: 'POST',
                headers: {{
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${{token}}`
                }}
            }})
            .then(response => {{
                console.log(`Track job response status: ${{response.status}}`);
                if (response.ok) {{
                    // Now update applied status
                    const updateUrl = `${{apiUrl}}/user/jobs/${{jobId}}/applied`;
                    console.log(`Updating applied status at: ${{updateUrl}}`);
                    
                    return fetch(updateUrl, {{
                        method: 'PUT',
                        headers: {{
                            'Content-Type': 'application/json',
                            'Authorization': `Bearer ${{token}}`
                        }},
                        body: JSON.stringify({{ applied: isApplied }})
                    }});
                }} else {{
                    throw new Error(`Failed to track job: ${{response.statusText}}`);
                }}
            }})
            .then(response => {{
                console.log(`Update applied status response: ${{response.status}}`);
                if (!response.ok) {{
                    throw new Error(`Failed to update application status: ${{response.statusText}}`);
                }}
                console.log('Successfully updated application status');
                
                // Re-enable the checkbox
                if (checkbox) {{
                    checkbox.disabled = false;
                }}
                
                // Refresh the page to show the updated state
                setTimeout(() => {{
                    window.location.reload();
                }}, 1000);
            }})
            .catch(error => {{
                console.error('Error:', error);
                alert(`Failed to update job status: ${{error.message}}`);
                
                // Revert checkbox state and re-enable it
                if (checkbox) {{
                    checkbox.checked = !isApplied;
                    checkbox.disabled = false;
                }}
            }});
        }}
        
        // Initialize checkboxes on page load
        document.addEventListener('DOMContentLoaded', function() {{
            console.log('Initializing job application checkboxes');
            
            // Add debug message to console
            console.log('Table rendered and DOM loaded');
            
            // Get auth token from localStorage
            const token = localStorage.getItem('job_tracker_token');
            if (!token) {{
                console.error('No authentication token found');
                return;
            }}
            
            // Wait a short delay to ensure the DOM is fully rendered
            setTimeout(function() {{
                // Verify if checkboxes exist
                const checkboxes = document.querySelectorAll('input[type="checkbox"][id^="applied_"]');
                console.log(`Found ${{checkboxes.length}} checkboxes in the table`);
                
                // Make sure table exists
                const table = document.getElementById('job-listings-table');
                console.log(`Table element found: ${{!!table}}`);
                
                // Fetch current tracked jobs to sync checkboxes
                fetch(`${{apiUrl}}/user/jobs`, {{
                    method: 'GET',
                    headers: {{
                        'Authorization': `Bearer ${{token}}`
                    }}
                }})
                .then(response => {{
                    console.log('API response status:', response.status);
                    return response.json();
                }})
                .then(jobs => {{
                    console.log('Received jobs data:', jobs);
                    if (Array.isArray(jobs)) {{
                        // Create a map of job IDs to application status
                        const jobStatusMap = {{}};
                        jobs.forEach(job => {{
                            if (job && job.id) {{
                                jobStatusMap[job.id] = job.tracking && job.tracking.is_applied || false;
                            }}
                        }});
                        
                        console.log('Job status map:', jobStatusMap);
                        
                        // Update checkbox states
                        checkboxes.forEach(checkbox => {{
                            const jobId = checkbox.id.split('_')[1];
                            if (jobStatusMap.hasOwnProperty(jobId)) {{
                                checkbox.checked = jobStatusMap[jobId];
                                console.log(`Set checkbox ${{jobId}} to ${{jobStatusMap[jobId]}}`);
                            }}
                        }});
                    }}
                }})
                .catch(error => {{
                    console.error('Error syncing checkboxes:', error);
                }});
            }}, 500); // Short delay to ensure DOM is ready
        }});
        </script>
        """
        
        # Add Job Count information in the debug marker
        st.markdown(f"<div class='debug-marker'>Table should appear below this line (showing {job_count} of {len(df_jobs)} jobs)</div>", unsafe_allow_html=True)
        
        # Display the complete HTML with JavaScript
        try:
            st.markdown(html_table + js_code, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error rendering table: {str(e)}")
            
        # If authenticated, provide alternative views for accessing job data
        if is_authenticated():
            # Use Streamlit's native table rendering as a backup
            st.write("### Simplified Job Table")
            st.write("If the main table is not visible above, use this simplified table view:")
            
            # Create a simplified view for authenticated users
            simple_df = df_jobs[display_columns].copy()
            
            # Format the date column if it exists
            if "date_posted" in simple_df.columns:
                simple_df["date_posted"] = simple_df["date_posted"].apply(lambda x: format_job_date(x) if not pd.isna(x) else "")
            
            # Clean any HTML from text columns
            for col in simple_df.columns:
                if simple_df[col].dtype == 'object':
                    simple_df[col] = simple_df[col].astype(str).apply(lambda x: x.replace('<', '&lt;').replace('>', '&gt;') if isinstance(x, str) else x)
            
            # Add an Apply column with links
            apply_links = []
            for i, row in df_jobs.iterrows():
                job_url = row["job_url"].strip() if isinstance(row["job_url"], str) else "#"
                apply_links.append(job_url)
            
            # Add the Apply column
            simple_df["Apply URL"] = apply_links
            
            # Display the simplified table
            st.dataframe(simple_df)

            # Create job cards for a more user-friendly display
            st.write("")
            st.write("### Job Cards")
            
            # Limit to avoid too many cards
            display_count = min(10, len(df_jobs))
            
            for i in range(display_count):
                job = df_jobs.iloc[i]
                job_title = job['job_title']
                company = job['company']
                location = job.get('location', 'Location not specified')
                job_url = job["job_url"].strip() if isinstance(job["job_url"], str) else "#"
                
                # Create a card-like container
                with st.container():
                    cols = st.columns([3, 1])
                    with cols[0]:
                        st.markdown(f"**{job_title}**")
                        st.write(f"{company} | {location}")
                    with cols[1]:
                        # Using a standard button since link_button might not be available in older Streamlit versions
                        st.markdown(f"<a href='{job_url}' target='_blank' style='display:inline-block; padding:0.25rem 0.75rem; background-color:#4CAF50; color:white; text-decoration:none; border-radius:4px;'>Apply</a>", unsafe_allow_html=True)
                    
                    st.markdown("---")
    else:
        st.warning("No data available to display.")
