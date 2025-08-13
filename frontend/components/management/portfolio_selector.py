import streamlit as st
from typing import Optional

from frontend.services.portfolio import PortfolioService


def render_portfolio_selector() -> Optional[str]:
    """Render portfolio selector in sidebar"""
    personal_portfolios = PortfolioService.get_my_portfolios().get("portfolios")
    system_portfolios = PortfolioService.get_system_portfolios().get("portfolios")
    portfolios = personal_portfolios + system_portfolios

    portfolio_options = [
        f"{p['metadata'].get('portfolioName', 'Unknown')} ({len(p.get('records', []))})"
        for p in portfolios
    ]

    if not personal_portfolios:
        st.sidebar.info(
            "💡 You can analyze the System Portfolio or create your first custom portfolio!"
        )

    selected_option = st.sidebar.selectbox(
        "📊 Select Portfolio", portfolio_options, key="portfolio_selector"
    )

    for portfolio in portfolios:
        option_text = f"{portfolio['metadata'].get('portfolioName', 'Unknown')} ({len(portfolio.get('records', []))})"
        if option_text == selected_option:
            return portfolio.get("portfolioId")

    return None
