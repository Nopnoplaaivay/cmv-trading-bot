"""
Order history page for CMV Trading Bot frontend
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from ..services.trading import cancel_order


def order_history_page():
    """Order history and status page"""
    st.subheader("📋 Order History & Status")

    if not st.session_state.order_history:
        st.info("No orders placed yet")
        return

    # Order summary metrics
    orders = st.session_state.order_history
    pending_orders = [o for o in orders if o["status"] == "PENDING"]
    filled_orders = [o for o in orders if o["status"] == "FILLED"]
    cancelled_orders = [o for o in orders if o["status"] == "CANCELLED"]

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Orders", len(orders))

    with col2:
        st.metric("Pending", len(pending_orders))

    with col3:
        st.metric("Filled", len(filled_orders))

    with col4:
        st.metric("Cancelled", len(cancelled_orders))

    # Order history table
    df_orders = pd.DataFrame(orders)

    # Add action buttons
    for i, order in enumerate(orders):
        col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 1, 1])

        with col1:
            status_class = f"status-{order['status'].lower()}"
            st.markdown(f"**{order['symbol']}** - {order['action']}")
            st.markdown(
                f"<span class='{status_class}'>●</span> {order['status']}",
                unsafe_allow_html=True,
            )

        with col2:
            st.write(f"Qty: {order['quantity']:,}")
            st.write(f"Price: ${order['price']:.2f}")

        with col3:
            st.write(f"Filled: {order['filled_quantity']:,}")
            st.write(f"Remaining: {order['remaining_quantity']:,}")

        with col4:
            order_time = datetime.fromisoformat(order["timestamp"])
            st.write(order_time.strftime("%m/%d %H:%M"))

        with col5:
            if order["status"] == "PENDING":
                if st.button("Cancel", key=f"cancel_{order['order_id']}"):
                    if cancel_order(order["order_id"]):
                        st.success("Order cancelled")
                        st.rerun()
                    else:
                        st.error("Failed to cancel")

        st.divider()
