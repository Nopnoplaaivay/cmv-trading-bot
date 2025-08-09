import streamlit as st

from frontend.components.portfolio_quick_stats import render_portfolio_quick_stats
from frontend.components.portfolio_management import render_portfolio_selector

def render_enhanced_sidebar():
    with st.sidebar:
        st.markdown(f"### 👋 Welcome, {st.session_state.get('username', 'User')}!")

        st.markdown("### 🧭 Navigation")
        pages = [
            "Portfolio Analysis",
            "Portfolio Management",  # New page
            "Trade Execution",
            "Order History",
            "Account Management",
        ]
        
        selected_page = st.selectbox(
            "Go to",
            pages,
            index=pages.index(st.session_state.get("current_page", "Portfolio Analysis")),
        )
        st.session_state.current_page = selected_page

        st.divider()

        # Portfolio Selection (only show on analysis page)
        if selected_page == "Portfolio Analysis":
            st.markdown("### 📊 Portfolio Selection")
            render_portfolio_selector()

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
                0 if st.session_state.get("strategy_type", "market_neutral") == "market_neutral" else 1
            ),
        )
        st.session_state.strategy_type = strategy_type

        st.divider()

        # Portfolio Quick Stats
        if selected_page == "Portfolio Analysis":
            render_portfolio_quick_stats()

        # Rest of sidebar (existing code)
        render_quick_actions()
        render_system_status()
        render_logout_button()



def render_quick_actions():
    """Render quick action buttons"""
    st.markdown("### ⚡ Quick Actions")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Refresh", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    with col2:
        if st.button("➕ New Portfolio", use_container_width=True):
            st.session_state.current_page = "Portfolio Management"
            st.rerun()


def render_system_status():
    """Render system status"""
    st.markdown("### 🟢 System Status")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("API", "🟢 Online")
    with col2:
        st.metric("Portfolios", len(st.session_state.get("portfolios", [])))


def render_logout_button():
    """Render logout functionality"""
    st.divider()
    
    if st.button("🚪 Logout", use_container_width=True, type="secondary"):
        from ..services.auth import logout_user
        
        if st.session_state.get("refresh_token"):
            logout_user(st.session_state.refresh_token)

        # Clear all session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()