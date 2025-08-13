import streamlit as st
import time
from typing import Dict, Optional


from .analysis_cache import (
    clear_all_portfolio_service_cache,
    clear_portfolio_analysis_cache,
)
from .portfolio_edit import render_edit_portfolio_form
from frontend.services.portfolio import PortfolioService


def render_portfolio_list():
    st.markdown("#### 📋 Your Portfolios")

    portfolios = PortfolioService.get_my_portfolios().get("portfolios")

    if not portfolios:
        st.info("🎯 You don't have any custom portfolios yet. Create your first one!")
        return

    with st.expander("🏢 System Portfolio (Default)", expanded=False):
        st.markdown(
            """
        **System Portfolio** contains the top 20 stocks selected by our algorithm each month:
        - ✅ Automatically updated monthly
        - 📊 Based on fundamental analysis
        - 🎯 Optimized for Vietnamese market
        """
        )

    custom_portfolios = [
        p for p in portfolios if p["metadata"].get("portfolioType") == "CUSTOM"
    ]

    if not custom_portfolios:
        st.info("No custom portfolios found.")
        return

    for portfolio in custom_portfolios:
        render_portfolio_card(portfolio)


def render_portfolio_card(portfolio: Dict):
    portfolio_id = portfolio["portfolioId"]

    expander_key = f"expander_{portfolio_id}"
    if expander_key not in st.session_state:
        st.session_state[expander_key] = False

    if st.session_state.get(f"confirm_delete_{portfolio_id}", False):
        st.session_state[expander_key] = True

    with st.expander(
        f"📁 {portfolio['metadata']['portfolioName']}",
        expanded=st.session_state[expander_key],
    ):
        col1, col2, col3 = st.columns([2, 2, 1])

        with col1:
            st.markdown(f"**Portfolio ID:** `{portfolio['portfolioId'][:8]}...`")
            st.markdown(
                f"**Type:** {portfolio['metadata'].get('portfolioType', 'Unknown')}"
            )
            st.markdown(
                f"**Status:** {'🟢 Active' if portfolio['metadata'].get('isActive') else '🔴 Inactive'}"
            )

        with col2:
            records = portfolio.get("records", [])
            st.markdown(f"**Stocks Count:** {len(records)}")
            if records:
                st.markdown(
                    f"**Symbols:** {', '.join(record.get('symbol', '') for record in records[:5])}"
                )
                if len(records) > 5:
                    st.markdown(f"*... and {len(records) - 5} more*")

        with col3:
            if st.button("✏️ Edit", key=f"edit_{portfolio['portfolioId']}"):
                st.session_state[f"editing_{portfolio['portfolioId']}"] = True
                st.session_state[expander_key] = True  # Keep expander open
                st.rerun()

            # Delete button - show modal dialog
            if st.button("🗑️ Delete", key=f"delete_{portfolio['portfolioId']}"):
                confirm_delete_dialog(portfolio)

        # Edit mode
        if st.session_state.get(f"editing_{portfolio['portfolioId']}", False):
            render_edit_portfolio_form(portfolio)


@st.dialog("Delete Portfolio")
def confirm_delete_dialog(portfolio: Dict):
    """Modal dialog for delete confirmation"""
    st.markdown(f"### ⚠️ Delete Portfolio")
    st.error(
        f"Are you sure you want to delete **{portfolio['metadata']['portfolioName']}**?"
    )
    st.markdown("This action cannot be undone!")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🗑️ Yes, Delete", type="primary", use_container_width=True):
            with st.spinner("Deleting portfolio..."):
                result = PortfolioService.delete_portfolio(portfolio["portfolioId"])

            if result["success"]:
                st.success("✅ Portfolio deleted successfully!")

                # Clear analysis cache for deleted portfolio
                clear_portfolio_analysis_cache(portfolio["portfolioId"])

                # Clear service cache to refresh portfolio lists
                clear_all_portfolio_service_cache()

                time.sleep(1.5)
                st.rerun()
            else:
                st.error(f"❌ Failed to delete: {result['error']}")

    with col2:
        if st.button("❌ Cancel", use_container_width=True):
            st.rerun()
