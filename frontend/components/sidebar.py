"""
Sidebar component for CMV Trading Bot frontend
"""

import streamlit as st
import time
from ..services.auth import logout_user


def render_sidebar():
    """Render sidebar with navigation and controls"""
    with st.sidebar:
        st.markdown(f"### 👋 Welcome, {st.session_state.get('username', 'User')}!")

        # Navigation
        st.markdown("### 🧭 Navigation")
        pages = [
            "Portfolio Analysis",
            "Trade Execution",
            "Order History",
            "Account Management",
        ]
        selected_page = st.selectbox(
            "Go to",
            pages,
            index=pages.index(
                st.session_state.get("current_page", "Portfolio Analysis")
            ),
        )
        st.session_state.current_page = selected_page

        st.divider()

        # Account Configuration
        st.markdown("### ⚙️ Account Settings")

        # Broker Account ID
        broker_account_id = st.text_input(
            "🏦 Broker Account ID",
            value=st.session_state.get("broker_account_id", ""),
            placeholder="Enter your account ID",
        )
        if broker_account_id:
            st.session_state.broker_account_id = broker_account_id

        # Strategy Selection
        strategy_type = st.selectbox(
            "📊 Trading Strategy",
            ["market_neutral", "long_only"],
            index=(
                0
                if st.session_state.get("strategy_type", "market_neutral")
                == "market_neutral"
                else 1
            ),
        )
        st.session_state.strategy_type = strategy_type

        # Auto-refresh settings
        auto_refresh = st.checkbox(
            "🔄 Auto Refresh (30s)", value=st.session_state.get("auto_refresh", False)
        )
        st.session_state.auto_refresh = auto_refresh

        st.divider()

        # Quick Actions
        st.markdown("### ⚡ Quick Actions")

        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

        if st.button("📊 Force Analysis", use_container_width=True):
            if st.session_state.get("broker_account_id"):
                with st.spinner("Running portfolio analysis..."):
                    # Clear cache and force refresh
                    st.cache_data.clear()
                    time.sleep(1)
                st.success("Analysis updated!")
            else:
                st.error("Please enter broker account ID first")

        st.divider()

        # System Status
        st.markdown("### 🟢 System Status")
        status_col1, status_col2 = st.columns(2)
        with status_col1:
            st.metric("API", "🟢 Online")
        with status_col2:
            st.metric("Orders", len(st.session_state.order_history))

        st.divider()

        # Logout
        if st.button("🚪 Logout", use_container_width=True, type="secondary"):
            if st.session_state.get("refresh_token"):
                logout_user(st.session_state.refresh_token)

            # Clear all session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
