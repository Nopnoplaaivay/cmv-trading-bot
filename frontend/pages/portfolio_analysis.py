import streamlit as st
from datetime import datetime
from frontend.services.portfolio import PortfolioService

from frontend.components.analysis import render_portfolio_vs_account_comparison, render_portfolio_analysis_page
from frontend.utils.helpers import format_currency


def portfolio_analysis_page():
    """Main portfolio analysis page with enhanced functionality"""

    # Create tabs for different analysis views
    tab1, tab2 = st.tabs(["📊 Enhanced Analysis", "⚖️ Portfolio vs Account"])

    with tab1:
        render_portfolio_analysis_page()

    with tab2:
        render_portfolio_vs_account_comparison()


