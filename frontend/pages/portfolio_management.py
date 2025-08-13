import streamlit as st

from frontend.components.management import (
    render_portfolio_list,
    render_create_portfolio_form,
)


def portfolio_management_page():
    """Main portfolio management page"""
    st.subheader("📊 Portfolio Management")

    tab1, tab2 = st.tabs(["📋 My Portfolios", "➕ Create New"])

    with tab1:
        render_portfolio_list()

    with tab2:
        render_create_portfolio_form()
