import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List
from frontend.utils.helpers import format_currency, format_percentage, safe_numeric_value



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

    df_positions["cost_price"] = df_positions["cost_price"].apply(lambda x: safe_numeric_value(x, default=0))
    df_positions["break_even_price"] = df_positions["break_even_price"].apply(lambda x: safe_numeric_value(x, default=0))
    df_positions["market_value"] = df_positions["market_value"].apply(lambda x: safe_numeric_value(x, default=0))
    df_positions["realized_profit"] = df_positions["realized_profit"].apply(lambda x: safe_numeric_value(x, default=0))
    df_positions["unrealized_profit"] = df_positions["unrealized_profit"].apply(lambda x: safe_numeric_value(x, default=0))
    df_positions["weight"] = df_positions["weight"].apply(lambda x: safe_numeric_value(x, default=0))
    df_positions["weight_over_sv"] = df_positions["weight_over_sv"].apply(lambda x: safe_numeric_value(x, default=0))


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
        "symbol": st.column_config.TextColumn("Mã", width="small"),
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

