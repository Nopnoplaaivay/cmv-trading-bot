import streamlit as st
from frontend.services.portfolio import PortfolioService


def render_portfolio_quick_stats():
    st.markdown("### 📊 Quick Stats")
    
    portfolios = PortfolioService.get_my_portfolios().get('portfolios')
    
    if portfolios:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("My Portfolios", len(portfolios))
        with col2:
            for portfolio in portfolios:
                portfolio_metadata = portfolio.get('metadata', {})
                st.text(f"Portfolio: {portfolio_metadata.get('portfolioName', 'Unnamed Portfolio')}")