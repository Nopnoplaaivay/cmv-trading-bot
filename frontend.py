"""
Enhanced Streamlit frontend for CMV Trading Bot with DNSE API integration
This application provides a comprehensive interface for portfolio management and trading
"""

import streamlit as st

# Configure Streamlit page
from frontend.utils.config import STREAMLIT_CONFIG

st.set_page_config(**STREAMLIT_CONFIG)

# Import styles and components
from frontend.styles.main import MAIN_CSS
from frontend.styles.portfolio_styles import ENHANCED_MAIN_CSS
from frontend.utils.helpers import init_session_state, init_enhanced_session_state
from frontend.components.auth import render_login_page
from frontend.components.footer import render_footer
from frontend.components.dashboard import render_dashboard

# Apply CSS styles
st.markdown(ENHANCED_MAIN_CSS, unsafe_allow_html=True)

def main():
    """Main application entry point"""
    # Initialize session state
    init_enhanced_session_state()

    # Route to appropriate page
    if not st.session_state.authenticated:
        render_login_page()
    else:
        render_dashboard()

    # Add footer
    render_footer()

if __name__ == "__main__":
    main()
