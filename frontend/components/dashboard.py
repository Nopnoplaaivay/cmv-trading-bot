import streamlit as st

from frontend.components.sidebar import render_sidebar
from frontend.components.portfolio_management import portfolio_management_page
from frontend.pages.portfolio_analysis import portfolio_analysis_page
from frontend.pages.trade_execution import trade_execution_page
from frontend.pages.order_history import order_history_page
from frontend.pages.account_management import account_management_page


def render_dashboard():
    """Render main dashboard"""
    st.markdown(
        '<div class="main-header"><h1>📈 CMV Portfolio Management Website</h1><p>Real-time Trading</p></div>',
        unsafe_allow_html=True,
    )

    render_sidebar()

    if "current_page" not in st.session_state:
        st.session_state.current_page = "Portfolio Analysis"

    if st.session_state.current_page == "Portfolio Analysis":
        portfolio_analysis_page()
    elif st.session_state.current_page == "Portfolio Management":
        portfolio_management_page()
    elif st.session_state.current_page == "Trade Execution":
        trade_execution_page()
    elif st.session_state.current_page == "Order History":
        order_history_page()
    elif st.session_state.current_page == "Account Management":
        account_management_page()
