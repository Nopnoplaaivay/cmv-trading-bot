import streamlit as st

from frontend.components.management import (
    render_portfolio_list,
    render_create_portfolio_form,
)


def portfolio_management_page():
    if not st.session_state.get("authenticated", False):
        st.error("❌ Please login to access this page")
        return

    if st.session_state.get("role") not in ["admin", "premium"]:
        st.error("❌ Access denied. This page is only accessible by premium users.")
        return

    st.subheader("📊 Portfolio Management")
    tab1, tab2 = st.tabs(["📋 My Portfolios", "➕ Create New"])

    with tab1:
        render_portfolio_list()

    with tab2:
        render_create_portfolio_form()
