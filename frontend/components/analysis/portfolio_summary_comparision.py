import streamlit as st


def display_portfolio_summary_comparison(portfolio_data, portfolio_id):
    st.write(f"**Portfolio ID:** `{portfolio_id[:8]}...`")

    risk_metrics = portfolio_data.get("risk_metrics", {})
    if risk_metrics:
        st.metric(
            "Expected Return", f"{risk_metrics.get('portfolio_expected_return', 0):.2%}"
        )
        st.metric("Volatility", f"{risk_metrics.get('portfolio_volatility', 0):.2%}")
        st.metric("Sharpe Ratio", f"{risk_metrics.get('sharpe_ratio', 0):.3f}")

    portfolio_df = portfolio_data.get("portfolio_pnl_df")
    if portfolio_df and isinstance(portfolio_df, list) and len(portfolio_df) > 0:
        st.markdown("**Portfolio Holdings:**")
        latest_data = portfolio_df[-1] if portfolio_df else {}
        symbols = portfolio_data.get("metadata", {}).get("symbols", [])

        for symbol in symbols[:5]: 
            st.write(f"• {symbol}")

        if len(symbols) > 5:
            st.write(f"... and {len(symbols) - 5} more stocks")
