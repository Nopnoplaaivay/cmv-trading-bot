import streamlit as st

from frontend.services.portfolio import PortfolioService


def render_sidebar():
    with st.sidebar:
        st.markdown(f"### 👋 Welcome, {st.session_state.get('username', 'User')}!")
        st.markdown("### 🧭 Navigation")
        pages = [
            "Portfolio Analysis",
            "Account Management"
        ]

        if st.session_state.get("role") == "premium":
            pages.append("Portfolio Management")

        if st.session_state.get("role") == "admin":
            pages.append("Portfolio Management")
            pages.append("User Management")

        current_page = st.session_state.get("current_page", "Portfolio Analysis")
        if current_page not in pages:
            current_page = "Portfolio Analysis"

        selected_page = st.selectbox(
            "Go to",
            pages,
            index=pages.index(current_page),
        )
        st.session_state.current_page = selected_page

        if st.session_state.get("broker_account_id"):
            st.divider()
            st.markdown("### ⚙️ Account Settings")
            st.text(f"Your Broker Account ID: {st.session_state.broker_account_id}")

        st.divider()
        if selected_page == "Portfolio Analysis":
            render_portfolio_quick_stats()

        render_quick_actions()
        render_logout_button()


def render_quick_actions():
    st.markdown("### ⚡ Quick Actions")
    if st.session_state.get("role") in ["premium", "admin"]:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Refresh", use_container_width=True):
                st.cache_data.clear()
                st.rerun()
        with col2:
            if st.button("➕ New Portfolio", use_container_width=True):
                st.session_state.current_page = "Portfolio Management"
                st.rerun()
    else:
        if st.button("🔄 Refresh", use_container_width=True):
            st.cache_data.clear()
            st.rerun()


def render_logout_button():
    st.divider()

    if st.button(
        "🚪 Logout",
        use_container_width=True,
        type="secondary",
        key="sidebar_logout_btn",
    ):
        from ..services.auth import logout_user

        logout_payload = {
            "sessionId": st.session_state.get("session_id", ""),
            "userId": st.session_state.get("user_id", ""),
            "role": st.session_state.get("role", ""),
        }
        logout_user(logout_payload)


        for key in list(st.session_state.keys()):
            del st.session_state[key]

        st.cache_data.clear()
        st.rerun()


def render_portfolio_quick_stats():
    st.markdown("### 📊 Quick Stats")

    portfolios = PortfolioService.get_my_portfolios().get("portfolios")

    if portfolios:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("My Portfolios", len(portfolios))
        with col2:
            for portfolio in portfolios:
                portfolio_metadata = portfolio.get("metadata", {})
                st.text(
                    f"Portfolio: {portfolio_metadata.get('portfolioName', 'Unnamed Portfolio')}"
                )
