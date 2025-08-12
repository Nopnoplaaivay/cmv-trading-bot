"""
Recommendations component for CMV Trading Bot frontend
"""

import streamlit as st
import pandas as pd
from typing import Dict, List
from ..utils.helpers import format_currency, safe_numeric_value
from ..services.trading import execute_single_order, execute_bulk_orders


def display_recommendations_tab(recommendations: List[Dict]):
    """Display trade recommendations in a tab"""
    if not recommendations:
        st.info("🎯 No trade recommendations available")
        return

    # Debug: Show sample recommendation structure
    if st.sidebar.checkbox("🔍 Debug Mode", value=False):
        with st.expander("Debug: Recommendation Data Structure"):
            if recommendations:
                st.json(recommendations[0])  # Show first recommendation structure

    # Filter recommendations
    buy_recs = [r for r in recommendations if r.get("action") == "BUY"]
    sell_recs = [r for r in recommendations if r.get("action") == "SELL"]

    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("🛒 Buy Orders", len(buy_recs))

    with col2:
        st.metric("💰 Sell Orders", len(sell_recs))

    with col3:
        total_buy_value = sum(safe_numeric_value(r.get("amount", 0)) for r in buy_recs)
        st.metric("💵 Buy Value", format_currency(total_buy_value))

    with col4:
        total_sell_value = sum(
            safe_numeric_value(r.get("amount", 0)) for r in sell_recs
        )
        st.metric("💎 Sell Value", format_currency(total_sell_value))

    # Recommendations tabs
    rec_tab1, rec_tab2, rec_tab3 = st.tabs(
        ["🛒 Buy Orders", "💰 Sell Orders", "⚡ Execute"]
    )

    with rec_tab1:
        if buy_recs:
            display_recommendation_cards(buy_recs, "BUY")
        else:
            st.info("No buy recommendations")

    with rec_tab2:
        if sell_recs:
            display_recommendation_cards(sell_recs, "SELL")
        else:
            st.info("No sell recommendations")

    with rec_tab3:
        display_execution_interface(recommendations)


def display_recommendation_cards(recommendations: List[Dict], action_type: str):
    """Display recommendation cards with selection"""
    for i, rec in enumerate(recommendations):
        priority = rec.get("priority", "LOW")
        priority_class = f"recommendation-{priority.lower()}"

        st.markdown(f'<div class="{priority_class}">', unsafe_allow_html=True)

        col1, col2, col3, col4 = st.columns([1, 3, 3, 2])

        with col1:
            key = f"{action_type}_{rec['symbol']}_{i}"
            selected = st.checkbox(
                "Select",
                key=key,
                value=rec.get("selected", False),
                label_visibility="hidden",
            )
            rec["selected"] = selected
            if selected and rec not in st.session_state.selected_recommendations:
                st.session_state.selected_recommendations.append(rec)
            elif not selected and rec in st.session_state.selected_recommendations:
                st.session_state.selected_recommendations.remove(rec)

        with col2:
            st.markdown(f"**{rec['symbol']}**")
            st.markdown(f"Priority: **{priority}**")
            st.markdown(f"Action: **{action_type}**")

        with col3:
            quantity = safe_numeric_value(rec.get("action_quantity", 0))
            price = safe_numeric_value(rec.get("action_price", 0))
            st.markdown(f"Quantity: **{quantity:,.0f}**")
            st.markdown(f"Price: **{format_currency(price)}**")
            st.markdown(f"Value: **{format_currency(quantity * price)}**")

        with col4:
            if st.button(f"Execute", key=f"exec_{key}", use_container_width=True):
                execute_single_order(rec, action_type)

        # Show recommendation reason
        reason = rec.get("reason", "No reason provided")
        st.caption(f"💡 **Reason:** {reason}")

        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("---")


def display_execution_interface(recommendations: List[Dict]):
    """Display bulk execution interface"""
    selected_recs = [r for r in recommendations if r.get("selected", False)]

    if not selected_recs:
        st.info("Select recommendations from the Buy/Sell tabs to execute them")
        return

    st.subheader(f"🎯 Selected Orders ({len(selected_recs)})")

    # Summary table
    df_selected = pd.DataFrame(selected_recs)

    # Clean up the data for display - handle any non-numeric amounts
    if "amount" in df_selected.columns:
        df_selected["amount"] = df_selected["amount"].apply(
            lambda x: safe_numeric_value(x, 0)
        )

    # Ensure other numeric columns are also clean
    for col in ["action_quantity", "action_price"]:
        if col in df_selected.columns:
            df_selected[col] = df_selected[col].apply(
                lambda x: safe_numeric_value(x, 0)
            )

    st.dataframe(
        df_selected[
            [
                "symbol",
                "action",
                "action_quantity",
                "action_price",
                "amount",
                "priority",
            ]
        ],
        use_container_width=True,
        hide_index=True,
        column_config={
            "symbol": "Symbol",
            "action": "Action",
            "action_quantity": st.column_config.NumberColumn("Quantity", format="%d"),
            "action_price": st.column_config.NumberColumn("Price", format="$%.2f"),
            "amount": st.column_config.NumberColumn("Amount", format="$%.2f"),
            "priority": "Priority",
        },
    )

    # Execution controls
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        if st.button(
            "🚀 Execute All Selected Orders", use_container_width=True, type="primary"
        ):
            execute_bulk_orders(selected_recs)
