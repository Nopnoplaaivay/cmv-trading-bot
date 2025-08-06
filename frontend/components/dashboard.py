"""
Main dashboard component for CMV Trading Bot frontend
"""

import streamlit as st
from ..components.sidebar import render_sidebar
from ..pages.portfolio_analysis import portfolio_analysis_page
from ..pages.trade_execution import trade_execution_page
from ..pages.order_history import order_history_page
from ..pages.account_management import account_management_page


def render_dashboard():
    """Render main dashboard"""
    st.markdown(
        '<div class="main-header"><h1>📈 CMV Trading Bot Dashboard</h1><p>Real-time Portfolio Management & Trading</p></div>',
        unsafe_allow_html=True,
    )

    # Sidebar controls
    render_sidebar()

    # Main content based on sidebar selection
    if "current_page" not in st.session_state:
        st.session_state.current_page = "Portfolio Analysis"

    if st.session_state.current_page == "Portfolio Analysis":
        portfolio_analysis_page()
    elif st.session_state.current_page == "Trade Execution":
        trade_execution_page()
    elif st.session_state.current_page == "Order History":
        order_history_page()
    elif st.session_state.current_page == "Account Management":
        account_management_page()
