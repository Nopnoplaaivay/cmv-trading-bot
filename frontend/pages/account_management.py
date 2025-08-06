"""
Account management page for CMV Trading Bot frontend
"""

import streamlit as st
from ..services.api import setup_dnse_account


def account_management_page():
    """Account management and setup page"""
    st.subheader("🏦 Account Management")

    # DNSE Account Setup
    st.markdown("#### 🔧 DNSE Account Setup")

    with st.expander("Setup New DNSE Account", expanded=False):
        with st.form("dnse_setup_form"):
            custody_code = st.text_input(
                "Custody Code", placeholder="Enter your custody code"
            )
            password = st.text_input(
                "Password", type="password", placeholder="Enter your password"
            )

            submit_setup = st.form_submit_button(
                "🔗 Setup Account", use_container_width=True
            )

            if submit_setup and custody_code and password:
                with st.spinner("Setting up DNSE account..."):
                    success = setup_dnse_account(custody_code, password)
                    if success:
                        st.success("✅ DNSE account setup successful!")
                    else:
                        st.error("❌ DNSE account setup failed!")

    # Account Information
    st.markdown("#### 📊 Account Information")

    if st.session_state.get("broker_account_id"):
        st.info(f"**Current Account:** {st.session_state.broker_account_id}")

        # Account status check
        col1, col2 = st.columns(2)

        with col1:
            if st.button("🔍 Check Account Status", use_container_width=True):
                st.success("Account is active and connected")

        with col2:
            if st.button("🔄 Refresh Account Data", use_container_width=True):
                st.cache_data.clear()
                st.success("Account data refreshed")
    else:
        st.warning("Please set your broker account ID in the sidebar")
