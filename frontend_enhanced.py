# frontend_enhanced.py
"""
Enhanced Streamlit frontend with Portfolio Management
"""

import streamlit as st
import time
import numpy as np
import pandas as pd

# Configure page
from frontend.utils.config import STREAMLIT_CONFIG
st.set_page_config(**STREAMLIT_CONFIG)

# Import enhanced styles and components
from frontend.styles.portfolio_styles import ENHANCED_MAIN_CSS
from frontend.utils.helpers import init_session_state
from frontend.components.auth import render_login_page
from frontend.components.enhanced_dashboard import render_enhanced_dashboard

# Apply enhanced CSS
st.markdown(ENHANCED_MAIN_CSS, unsafe_allow_html=True)


def init_enhanced_session_state():
    """Initialize enhanced session state with portfolio data"""
    init_session_state()
    
    # Portfolio-specific session state
    if "selected_symbols" not in st.session_state:
        st.session_state.selected_symbols = []
    
    if "portfolios" not in st.session_state:
        st.session_state.portfolios = []
    
    if "current_portfolio_id" not in st.session_state:
        st.session_state.current_portfolio_id = None
    
    if "portfolio_analysis_cache" not in st.session_state:
        st.session_state.portfolio_analysis_cache = {}


def main():
    """Enhanced main application with portfolio management"""
    # Initialize session state
    init_enhanced_session_state()

    # Add custom JavaScript for enhanced UX
    st.markdown("""
        <script>
        // Auto-refresh functionality
        function autoRefresh() {
            if (window.sessionStorage.getItem('auto_refresh') === 'true') {
                setTimeout(() => {
                    window.location.reload();
                }, 30000); // 30 seconds
            }
        }
        
        // Portfolio comparison functionality
        function comparePortfolios() {
            // Implementation for portfolio comparison
            console.log('Comparing portfolios...');
        }
        
        // Initialize
        document.addEventListener('DOMContentLoaded', autoRefresh);
        </script>
    """, unsafe_allow_html=True)

    # Route to appropriate page
    if not st.session_state.authenticated:
        render_login_page()
    else:
        render_enhanced_dashboard()

    # Add footer
    render_footer()


def render_footer():
    """Render application footer"""
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666; padding: 1rem;'>
            <p>📈 CMV Trading Bot v2.0 | Enhanced Portfolio Management System</p>
            <p>Made with ❤️ using Streamlit | 
            <a href='#' style='color: #2a5298;'>Documentation</a> | 
            <a href='#' style='color: #2a5298;'>Support</a> | 
            <a href='#' style='color: #2a5298;'>API</a></p>
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()