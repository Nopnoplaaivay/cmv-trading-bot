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
                                # Set all auth data atomically
                                st.session_state.auth_token = auth_data.get(
                                    "accessToken"
                                )
                                st.session_state.refresh_token = auth_data.get(
                                    "refreshToken"
                                )
                                st.session_state.username = username

                                # Set authenticated LAST to ensure all data is in place
                                st.session_state.authenticated = True

                                # Initialize other required session state
                                if "order_history" not in st.session_state:
                                    st.session_state.order_history = []
                                if "selected_recommendations" not in st.session_state:
                                    st.session_state.selected_recommendations = []

                                # Fetch default account information
                                with st.spinner("📊 Loading account information..."):
                                    from ..services.auth import get_default_account

                                    account_data = get_default_account()
                                    if account_data:
                                        st.session_state.broker_account_id = (
                                            account_data.get("broker_account_id")
                                        )
                                        st.session_state.account_name = (
                                            account_data.get("name")
                                        )
                                        st.session_state.broker_name = account_data.get(
                                            "broker_name"
                                        )
                                        st.session_state.broker_investor_id = (
                                            account_data.get("broker_investor_id")
                                        )

                                st.success("✅ Login successful!")
                                time.sleep(1)
                                st.rerun()
                            else:
                                # Ensure authenticated is False on failed login
                                st.session_state.authenticated = False
                    else:
                        st.error("❌ Please enter both username and password")

            st.markdown("</div>", unsafe_allow_html=True)
