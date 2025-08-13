import streamlit as st


def display_portfolio_summary_comparison(portfolio_data, portfolio_id):
    st.write(f"**Portfolio ID:** {portfolio_id}")

    risk_metrics = portfolio_data["risk_metrics"]["portfolio"]
    if risk_metrics:
        st.metric("Win Rate", f"{risk_metrics.get('win_rate_pct', 0):.2f}%")
        st.metric("Max Return", f"{risk_metrics.get('max_return_pct', 0):.2f}%")
        st.metric("Max Drawdown", f"{risk_metrics.get('max_dd_pct', 0):.2f}%")
        st.metric("Daily Volatility", f"{risk_metrics.get('daily_volatility_pct', 0):.2f}%")
        st.metric("Sharpe Ratio", f"{risk_metrics.get('sharpe_ratio', 0):.3f}")
        st.metric("Sortino Ratio", f"{risk_metrics.get('sortino_ratio', 0):.3f}")

    portfolio_df = portfolio_data.get("portfolio_pnl_df")
    if portfolio_df and isinstance(portfolio_df, list) and len(portfolio_df) > 0:
        st.markdown("**Portfolio Holdings:**")
        latest_data = portfolio_df[-1] if portfolio_df else {}
        symbols = portfolio_data.get("metadata", {}).get("symbols", [])

        for symbol in symbols[:5]: 
            st.write(f"• {symbol}")

        if len(symbols) > 5:
            st.write(f"... and {len(symbols) - 5} more stocks")
