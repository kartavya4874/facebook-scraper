import streamlit as st
from utils.helpers import require_authentication

# Require authentication
require_authentication()

# Redirect to main dashboard
st.switch_page("main.py")

