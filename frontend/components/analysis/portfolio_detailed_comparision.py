import streamlit as st
import plotly.express as px 
import pandas as pd
from typing import Dict, List
from frontend.utils.helpers import format_currency, safe_numeric_value


def render_detailed_comparison(account_data, portfolio_data, strategy):
    """Render detailed comparison between account and portfolio"""
    st.subheader("📊 Detailed Comparison")

    # Create comparison tabs
    comp_tab1, comp_tab2 = st.tabs(
        ["📋 Holdings Comparison", "💡 Recommendations"]
    )

    with comp_tab1:
        render_holdings_comparison(account_data, portfolio_data)


    with comp_tab2:
        render_rebalancing_recommendations(account_data, portfolio_data)

    # with comp_tab2:
    #     render_performance_comparison(account_data, portfolio_data)

def render_holdings_comparison(account_data, portfolio_data):

    current_positions = account_data.get("current_positions", [])
    target_positions = account_data.get("target_weights", [])

    display_current_positions(current_positions)

    st.markdown("#### 📋 Holdings Comparison")
    current_symbols = {pos["symbol"]: pos for pos in current_positions}

    target_symbols = {target["symbol"]: target for target in target_positions}

    comparison_data = []
    all_symbols = set(current_symbols.keys()) | set(target_symbols.keys())

    for symbol in all_symbols:
        current_pos = current_symbols.get(symbol, {})
        current_weight = 0
        if current_pos:
            weight_data = current_pos.get("weight", {})
            current_weight = (
                weight_data.get("percentage", 0)
                if isinstance(weight_data, dict)
                else weight_data
            )

        in_target = symbol in target_symbols
        target_weight = target_symbols[symbol]["weight"] if in_target and target_symbols.get(symbol) else 0

        comparison_data.append(
            {
                "Mã": symbol,
                "Tỷ trọng / NAV (%)": f"{current_weight:.2f}",
                "Tỷ trọng mục tiêu (%)": f"{target_weight:.2f}" if in_target else "0.00",
                "Chênh lệch": f"{current_weight - target_weight:.2f}",
                "Hành động": (
                    "Giữ"
                    if abs(current_weight - target_weight) < 1
                    else ("Mua" if current_weight < target_weight else "Bán")
                ),
            }
        )

    if comparison_data:
        import pandas as pd

        df_comparison = pd.DataFrame(comparison_data)
        st.dataframe(df_comparison, use_container_width=True)


def render_performance_comparison(account_data, portfolio_data):
    """Compare performance metrics"""
    st.markdown("#### 📈 Performance Comparison")

    account_balance = account_data.get("account_balance", {})
    risk_metrics = portfolio_data.get("risk_metrics", {})

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Your Account**")
        nav = account_balance.get("net_asset_value", 0)
        cash_ratio = account_balance.get("cash_ratio", 0)
        st.metric("Net Asset Value", format_currency(nav))
        st.metric("Cash Ratio", f"{cash_ratio}%")

    with col2:
        st.markdown("**Target Portfolio**")
        expected_return = risk_metrics.get("portfolio_expected_return", 0)
        volatility = risk_metrics.get("portfolio_volatility", 0)
        sharpe = risk_metrics.get("sharpe_ratio", 0)
        st.metric("Expected Return", f"{expected_return:.2%}")
        st.metric("Volatility", f"{volatility:.2%}")
        st.metric("Sharpe Ratio", f"{sharpe:.3f}")


def render_rebalancing_recommendations(account_data, portfolio_data):
    """Provide rebalancing recommendations"""
    st.markdown("#### 💡 Rebalancing Recommendations")

    current_positions = account_data.get("current_positions", [])
    target_positions = account_data.get("target_weights", [])
    target_symbols = {target["symbol"]: target for target in target_positions}

    if not target_symbols:
        st.info("No target portfolio symbols available for recommendations.")
        return

    # Calculate total account value for rebalancing
    account_balance = account_data.get("account_balance", {})
    total_value = account_balance.get("net_asset_value", 0)

    if total_value <= 0:
        st.warning("Cannot generate recommendations without valid account value.")
        return

    st.success(f"� Based on your account value of {format_currency(total_value)}")

    # Show recommendations for each target symbol
    for symbol, target in target_symbols.items():
        current_pos = next(
            (pos for pos in current_positions if pos.get("symbol") == symbol), None
        )
        current_value = 0

        if current_pos:
            quantity = current_pos.get("quantity", 0)
            market_price_data = current_pos.get("market_price", {})
            price = (
                market_price_data.get("amount", 0)
                if isinstance(market_price_data, dict)
                else market_price_data
            )
            current_value = quantity * price

        target_value = target.get("weight", 0) * total_value / 100
        difference = target_value - current_value

        if (
            abs(difference) > total_value * 0.01
        ):  # Only recommend if difference > 1% of total value
            if difference > 0:
                st.write(
                    f"📈 **{symbol}**: Buy {format_currency(abs(difference))} more"
                )
            else:
                st.write(
                    f"📉 **{symbol}**: Sell {format_currency(abs(difference))} worth"
                )
        else:
            st.write(f"✅ **{symbol}**: Current allocation is appropriate")


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
    df_positions["unrealized_profit"] = df_positions["unrealized_profit"].apply(lambda x: safe_numeric_value(x, default=0))
    df_positions["weight"] = df_positions["weight"].apply(lambda x: safe_numeric_value(x, default=0))
    df_positions["weight_over_sv"] = df_positions["weight_over_sv"].apply(lambda x: safe_numeric_value(x, default=0))


    # Convert numeric columns to proper dtypes
    numeric_columns = [
        "quantity",
        "cost_price",
        "break_even_price",
        "market_value",
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
        "weight": st.column_config.NumberColumn("Tỷ trọng (%)/ Tài sản ròng", format="%.2f%%"),
        "weight_over_sv": st.column_config.NumberColumn("Tỷ trọng (%)/ Giá trị cổ phiếu", format="%.2f%%"),
        "market_value": st.column_config.NumberColumn("Giá trị thị trường", format="%.2f"),
        "unrealized_profit": st.column_config.NumberColumn("Lãi chưa thực hiện", format="%.2f")
    }

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config=column_config,
    )

