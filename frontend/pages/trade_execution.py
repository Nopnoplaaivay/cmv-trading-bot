"""
Trade execution page for CMV Trading Bot frontend
"""

import streamlit as st
from ..services.trading import place_order_via_dnse


def trade_execution_page():
    """Trade execution and order management page"""
    st.subheader("⚡ Trade Execution Center")

    # Quick order form
    st.markdown("#### 🎯 Quick Order Entry")

    with st.form("quick_order_form"):
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            symbol = st.text_input("Symbol", placeholder="e.g., VIC")

        with col2:
            action = st.selectbox("Action", ["BUY", "SELL"])

        with col3:
            quantity = st.number_input("Quantity", min_value=1, value=100)

        with col4:
            price = st.number_input("Price", min_value=0.01, value=10.0, step=0.01)

        col_a, col_b, col_c = st.columns([1, 1, 1])
        with col_b:
            submit_order = st.form_submit_button(
                "🚀 Place Order", use_container_width=True
            )

        if submit_order and symbol and st.session_state.get("broker_account_id"):
            result = place_order_via_dnse(
                symbol=symbol,
                action=action,
                quantity=quantity,
                price=price,
                account_no=st.session_state.broker_account_id,
            )

            if result.get("status") in ["PENDING", "FILLED"]:
                st.success(f"✅ Order placed! Order ID: {result['order_id']}")
            else:
                st.error(f"❌ Order failed: {result.get('status', 'Unknown error')}")
