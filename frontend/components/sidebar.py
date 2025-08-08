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
        st.markdown("### ⚙️ Account Information")

        # Display account information if available
        if st.session_state.get("broker_account_id"):
            st.markdown("#### 🏦 Default Account")

            col1, col2 = st.columns([1, 2])
            with col1:
                st.write("**Account ID:**")
                st.write("**Name:**")
                st.write("**Broker:**")
                st.write("**Investor ID:**")
            with col2:
                st.write(st.session_state.get("broker_account_id", "N/A"))
                st.write(st.session_state.get("account_name", "N/A"))
                st.write(st.session_state.get("broker_name", "N/A"))
                st.write(st.session_state.get("broker_investor_id", "N/A"))

            # Option to refresh account info
            if st.button("🔄 Refresh Account Info", use_container_width=True):
                with st.spinner("Loading account information..."):
                    from ..services.auth import get_default_account

                    account_data = get_default_account()
                    if account_data:
                        st.session_state.broker_account_id = account_data.get(
                            "broker_account_id"
                        )
                        st.session_state.account_name = account_data.get("name")
                        st.session_state.broker_name = account_data.get("broker_name")
                        st.session_state.broker_investor_id = account_data.get(
                            "broker_investor_id"
                        )
                        st.success("Account information refreshed!")
                        st.rerun()
                    else:
                        st.error("Failed to refresh account information")
        else:
            st.warning("⚠️ No account information available")
            # Option to manually set if auto-fetch failed
            manual_id = st.text_input(
                "🔧 Manual Broker Account ID",
                placeholder="Enter account ID if auto-fetch failed",
            )
            if manual_id:
                st.session_state.broker_account_id = manual_id
                st.success("Account ID set manually")

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
            # Preserve auth state before clearing cache
            from ..utils.helpers import preserve_auth_state, restore_auth_state

            auth_backup = preserve_auth_state()

            # Only clear portfolio analysis cache, not all cache
            from ..services.api import get_portfolio_analysis

            get_portfolio_analysis.clear()

            # Restore auth state
            restore_auth_state(auth_backup)

            st.success("Data refreshed!")

        if st.button("📊 Force Analysis", use_container_width=True):
            if st.session_state.get("broker_account_id"):
                with st.spinner("Running portfolio analysis..."):
                    # Clear specific cache and force refresh
                    from ..services.api import get_portfolio_analysis

                    get_portfolio_analysis.clear()
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

            # Clear authentication and account-related session state
            auth_keys = [
                "authenticated",
                "auth_token",
                "refresh_token",
                "username",
                "broker_account_id",
                "account_name",
                "broker_name",
                "broker_investor_id",
            ]
            for key in auth_keys:
                if key in st.session_state:
                    del st.session_state[key]

            # Set authenticated to False
            st.session_state.authenticated = False
            st.rerun()
