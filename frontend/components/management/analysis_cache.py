import streamlit as st
from frontend.services.portfolio import PortfolioService


def clear_portfolio_analysis_cache(portfolio_id: str):
    keys_to_remove = []
    for key in st.session_state.keys():
        if portfolio_id in key and any(
            prefix in key
            for prefix in ["portfolio_data", "risk_metrics", "performance_data"]
        ):
            keys_to_remove.append(key)

    for key in keys_to_remove:
        del st.session_state[key]


def clear_all_portfolio_service_cache():
    try:
        PortfolioService.get_my_portfolios.clear()
        PortfolioService.get_portfolio_pnl.clear()
        PortfolioService.get_system_portfolios.clear()
        PortfolioService.get_all_symbols.clear()
    except AttributeError:
        pass
