import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Dict, List

def check_authentication():
    """Check if user is authenticated"""
    return 'access_token' in st.session_state and 'user' in st.session_state

def require_authentication():
    """Redirect to login if not authenticated"""
    if not check_authentication():
        st.error("Please login to access this page")
        st.page_link("main.py", label="Go to Login", icon="🔐")
        st.stop()

def logout():
    """Clear session and logout user"""
    st.session_state.clear()
    st.success("Logged out successfully!")
    st.rerun()

def format_number(num: int) -> str:
    """Format large numbers with K, M suffixes"""
    if num >= 1000000:
        return f"{num/1000000:.1f}M"
    elif num >= 1000:
        return f"{num/1000:.1f}K"
    return str(num)

def get_status_color(status: str) -> str:
    """Get color for job status"""
    colors = {
        'running': 'green',
        'completed': 'blue',
        'failed': 'red',
        'paused': 'orange',
        'created': 'gray'
    }
    return colors.get(status, 'gray')

def validate_facebook_url(url: str) -> bool:
    """Validate if URL is a Facebook group URL"""
    facebook_patterns = [
        'facebook.com/groups/',
        'fb.com/groups/',
        'm.facebook.com/groups/'
    ]
    return any(pattern in url.lower() for pattern in facebook_patterns)

def posts_to_dataframe(posts: List[Dict]) -> pd.DataFrame:
    """Convert posts list to pandas DataFrame"""
    if not posts:
        return pd.DataFrame()
    
    df = pd.DataFrame(posts)
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    if 'scraped_at' in df.columns:
        df['scraped_at'] = pd.to_datetime(df['scraped_at'])
    
    return df

