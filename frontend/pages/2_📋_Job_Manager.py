import streamlit as st
from utils.helpers import require_authentication, validate_facebook_url, get_status_color
from utils.api_client import APIClient
from datetime import datetime
import time

# Require authentication
require_authentication()

st.set_page_config(page_title="Job Manager", page_icon="📋", layout="wide")

# Initialize API client
api_client = APIClient()

st.title("📋 Job Manager")

# Tabs for different job management functions
tab1, tab2, tab3 = st.tabs(["Create Job", "Manage Jobs", "Job Details"])

with tab1:
    st.subheader("🆕 Create New Scraping Job")
    
    with st.form("create_job_form"):
        job_name = st.text_input("Job Name", placeholder="My Facebook Group Analysis")
        
        # Group URLs input
        st.write("**Facebook Group URLs**")
        group_urls_text = st.text_area(
            "Enter Facebook group URLs (one per line)",
            placeholder="https://www.facebook.com/groups/example1\nhttps://www.facebook.com/groups/example2",
            help="Only public Facebook groups are supported"
        )
        
        # Configuration options
        st.write("**Configuration**")
        col1, col2 = st.columns(2)
        
        with col1:
            max_posts = st.number_input("Max Posts per Group", min_value=10, max_value=1000, value=50)
        
        with col2:
            extract_comments = st.checkbox("Extract Comments", value=True)
        
        submit_btn = st.form_submit_button("Create Job", use_container_width=True)
        
        if submit_btn:
            if not job_name or not group_urls_text:
                st.error("Please fill in all required fields")
            else:
                # Parse URLs
                group_urls = [url.strip() for url in group_urls_text.split('\n') if url.strip()]
                
                # Validate URLs
                invalid_urls = [url for url in group_urls if not validate_facebook_url(url)]
                if invalid_urls:
                    st.error(f"Invalid Facebook group URLs: {', '.join(invalid_urls)}")
                else:
                    try:
                        config = {
                            "max_posts_per_group": max_posts,
                            "extract_comments": extract_comments
                        }
                        
                        with st.spinner("Creating job..."):
                            result = api_client.create_job(job_name, group_urls, config)
                            st.success(f"Job '{job_name}' created successfully!")
                            st.session_state.selected_job = result['id']
                            time.sleep(1)
                            st.rerun()
                    except Exception as e:
                        st.error(f"Failed to create job: {str(e)}")

with tab2:
    st.subheader("📋 Manage Your Jobs")
    
    try:
        jobs = api_client.get_jobs()
        
        if jobs:
            # Sort jobs by creation date
            jobs = sorted(jobs, key=lambda x: x['created_at'], reverse=True)
            
            for job in jobs:
                with st.container():
                    col1, col2, col3, col4, col5 = st.columns([3, 2, 1, 1, 2])
                    
                    with col1:
                        st.write(f"**{job['name']}**")
                        st.caption(f"Created: {datetime.fromisoformat(job['created_at'].replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M')}")
                        st.caption(f"Groups: {len(job['group_urls'])}")
                    
                    with col2:
                        status_colors = {
                            'running': '🟢 Running',
                            'completed': '🔵 Completed',
                            'failed': '🔴 Failed',
                            'paused': '🟡 Paused',
                            'created': '⚪ Created'
                        }
                        st.write(status_colors.get(job['status'], f"⚪ {job['status'].title()}"))
                    
                    with col3:
                        st.metric("Posts", job['total_posts'])
                    
                    with col4:
                        if job['last_run']:
                            last_run = datetime.fromisoformat(job['last_run'].replace('Z', '+00:00'))
                            st.caption(f"Last run: {last_run.strftime('%m-%d %H:%M')}")
                        else:
                            st.caption("Never run")
                    
                    with col5:
                        action_col1, action_col2, action_col3 = st.columns(3)
                        
                        with action_col1:
                            if job['status'] in ['created', 'paused', 'failed']:
                                if st.button("▶️", key=f"start_{job['id']}", help="Start Job"):
                                    try:
                                        api_client.start_job(job['id'])
                                        st.success("Job started!")
                                        time.sleep(1)
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Failed to start job: {str(e)}")
                            elif job['status'] == 'running':
                                if st.button("⏸️", key=f"pause_{job['id']}", help="Pause Job"):
                                    try:
                                        api_client.stop_job(job['id'])
                                        st.success("Job paused!")
                                        time.sleep(1)
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Failed to pause job: {str(e)}")
                        
                        with action_col2:
                            if st.button("👁️", key=f"view_{job['id']}", help="View Details"):
                                st.session_state.selected_job = job['id']
                        
                        with action_col3:
                            if st.button("🗑️", key=f"delete_{job['id']}", help="Delete Job"):
                                if st.session_state.get(f'confirm_delete_{job["id"]}'):
                                    try:
                                        api_client.delete_job(job['id'])
                                        st.success("Job deleted!")
                                        time.sleep(1)
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Failed to delete job: {str(e)}")
                                else:
                                    st.session_state[f'confirm_delete_{job["id"]}'] = True
                                    st.warning("Click again to confirm deletion")
                
                st.divider()
        else:
            st.info("No jobs created yet. Create your first job using the form above!")
            
    except Exception as e:
        st.error(f"Error loading jobs: {str(e)}")

with tab3:
    st.subheader("📊 Job Details")
    
    selected_job_id = st.session_state.get('selected_job')
    
    if selected_job_id:
        try:
            job = api_client.get_job(selected_job_id)
            
            # Job information
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Job Information**")
                st.write(f"**Name:** {job['name']}")
                st.write(f"**Status:** {job['status'].title()}")
                st.write(f"**Total Posts:** {job['total_posts']}")
                st.write(f"**Created:** {datetime.fromisoformat(job['created_at'].replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S')}")
                
                if job['last_run']:
                    st.write(f"**Last Run:** {datetime.fromisoformat(job['last_run'].replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S')}")
            
            with col2:
                st.write("**Configuration**")
                config = job.get('config', {})
                for key, value in config.items():
                    st.write(f"**{key.replace('_', ' ').title()}:** {value}")
                
                st.write("**Group URLs**")
                for i, url in enumerate(job['group_urls'], 1):
                    st.write(f"{i}. {url}")
            
            # Job logs
            st.subheader("📋 Job Logs")
            try:
                logs = api_client.get_job_logs(selected_job_id)
                
                if logs:
                    for log in logs[:20]:  # Show last 20 logs
                        timestamp = datetime.fromisoformat(log['timestamp'].replace('Z', '+00:00'))
                        
                        if log['level'] == 'ERROR':
                            st.error(f"[{timestamp.strftime('%H:%M:%S')}] {log['message']}")
                        elif log['level'] == 'WARNING':
                            st.warning(f"[{timestamp.strftime('%H:%M:%S')}] {log['message']}")
                        else:
                            st.info(f"[{timestamp.strftime('%H:%M:%S')}] {log['message']}")
                else:
                    st.info("No logs available for this job")
                    
            except Exception as e:
                st.error(f"Error loading job logs: {str(e)}")
                
        except Exception as e:
            st.error(f"Error loading job details: {str(e)}")
    else:
        st.info("Select a job from the 'Manage Jobs' tab to view details")

