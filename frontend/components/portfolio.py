"""
Portfolio components for CMV Trading Bot frontend
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List
from ..utils.helpers import format_currency, format_percentage, safe_numeric_value


def display_portfolio_summary(analysis_data: Dict):
    """Display portfolio summary metrics"""
    st.subheader("💰 Portfolio Summary")

    account_balance = analysis_data.get("account_balance", {})

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        cash = account_balance.get("available_cash", 0)
        st.metric(
            "💵 Available Cash",
            format_currency(cash),
            delta=None,
            help="Available cash for new investments",
        )

    with col2:
        nav = account_balance.get("net_asset_value", 0)
        st.metric(
            "💎 Net Asset Value",
            format_currency(nav),
            delta=None,
            help="Total portfolio value",
        )

    with col3:
        cash_ratio = account_balance.get("cash_ratio", 0)
        st.metric(
            "💰 Cash Ratio",
            format_percentage(cash_ratio),
            delta=None,
            help="Percentage of portfolio in cash",
        )

    with col4:
        strategy = analysis_data.get("strategy_type", "N/A").replace("_", " ").title()
        st.metric("📊 Strategy", strategy, delta=None, help="Current trading strategy")


def display_current_positions(positions: List[Dict]):
    """Display current portfolio positions"""
    if not positions:
        st.info("📋 No current positions found")
        return

    st.subheader("📊 Current Portfolio Positions")

    # Create DataFrame
    df_positions = pd.DataFrame(positions)

    if "market_price" in df_positions.columns:
        df_positions = df_positions.drop(columns=["market_price"])

    df_positions["cost_price"] = df_positions["cost_price"].apply(
        lambda x: safe_numeric_value(x, default=0)
    )
    df_positions["break_even_price"] = df_positions["break_even_price"].apply(
        lambda x: safe_numeric_value(x, default=0)
    )
    df_positions["market_value"] = df_positions["market_value"].apply(
        lambda x: safe_numeric_value(x, default=0)
    )
    df_positions["realized_profit"] = df_positions["realized_profit"].apply(
        lambda x: safe_numeric_value(x, default=0)
    )
    df_positions["unrealized_profit"] = df_positions["unrealized_profit"].apply(
        lambda x: safe_numeric_value(x, default=0)
    )
    df_positions["weight"] = df_positions["weight"].apply(
        lambda x: safe_numeric_value(x, default=0)
    )
    df_positions["weight_over_sv"] = df_positions["weight_over_sv"].apply(
        lambda x: safe_numeric_value(x, default=0)
    )

    print(df_positions.head())  # Debugging line to check DataFrame structure

    # Convert numeric columns to proper dtypes
    numeric_columns = [
        "quantity",
        "cost_price",
        "break_even_price",
        "market_value",
        "realized_profit",
        "unrealized_profit",
    ]
    weight_columns = ["weight_percentage", "weight"]

    for col in numeric_columns:
        if col in df_positions.columns:
            df_positions[col] = pd.to_numeric(df_positions[col], errors="coerce")

    for col in weight_columns:
        if col in df_positions.columns:
            df_positions[col] = pd.to_numeric(df_positions[col], errors="coerce")

    # Portfolio weight distribution chart
    col1, col2 = st.columns([1, 1])

    with col1:
        if "weight_percentage" in df_positions.columns:
            weight_col = "weight_percentage"
        elif "weight" in df_positions.columns:
            weight_col = "weight"
        else:
            weight_col = None

        if weight_col:
            fig_pie = px.pie(
                df_positions,
                values=weight_col,
                names="symbol",
                title="Portfolio Weight Distribution",
                color_discrete_sequence=px.colors.qualitative.Set3,
            )
            fig_pie.update_traces(textposition="inside", textinfo="percent+label")
            fig_pie.update_layout(showlegend=True, height=400)
            st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        if (
            "market_value" in df_positions.columns
            and not df_positions["market_value"].isna().all()
        ):
            try:
                top_positions = df_positions.nlargest(5, "market_value")
                fig_bar = px.bar(
                    top_positions,
                    x="symbol",
                    y="market_value",
                    title="Top 5 Positions by Value",
                    color="market_value",
                    color_continuous_scale="Blues",
                )
                fig_bar.update_layout(height=400)
                st.plotly_chart(fig_bar, use_container_width=True)
            except (TypeError, ValueError) as e:
                st.warning(
                    "Unable to display top positions chart due to data format issues"
                )

    st.markdown("#### 📋 Detailed Positions")

    display_df = df_positions.copy()

    column_config = {
        "symbol": st.column_config.TextColumn("Symbol", width="small"),
        "quantity": st.column_config.NumberColumn("Khối lượng", format="%d"),
        "cost_price": st.column_config.NumberColumn("Giá vốn TB", format="%.2f"),
        "break_even_price": st.column_config.NumberColumn("Giá hòa vốn", format="%.2f"),
        "weight": st.column_config.NumberColumn("Trọng số (%)/ Tài sản ròng", format="%.2f%%"),
        "weight_over_sv": st.column_config.NumberColumn("Trọng số (%)/ Giá trị cổ phiếu", format="%.2f%%"),
        "market_value": st.column_config.NumberColumn("Giá trị thị trường", format="%.2f"),
        "realized_profit": st.column_config.NumberColumn("Lãi thực hiện", format="%.2f"),
        "unrealized_profit": st.column_config.NumberColumn("Lãi chưa thực hiện", format="%.2f")

    }

    if "weight_percentage" in display_df.columns:
        column_config["weight_percentage"] = st.column_config.NumberColumn(
            "Weight %", format="%.2f%%"
        )
    elif "weight" in display_df.columns:
        column_config["weight"] = st.column_config.NumberColumn(
            "Weight %", format="%.2f%%"
        )

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config=column_config,
    )


def display_weight_comparison_chart(
    current_positions: List[Dict], target_weights: List[Dict]
):
    """Display current vs target weight comparison"""
    st.markdown("#### 🎯 Target vs Current Allocation")

    # Prepare comparison data
    current_dict = {}
    for pos in current_positions:
        weight_key = "weight_percentage" if "weight_percentage" in pos else "weight"
        weight_value = pos.get(weight_key, 0)
        # Convert to numeric, default to 0 if conversion fails
        try:
            current_dict[pos["symbol"]] = (
                float(weight_value) if weight_value is not None else 0
            )
        except (ValueError, TypeError):
            current_dict[pos["symbol"]] = 0

    target_dict = {}
    for weight in target_weights:
        try:
            target_dict[weight["symbol"]] = (
                float(weight["weight"]) if weight["weight"] is not None else 0
            )
        except (ValueError, TypeError):
            target_dict[weight["symbol"]] = 0

    all_symbols = set(list(current_dict.keys()) + list(target_dict.keys()))

    comparison_data = []
    for symbol in all_symbols:
        current_weight = current_dict.get(symbol, 0)
        target_weight = target_dict.get(symbol, 0)
        difference = target_weight - current_weight

        comparison_data.append(
            {
                "symbol": symbol,
                "current_weight": current_weight,
                "target_weight": target_weight,
                "difference": difference,
            }
        )

    df_comparison = pd.DataFrame(comparison_data)

    # Create comparison chart
    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            name="Current Weight (%)",
            x=df_comparison["symbol"],
            y=df_comparison["current_weight"],
            marker_color="lightblue",
            text=df_comparison["current_weight"].round(2),
            textposition="outside",
        )
    )

    fig.add_trace(
        go.Bar(
            name="Target Weight (%)",
            x=df_comparison["symbol"],
            y=df_comparison["target_weight"],
            marker_color="darkblue",
            text=df_comparison["target_weight"].round(2),
            textposition="outside",
        )
    )

    fig.update_layout(
        title="Portfolio Allocation: Current vs Target",
        xaxis_title="Symbols",
        yaxis_title="Weight (%)",
        barmode="group",
        height=500,
        showlegend=True,
    )

    st.plotly_chart(fig, use_container_width=True)

    # Comparison table
    st.dataframe(
        df_comparison.round(2),
        use_container_width=True,
        hide_index=True,
        column_config={
            "symbol": "Symbol",
            "current_weight": st.column_config.NumberColumn(
                "Current %", format="%.2f%%"
            ),
            "target_weight": st.column_config.NumberColumn("Target %", format="%.2f%%"),
            "difference": st.column_config.NumberColumn("Difference", format="%.2f%%"),
        },
    )
