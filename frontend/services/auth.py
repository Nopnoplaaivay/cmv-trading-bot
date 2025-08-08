"""
Authentication service for CMV Trading Bot frontend
"""

import streamlit as st
import requests
from typing import Optional, Dict
from ..utils.config import API_BASE_URL


def login_user(username: str, password: str) -> Optional[Dict]:
    try:
        print(
            f"Attempting login... {username} {password}: {API_BASE_URL}/auth-service/login"
        )
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


def logout_user(logout_payload: Dict) -> bool:
    try:
        response = requests.post(
            f"{API_BASE_URL}/auth-service/logout",
            json=logout_payload,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )
        return response.status_code == 200
    except:
        return False


def get_default_account() -> Optional[Dict]:
    try:
        response = requests.get(
            f"{API_BASE_URL}/accounts-service/default",
            headers=get_auth_headers(),
            timeout=10,
        )
        if response.status_code == 200:
            return response.json().get("data")
        else:
            st.error("Failed to fetch default account")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Connection error: {str(e)}")
        return None


def get_auth_headers() -> Dict[str, str]:
    headers = {"Content-Type": "application/json"}
    debug_mode = st.session_state.get("debug_mode", False)

    if "auth_token" in st.session_state and st.session_state.auth_token:
        token = st.session_state.auth_token
        # Debug: Show token info in sidebar (first/last 10 chars only for security)
        if debug_mode:
            if len(token) > 20:
                st.sidebar.caption(f"🔑 Token: {token[:10]}...{token[-10:]}")
            else:
                st.sidebar.caption(f"🔑 Token: {token}")
        headers["Authorization"] = f"Bearer {token}"
    else:
        if debug_mode:
            st.sidebar.caption("❌ No valid token found")
            # Debug: Show what auth-related keys exist
            auth_keys = [
                k
                for k in st.session_state.keys()
                if "auth" in k.lower() or k in ["authenticated", "username"]
            ]
            if auth_keys:
                st.sidebar.caption(f"🔍 Auth keys: {auth_keys}")
            else:
                st.sidebar.caption("🔍 No auth keys found at all")
    return headers


def handle_auth_error(response):
    if response.status_code == 401:
        debug_mode = st.session_state.get("debug_mode", False)
        if debug_mode:
            st.sidebar.error(f"🔒 Got 401 error from API")

        # Only clear auth-related session state, preserve other data
        auth_keys = ["auth_token", "refresh_token"]
        cleared_keys = []
        for key in auth_keys:
            if key in st.session_state:
                del st.session_state[key]
                cleared_keys.append(key)

        if cleared_keys and debug_mode:
            st.sidebar.caption(f"🗑️ Cleared keys: {cleared_keys}")

        # Set authenticated to False instead of deleting everything
        st.session_state.authenticated = False
        st.error("🔒 Authentication expired. Please log in again.")

        # Don't call st.rerun() here - let the main app handle the redirect
        # st.rerun() causes infinite loops
        return True
    return False
