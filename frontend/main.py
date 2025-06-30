import streamlit as st
from utils.api_client import APIClient
from utils.helpers import check_authentication

# Page configuration
st.set_page_config(
    page_title="Facebook Group Scraper",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize API client
if 'api_client' not in st.session_state:
    st.session_state.api_client = APIClient()

def login_page():
    st.title("🔐 Login to Facebook Group Scraper")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        st.subheader("Login")
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="your@email.com")
            password = st.text_input("Password", type="password")
            login_btn = st.form_submit_button("Login", use_container_width=True)
            
            if login_btn:
                if not email or not password:
                    st.error("Please fill in all fields")
                else:
                    try:
                        with st.spinner("Logging in..."):
                            result = st.session_state.api_client.login(email, password)
                            st.session_state.access_token = result['access_token']
                            st.session_state.user = result['user']
                            st.success("Login successful!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Login failed: {str(e)}")
    
    with tab2:
        st.subheader("Register")
        with st.form("register_form"):
            reg_email = st.text_input("Email", key="reg_email", placeholder="your@email.com")
            reg_password = st.text_input("Password", key="reg_password", type="password")
            reg_confirm_password = st.text_input("Confirm Password", type="password")
            reg_full_name = st.text_input("Full Name", placeholder="Your Name")
            register_btn = st.form_submit_button("Register", use_container_width=True)
            
            if register_btn:
                if not all([reg_email, reg_password, reg_confirm_password]):
                    st.error("Please fill in all required fields")
                elif reg_password != reg_confirm_password:
                    st.error("Passwords do not match")
                elif len(reg_password) < 6:
                    st.error("Password must be at least 6 characters long")
                else:
                    try:
                        with st.spinner("Creating account..."):
                            st.session_state.api_client.register(reg_email, reg_password, reg_full_name)
                            st.success("Account created successfully! Please login.")
                    except Exception as e:
                        st.error(f"Registration failed: {str(e)}")

def main_app():
    # Sidebar navigation
    with st.sidebar:
        st.title("📊 FB Group Scraper")
        
        # User info
        user = st.session_state.user
        st.write(f"👤 Welcome, {user['full_name'] or user['email']}")
        st.write(f"🎯 Plan: {user['user_tier'].title()}")
        
        # Navigation
        st.divider()
        
        # Logout button
        if st.button("🚪 Logout", use_container_width=True):
            from utils.helpers import logout
            logout()
    
    # Main content
    st.title("🏠 Dashboard")
    
    # Get user stats
    try:
        stats = st.session_state.api_client.get_user_stats()
        
        # Display stats
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Jobs", stats['total_jobs'])
        
        with col2:
            st.metric("Total Posts", stats['total_posts'])
        
        with col3:
            st.metric("Active Jobs", stats['active_jobs'])
        
        with col4:
            st.metric("Plan", stats['user_tier'].title())
        
        st.divider()
        
        # Recent jobs
        st.subheader("📋 Recent Jobs")
        jobs = st.session_state.api_client.get_jobs()
        
        if jobs:
            # Sort by creation date
            jobs = sorted(jobs, key=lambda x: x['created_at'], reverse=True)
            
            for job in jobs[:5]:  # Show last 5 jobs
                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
                    
                    with col1:
                        st.write(f"**{job['name']}**")
                        st.caption(f"Groups: {len(job['group_urls'])}")
                    
                    with col2:
                        status_color = {
                            'running': '🟢',
                            'completed': '🔵',
                            'failed': '🔴',
                            'paused': '🟡',
                            'created': '⚪'
                        }.get(job['status'], '⚪')
                        st.write(f"{status_color} {job['status'].title()}")
                    
                    with col3:
                        st.metric("Posts", job['total_posts'])
                    
                    with col4:
                        if st.button("View", key=f"view_{job['id']}"):
                            st.session_state.selected_job = job['id']
                            st.switch_page("pages/2_📋_Job_Manager.py")
                
                st.divider()
        else:
            st.info("No jobs created yet. Go to Job Manager to create your first scraping job!")
        
        # Quick actions
        st.subheader("🚀 Quick Actions")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📋 Create New Job", use_container_width=True):
                st.switch_page("pages/2_📋_Job_Manager.py")
        
        with col2:
            if st.button("📊 View Data", use_container_width=True):
                st.switch_page("pages/3_📊_Data_Viewer.py")
                
    except Exception as e:
        st.error(f"Error loading dashboard: {str(e)}")

# Main app logic
if __name__ == "__main__":
    if check_authentication():
        main_app()
    else:
        login_page()

