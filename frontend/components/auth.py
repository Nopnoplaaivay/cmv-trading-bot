import streamlit as st
import re
from typing import Dict, Optional
import time

from frontend.services.auth import login_user, register_user
from frontend.utils.helpers import init_session_state
from backend.common.consts import CommonConsts
from backend.utils.jwt_utils import JWTUtils


def render_login_form():
    st.markdown("### 🔑 Sign In to Your Account")

    with st.form("login_form", clear_on_submit=False):
        username = st.text_input(
            "Username", placeholder="Enter your username", help="Your account username"
        )

        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter your password",
            help="Your account password",
        )

        submit_login = st.form_submit_button(
            "🚀 Login", use_container_width=True, type="primary"
        )

        if submit_login:
            handle_login(username, password)

    st.markdown("---")
    st.markdown("📝 **New to CMV Portfolio Management App?**")
    if st.button(
        "Create Free Account",
        use_container_width=True,
        type="secondary",
        key="register_btn",
    ):
        st.session_state.auth_mode = "register"
        st.rerun()


def render_register_form():
    st.markdown("### 📝 Create Your Free Account")
    with st.form("register_form", clear_on_submit=False):
        username = st.text_input(
            "Username *",
            placeholder="Choose a unique username",
            help="3-20 characters, letters, numbers, and underscores only",
        )

        col1, col2 = st.columns(2)
        with col1:
            password = st.text_input(
                "Password *",
                type="password",
                placeholder="Create a strong password",
                help="Minimum 8 characters",
            )

        with col2:
            confirm_password = st.text_input(
                "Confirm Password *",
                type="password",
                placeholder="Confirm your password",
            )

        # Terms and conditions
        st.markdown("---")
        terms_accepted = st.checkbox(
            "I agree to the Terms of Service and Privacy Policy",
            help="Required to create an account",
        )

        # Submit button
        submit_register = st.form_submit_button(
            "🎯 Create Account", use_container_width=True, type="primary"
        )

        if submit_register:
            handle_registration(username, password, confirm_password, terms_accepted)

    # Quick login link
    st.markdown("---")
    st.markdown("🔑 **Already have an account?**")
    if st.button(
        "Already have an account? Sign In",
        use_container_width=True,
        type="secondary",
        key="login_btn",
    ):
        st.session_state.auth_mode = "login"
        st.rerun()


def handle_login(username: str, password: str):
    if not username or not password:
        st.error("❌ Please fill in all required fields")
        return

    with st.spinner("🔐 Authenticating..."):
        time.sleep(0.5) 
        auth_data = login_user(username, password)

    if auth_data:
        st.session_state.authenticated = True
        st.session_state.username = username
        st.session_state.auth_token = auth_data.get("accessToken")
        st.session_state.refresh_token = auth_data.get("refreshToken")
        st.session_state.role = auth_data.get("role")

        decoded_payload = JWTUtils.decode_token(
            token=st.session_state.auth_token, secret_key=CommonConsts.AT_SECRET_KEY
        )

        if decoded_payload:
            st.session_state.user_id = decoded_payload.get("userId")
            st.session_state.session_id = decoded_payload.get("sessionId")
            st.session_state.role = decoded_payload.get("role")

        st.session_state.authenticated = True

        if "order_history" not in st.session_state:
            st.session_state.order_history = []
        if "selected_recommendations" not in st.session_state:
            st.session_state.selected_recommendations = []

        with st.spinner("📊 Loading account information..."):
            from ..services.auth import get_default_account

            account_data = get_default_account()
            if account_data:
                st.session_state.custody_code = account_data.get("custody_code")
                st.session_state.broker_account_id = (account_data.get("broker_account_id"))
                st.session_state.account_name = (account_data.get("name"))
                st.session_state.broker_name = (account_data.get("broker_name"))
                st.session_state.broker_investor_id = (account_data.get("broker_investor_id"))

        st.success("✅ Login successful! Redirecting...")

        time.sleep(1)
        st.rerun()
    else:
        st.error("❌ Login failed. Please check your credentials.")


def handle_registration(
    username: str, password: str, confirm_password: str, terms_accepted: bool
):
    validation_errors = []

    if not username:
        validation_errors.append("Username is required")
    elif not validate_username(username):
        validation_errors.append(
            "Username must be 3-20 characters, letters, numbers, and underscores only"
        )

    if not password:
        validation_errors.append("Password is required")
    elif len(password) < 8:
        validation_errors.append("Password must be at least 8 characters")

    if not confirm_password:
        validation_errors.append("Please confirm your password")
    elif password != confirm_password:
        validation_errors.append("Passwords do not match")

    if not terms_accepted:
        validation_errors.append("You must accept the Terms of Service")

    if validation_errors:
        for error in validation_errors:
            st.error(f"❌ {error}")
        return

    with st.spinner("📝 Creating your account..."):
        time.sleep(0.5)  
        register_data = register_user(username, password, confirm_password)

    if register_data:
        st.success("🎉 Account created successfully!")
        st.balloons()

        st.info(
            "✨ **Welcome to CMV Portfolio Management App!** You can now sign in with your credentials."
        )

        st.session_state.auth_mode = "login"
        time.sleep(2)
        st.rerun()
    else:
        st.error("❌ Registration failed. Please try again.")


def validate_username(username: str) -> bool:
    if len(username) < 3 or len(username) > 20:
        return False
    return re.match(r"^[a-zA-Z0-9_]+$", username) is not None



def render_user_info_sidebar():
    if st.session_state.get("authenticated", False):
        with st.sidebar:
            st.markdown("---")
            st.markdown("### 👤 Account Info")

            username = st.session_state.get("username", "Unknown")
            role = st.session_state.get("role", "unknown")

            st.markdown(f"**Username:** {username}")
            st.markdown(f"**Account Plan:** {role.capitalize()}")