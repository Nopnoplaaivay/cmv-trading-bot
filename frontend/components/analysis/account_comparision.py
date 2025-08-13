import streamlit as st

from frontend.components.analysis.portfolio_selector import render_portfolio_selector_for_comparison
from frontend.components.analysis.account_summary import display_account_summary
from frontend.components.analysis.portfolio_summary_comparision import display_portfolio_summary_comparison
from frontend.components.analysis.portfolio_detailed_comparision import render_detailed_comparison
from frontend.services.portfolio import PortfolioService



def render_portfolio_vs_account_comparison():
    """Render comparison between user's real account and selected portfolio"""
    st.subheader("⚖️ Portfolio vs Real Account Comparison")

    # Check if user has broker account
    if not st.session_state.get("broker_account_id"):
        st.warning(
            "⚠️ No broker account information available. Please check the Account Information section in the sidebar."
        )
        st.info(
            "💡 If you just logged in, try refreshing the account information from the sidebar."
        )
        return

    # Portfolio selector for comparison
    st.markdown("#### 📊 Select Portfolio for Comparison")
    selected_portfolio_id = render_portfolio_selector_for_comparison()

    if not selected_portfolio_id:
        st.info("💡 Select your own portfolio to compare with your real account.")
        return

    # Strategy selector
    strategy = st.radio(
        "Select Strategy for Portfolio Analysis",
        options=["LongOnly", "MarketNeutral"],
        index=0,
        horizontal=True,
        key="comparison_strategy_selector",
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 💼 Your Real Account")
        with st.spinner("📊 Loading account data..."):
            account_data = PortfolioService.get_portfolio_analysis(
                broker_account_id=st.session_state.broker_account_id,
                portfolio_id=selected_portfolio_id,
                strategy_type=strategy,
            )

        if account_data:
            display_account_summary(account_data)
        else:
            st.error("❌ Failed to load account data.")

    with col2:
        st.markdown("### 📈 Selected Portfolio")
        with st.spinner("📊 Loading portfolio data..."):
            portfolio_data = PortfolioService.get_portfolio_pnl(
                selected_portfolio_id, strategy
            )

        if portfolio_data:
            display_portfolio_summary_comparison(portfolio_data, selected_portfolio_id)
        else:
            st.error("❌ Failed to load portfolio data.")

    if account_data and portfolio_data:
        st.markdown("---")
        render_detailed_comparison(account_data, portfolio_data, strategy)


