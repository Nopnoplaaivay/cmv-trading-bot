"""
Utility functions for CMV Trading Bot frontend
"""

from typing import Dict, Any


def format_currency(amount: float) -> str:
    """Format currency with proper formatting"""
    return f"${amount:,.2f}"


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
        for key in ["value", "amount", "total", "price"]:
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

    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "order_history" not in st.session_state:
        st.session_state.order_history = []
    if "selected_recommendations" not in st.session_state:
        st.session_state.selected_recommendations = []
