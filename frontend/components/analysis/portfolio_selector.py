import streamlit as st

from frontend.services.portfolio import PortfolioService


def render_portfolio_selector_for_comparison():
    personal_portfolios = PortfolioService.get_my_portfolios().get("portfolios", [])
    system_portfolios = PortfolioService.get_system_portfolios().get("portfolios", [])
    portfolios = personal_portfolios + system_portfolios

    if not portfolios:
        st.warning("No portfolios available. Create a portfolio first.")
        return None

    # Create portfolio options
    portfolio_options = {}
    for portfolio in portfolios:
        try:
            name = portfolio["metadata"].get("portfolioName", "Unknown")
            portfolio_id = portfolio["portfolioId"]
            num_stocks = len(portfolio.get("records", []))
            display_name = f"{name} ({num_stocks} stocks)"
            portfolio_options[display_name] = portfolio_id
        except Exception as e:
            st.error(f"Error processing portfolio: {e}")

    if not portfolio_options:
        return None

    selected_display_name = st.selectbox(
        "📊 Select Portfolio for Comparison",
        options=list(portfolio_options.keys()),
        key="comparison_portfolio_selector",
        help="Choose a portfolio to compare with your real account holdings",
    )

    return portfolio_options[selected_display_name] if selected_display_name else None
