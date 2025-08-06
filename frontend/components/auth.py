"""
Login component for CMV Trading Bot frontend
"""

import streamlit as st
import time
from ..services.auth import login_user


def render_login_page():
    """Render login page"""
    st.markdown(
        '<div class="main-header"><h1>🔐 CMV Trading Bot</h1><p>Professional Portfolio Management System</p></div>',
        unsafe_allow_html=True,
    )

    # Center the login form
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        with st.container():
            st.markdown('<div class="metric-card">', unsafe_allow_html=True)
            st.subheader("Welcome Back")
            st.write("Please log in to access your trading dashboard")

            with st.form("login_form", clear_on_submit=False):
                username = st.text_input(
                    "👤 Username", placeholder="Enter your username"
                )
                password = st.text_input(
                    "🔒 Password", type="password", placeholder="Enter your password"
                )

                col_a, col_b, col_c = st.columns([1, 2, 1])
                with col_b:
                    submit_button = st.form_submit_button(
                        "🚀 Login", use_container_width=True
                    )

                if submit_button:
                    if username and password:
                        with st.spinner("🔄 Authenticating..."):
                            auth_data = login_user(username, password)
                            if auth_data:
                                st.session_state.authenticated = True
                                st.session_state.auth_token = auth_data.get(
                                    "accessToken"
                                )
                                st.session_state.refresh_token = auth_data.get(
                                    "refreshToken"
                                )
                                st.session_state.username = username
                                st.success("✅ Login successful!")
                                time.sleep(1)
                                st.rerun()
                    else:
                        st.error("❌ Please enter both username and password")

            st.markdown("</div>", unsafe_allow_html=True)
