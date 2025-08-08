"""
Utility functions for CMV Trading Bot frontend
"""

from typing import Dict, Any


def format_currency(amount: float) -> str:
    """Format currency with proper formatting"""
    return f"{amount:,.2f} VND"  # Assuming VND as the currency, adjust as needed


def format_percentage(percentage: float) -> str:
    """Format percentage with proper formatting"""
    return f"{percentage:.2f}%"


def safe_numeric_value(value, default=0) -> float:
    """Safely extract numeric value from various data types"""
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except (ValueError, TypeError):
            return default
    if isinstance(value, dict):
        # If it's a dict, try to extract a numeric value from common keys
        for key in ["value", "amount", "total", "price", "weight", "percentage"]:
            if key in value:
                return safe_numeric_value(value[key], default)
            
        return default
    return default


def get_priority_color(priority: str) -> str:
    """Get color based on priority"""
    colors = {"HIGH": "#f44336", "MEDIUM": "#ff9800", "LOW": "#4caf50"}
    return colors.get(priority.upper(), "#6c757d")


def init_session_state():
    """Initialize session state variables"""
    import streamlit as st

    # Initialize core auth state
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    # Initialize other required state
    if "order_history" not in st.session_state:
        st.session_state.order_history = []
    if "selected_recommendations" not in st.session_state:
        st.session_state.selected_recommendations = []

    # Initialize UI state
    if "current_page" not in st.session_state:
        st.session_state.current_page = "Portfolio Analysis"

    # Initialize debug counters
    if "token_missing_count" not in st.session_state:
        st.session_state.token_missing_count = 0

    # Initialize account information
    if "broker_account_id" not in st.session_state:
        st.session_state.broker_account_id = None
    if "account_name" not in st.session_state:
        st.session_state.account_name = None
    if "broker_name" not in st.session_state:
        st.session_state.broker_name = None
    if "broker_investor_id" not in st.session_state:
        st.session_state.broker_investor_id = None

    # Validate auth state consistency
    if st.session_state.get("authenticated", False):
        # If marked as authenticated but missing token, track this
        if not st.session_state.get("auth_token"):
            st.session_state.token_missing_count += 1


def track_session_state_change(key: str, old_value=None, new_value=None):
    """Track when important session state changes"""
    import streamlit as st

    debug_mode = st.session_state.get("debug_mode", False)
    if debug_mode:
        st.sidebar.caption(f"📝 {key}: {old_value} → {new_value}")


def preserve_auth_state():
    """Ensure auth state is preserved across operations"""
    import streamlit as st

    # Store current auth state
    auth_backup = {
        "authenticated": st.session_state.get("authenticated", False),
        "auth_token": st.session_state.get("auth_token"),
        "refresh_token": st.session_state.get("refresh_token"),
        "username": st.session_state.get("username"),
    }

    return auth_backup


def restore_auth_state(auth_backup: dict):
    """Restore auth state from backup"""
    import streamlit as st

    for key, value in auth_backup.items():
        if value is not None:
            st.session_state[key] = value
