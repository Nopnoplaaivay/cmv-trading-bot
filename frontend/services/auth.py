"""
Authentication service for CMV Trading Bot frontend
"""

import streamlit as st
import requests
from typing import Optional, Dict
from ..utils.config import API_BASE_URL


def login_user(username: str, password: str) -> Optional[Dict]:
    """Login user and return authentication data"""
    try:
        print(f"Attempting login... {username}")
        response = requests.post(
            f"{API_BASE_URL}/auth-service/login",
            json={"account": username, "password": password},
            headers={"Content-Type": "application/json"},
            timeout=10,
        )

        if response.status_code == 200:
            return response.json().get("data")
        else:
            error_msg = response.json().get("message", "Unknown error")
            st.error(f"Login failed: {error_msg}")
            return None

    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {str(e)}")
        return None


def logout_user(refresh_token: str) -> bool:
    """Logout user"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/auth-service/logout",
            json={"refreshToken": refresh_token},
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        return response.status_code == 200
    except:
        return False


def get_auth_headers() -> Dict[str, str]:
    """Get authorization headers for API requests"""
    headers = {"Content-Type": "application/json"}
    if "auth_token" in st.session_state and st.session_state.auth_token:
        token = st.session_state.auth_token
        # Debug: Show token info in sidebar (first/last 10 chars only for security)
        if len(token) > 20:
            st.sidebar.caption(f"🔑 Token: {token[:10]}...{token[-10:]}")
        headers["Authorization"] = f"Bearer {token}"
    else:
        st.sidebar.caption("❌ No valid token found")
    return headers


def handle_auth_error(response):
    """Handle authentication errors by clearing session state"""
    if response.status_code == 401:
        # Clear session state for invalid/expired tokens
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.error("🔒 Authentication expired. Please log in again.")
        st.rerun()
        return True
    return False
