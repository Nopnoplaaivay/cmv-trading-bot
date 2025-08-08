import streamlit as st
import time
import random
from datetime import datetime
from typing import Dict, List
from ..utils.helpers import safe_numeric_value


def place_order_via_dnse(
    symbol: str, action: str, quantity: int, price: float, account_no: str
) -> Dict:
    """
    Place order via DNSE API (Simulated)
    In production, this would use your DNSE API client
    """
    # Simulate order placement with some validation
    order_id = f"DNSE_{int(time.time() * 1000)}"

    # Simulate order status based on various factors
    statuses = ["PENDING", "FILLED", "PARTIALLY_FILLED"]
    weights = [0.7, 0.2, 0.1]
    status = random.choices(statuses, weights=weights)[0]

    order = {
        "order_id": order_id,
        "symbol": symbol,
        "action": action,
        "quantity": quantity,
        "price": price,
        "account_no": account_no,
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "filled_quantity": (
            quantity
            if status == "FILLED"
            else (quantity // 2 if status == "PARTIALLY_FILLED" else 0)
        ),
        "remaining_quantity": (
            0
            if status == "FILLED"
            else (quantity // 2 if status == "PARTIALLY_FILLED" else quantity)
        ),
    }

    # Add to order history
    st.session_state.order_history.append(order)

    return order


def get_order_status(order_id: str) -> Dict:
    for order in st.session_state.order_history:
        if order["order_id"] == order_id:
            return order
    return {}


def cancel_order(order_id: str) -> bool:
    for order in st.session_state.order_history:
        if order["order_id"] == order_id and order["status"] == "PENDING":
            order["status"] = "CANCELLED"
            return True
    return False


def execute_single_order(recommendation: Dict, action_type: str):
    if not st.session_state.get("broker_account_id"):
        st.error("Please set broker account ID first")
        return

    with st.spinner(f"Executing {action_type} order for {recommendation['symbol']}..."):
        result = place_order_via_dnse(
            symbol=recommendation["symbol"],
            action=action_type,
            quantity=int(safe_numeric_value(recommendation.get("action_quantity", 0))),
            price=safe_numeric_value(recommendation.get("action_price", 0)),
            account_no=st.session_state.broker_account_id,
        )

        if result.get("status") in ["PENDING", "FILLED"]:
            st.success(f"✅ Order placed successfully! Order ID: {result['order_id']}")
        else:
            st.error(f"❌ Order failed: {result.get('status', 'Unknown error')}")


def execute_bulk_orders(recommendations: List[Dict]):
    if not st.session_state.get("broker_account_id"):
        st.error("Please set broker account ID first")
        return

    progress_bar = st.progress(0)
    status_text = st.empty()

    results = []
    successful_orders = 0

    for i, rec in enumerate(recommendations):
        status_text.text(
            f"Executing order {i+1}/{len(recommendations)}: {rec['symbol']}"
        )

        result = place_order_via_dnse(
            symbol=rec["symbol"],
            action=rec["action"],
            quantity=int(safe_numeric_value(rec.get("action_quantity", 0))),
            price=safe_numeric_value(rec.get("action_price", 0)),
            account_no=st.session_state.broker_account_id,
        )

        results.append(result)
        if result.get("status") in ["PENDING", "FILLED"]:
            successful_orders += 1

        progress_bar.progress((i + 1) / len(recommendations))
        time.sleep(0.5)  # Simulate API delay

    status_text.empty()
    progress_bar.empty()

    # Display results summary
    st.subheader("📊 Execution Summary")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Orders", len(results))
    with col2:
        st.metric("Successful", successful_orders)
    with col3:
        st.metric("Failed", len(results) - successful_orders)

    # Detailed results
    for result in results:
        status = result.get("status", "UNKNOWN")
        if status in ["PENDING", "FILLED"]:
            st.success(f"✅ {result['symbol']}: Order {result['order_id']} - {status}")
        else:
            st.error(f"❌ {result['symbol']}: Order failed - {status}")
