import streamlit as st
from frontend.utils.helpers import format_currency


def display_account_summary(account_data):
    account_balance = account_data.get("account_balance", {})

    # Account metrics
    st.metric("Net Asset Value", format_currency(account_balance.get("net_asset_value", 0)))
    st.metric("Available Cash", format_currency(account_balance.get("available_cash", 0)))
    st.metric("Cash Ratio", f"{account_balance.get('cash_ratio', 0):.2f}%")

    # Current positions
    current_positions = account_data.get("current_positions", [])
    if current_positions:
        st.markdown("**Current Holdings:**")
        for pos in current_positions[:5]:  # Show top 5
            symbol = pos.get("symbol", "")
            quantity = pos.get("quantity", 0)
            weight = pos.get("weight", {})
            weight_pct = (
                weight.get("percentage", 0) if isinstance(weight, dict) else weight
            )
            st.write(f"• {symbol}: {quantity:,} shares ({weight_pct:.1f}%)")

        if len(current_positions) > 5:
            st.write(f"... and {len(current_positions) - 5} more positions")