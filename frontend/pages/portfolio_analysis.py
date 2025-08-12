import streamlit as st
from datetime import datetime
from frontend.services.portfolio import PortfolioService
from frontend.components.portfolio import (
    display_portfolio_summary,
    display_current_positions,
    display_weight_comparison_chart,
)
from frontend.components.portfolio_analysis import render_portfolio_analysis_page
from ..components.recommendations import display_recommendations_tab
from ..utils.helpers import format_currency


def portfolio_analysis_page():
    """Main portfolio analysis page with enhanced functionality"""

    # Create tabs for different analysis views
    tab1, tab2 = st.tabs(["📊 Enhanced Analysis", "⚖️ Portfolio vs Account"])

    with tab1:
        render_portfolio_analysis_page()

    with tab2:
        render_portfolio_vs_account_comparison()


def render_portfolio_vs_account_comparison():
    """Render comparison between user's real account and selected portfolio"""
    st.subheader("⚖️ Portfolio vs Real Account Comparison")
    
    # Check if user has broker account
    if not st.session_state.get("broker_account_id"):
        st.warning(
            "⚠️ No broker account information available. Please check the Account Information section in the sidebar."
        )
        st.info(
            "💡 If you just logged in, try refreshing the account information from the sidebar."
        )
        return

    # Portfolio selector for comparison
    st.markdown("#### 📊 Select Portfolio for Comparison")
    selected_portfolio_id = render_portfolio_selector_for_comparison()
    
    if not selected_portfolio_id:
        st.info("Please select a portfolio to compare with your real account.")
        return

    # Strategy selector
    strategy = st.radio(
        "Select Strategy for Portfolio Analysis",
        options=["long-only", "market-neutral"],
        index=0,
        horizontal=True,
        key="comparison_strategy_selector",
    )

    col1, col2 = st.columns(2)
    
    with col1:
        # Load real account data
        st.markdown("### 💼 Your Real Account")
        with st.spinner("📊 Loading account data..."):
            account_data = PortfolioService.get_system_portfolio_analysis(
                st.session_state.broker_account_id,
                strategy,
            )
            
        if account_data:
            display_account_summary(account_data)
        else:
            st.error("❌ Failed to load account data.")
            
    with col2:
        # Load selected portfolio data
        st.markdown("### 📈 Selected Portfolio")
        with st.spinner("📊 Loading portfolio data..."):
            portfolio_data = PortfolioService.get_portfolio_pnl(selected_portfolio_id, strategy)
            
        if portfolio_data:
            display_portfolio_summary_comparison(portfolio_data, selected_portfolio_id)
        else:
            st.error("❌ Failed to load portfolio data.")

    # Detailed comparison if both data sets are available
    if account_data and portfolio_data:
        st.markdown("---")
        render_detailed_comparison(account_data, portfolio_data, strategy)


def render_portfolio_selector_for_comparison():
    """Render portfolio selector for comparison feature"""
    personal_portfolios = PortfolioService.get_my_portfolios().get("portfolios", [])
    system_portfolios = PortfolioService.get_system_portfolios().get("portfolios", [])
    portfolios = personal_portfolios + system_portfolios

    if not portfolios:
        st.warning("No portfolios available. Create a portfolio first.")
        return None

    # Create portfolio options
    portfolio_options = {}
    for portfolio in portfolios:
        try:
            name = portfolio["metadata"].get("portfolioName", "Unknown")
            portfolio_id = portfolio["portfolioId"]
            num_stocks = len(portfolio.get("records", []))
            display_name = f"{name} ({num_stocks} stocks)"
            portfolio_options[display_name] = portfolio_id
        except Exception as e:
            st.error(f"Error processing portfolio: {e}")

    if not portfolio_options:
        return None

    selected_display_name = st.selectbox(
        "📊 Select Portfolio for Comparison",
        options=list(portfolio_options.keys()),
        key="comparison_portfolio_selector",
        help="Choose a portfolio to compare with your real account holdings"
    )

    return portfolio_options[selected_display_name] if selected_display_name else None


def display_account_summary(account_data):
    """Display real account summary"""
    account_balance = account_data.get("account_balance", {})
    
    # Account metrics
    st.metric("Net Asset Value", format_currency(account_balance.get("net_asset_value", 0)))
    st.metric("Available Cash", format_currency(account_balance.get("available_cash", 0)))
    st.metric("Cash Ratio", f"{account_balance.get('cash_ratio', 0):.2%}")
    
    # Current positions
    current_positions = account_data.get("current_positions", [])
    if current_positions:
        st.markdown("**Current Holdings:**")
        for pos in current_positions[:5]:  # Show top 5
            symbol = pos.get("symbol", "")
            quantity = pos.get("quantity", 0)
            weight = pos.get("weight", {})
            weight_pct = weight.get("percentage", 0) if isinstance(weight, dict) else weight
            st.write(f"• {symbol}: {quantity:,} shares ({weight_pct:.1f}%)")
        
        if len(current_positions) > 5:
            st.write(f"... and {len(current_positions) - 5} more positions")


def display_portfolio_summary_comparison(portfolio_data, portfolio_id):
    """Display portfolio summary for comparison"""
    # Portfolio basic info
    st.write(f"**Portfolio ID:** `{portfolio_id[:8]}...`")
    
    # Risk metrics if available
    risk_metrics = portfolio_data.get("risk_metrics", {})
    if risk_metrics:
        st.metric("Expected Return", f"{risk_metrics.get('portfolio_expected_return', 0):.2%}")
        st.metric("Volatility", f"{risk_metrics.get('portfolio_volatility', 0):.2%}")
        st.metric("Sharpe Ratio", f"{risk_metrics.get('sharpe_ratio', 0):.3f}")
    
    # Portfolio composition
    portfolio_df = portfolio_data.get("portfolio_pnl_df")
    if portfolio_df and isinstance(portfolio_df, list) and len(portfolio_df) > 0:
        st.markdown("**Portfolio Holdings:**")
        # Get latest weights from the portfolio data
        latest_data = portfolio_df[-1] if portfolio_df else {}
        symbols = portfolio_data.get("metadata", {}).get("symbols", [])
        
        for symbol in symbols[:5]:  # Show top 5
            st.write(f"• {symbol}")
            
        if len(symbols) > 5:
            st.write(f"... and {len(symbols) - 5} more stocks")


def render_detailed_comparison(account_data, portfolio_data, strategy):
    """Render detailed comparison between account and portfolio"""
    st.subheader("📊 Detailed Comparison")
    
    # Create comparison tabs
    comp_tab1, comp_tab2, comp_tab3 = st.tabs(
        ["📋 Holdings Comparison", "📈 Performance", "💡 Recommendations"]
    )
    
    with comp_tab1:
        render_holdings_comparison(account_data, portfolio_data)
        
    with comp_tab2:
        render_performance_comparison(account_data, portfolio_data)
        
    with comp_tab3:
        render_rebalancing_recommendations(account_data, portfolio_data)


def render_holdings_comparison(account_data, portfolio_data):
    """Compare holdings between account and portfolio"""
    st.markdown("#### 📋 Holdings Comparison")
    
    # Get current positions from account
    current_positions = account_data.get("current_positions", [])
    current_symbols = {pos.get("symbol"): pos for pos in current_positions}
    
    # Get target symbols from portfolio
    target_symbols = portfolio_data.get("metadata", {}).get("symbols", [])
    
    # Create comparison dataframe
    comparison_data = []
    all_symbols = set(current_symbols.keys()) | set(target_symbols)
    
    for symbol in all_symbols:
        current_pos = current_symbols.get(symbol, {})
        current_weight = 0
        if current_pos:
            weight_data = current_pos.get("weight", {})
            current_weight = weight_data.get("percentage", 0) if isinstance(weight_data, dict) else weight_data
        
        in_target = symbol in target_symbols
        target_weight = 100 / len(target_symbols) if in_target and target_symbols else 0
        
        comparison_data.append({
            "Symbol": symbol,
            "Current Weight (%)": f"{current_weight:.2f}",
            "Target Weight (%)": f"{target_weight:.2f}" if in_target else "0.00",
            "Difference": f"{current_weight - target_weight:.2f}",
            "Action": "Hold" if abs(current_weight - target_weight) < 1 else ("Buy" if current_weight < target_weight else "Sell")
        })
    
    if comparison_data:
        import pandas as pd
        df_comparison = pd.DataFrame(comparison_data)
        st.dataframe(df_comparison, use_container_width=True)


def render_performance_comparison(account_data, portfolio_data):
    """Compare performance metrics"""
    st.markdown("#### 📈 Performance Comparison")
    
    # Account metrics
    account_balance = account_data.get("account_balance", {})
    risk_metrics = portfolio_data.get("risk_metrics", {})
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Your Account**")
        nav = account_balance.get("net_asset_value", 0)
        cash_ratio = account_balance.get("cash_ratio", 0)
        st.metric("Net Asset Value", format_currency(nav))
        st.metric("Cash Ratio", f"{cash_ratio:.2%}")
        
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
    target_symbols = portfolio_data.get("metadata", {}).get("symbols", [])
    
    if not target_symbols:
        st.info("No target portfolio symbols available for recommendations.")
        return
    
    # Calculate total account value for rebalancing
    account_balance = account_data.get("account_balance", {})
    total_value = account_balance.get("net_asset_value", 0)
    
    if total_value <= 0:
        st.warning("Cannot generate recommendations without valid account value.")
        return
    
    st.success(f"� Based on your account value of {format_currency(total_value)}:")
    
    # Equal weight allocation
    target_weight_per_stock = 100 / len(target_symbols)
    target_value_per_stock = total_value * (target_weight_per_stock / 100)
    
    st.info(f"🎯 Target allocation: {target_weight_per_stock:.2f}% per stock ({format_currency(target_value_per_stock)} each)")
    
    # Show recommendations for each target symbol
    for symbol in target_symbols:
        current_pos = next((pos for pos in current_positions if pos.get("symbol") == symbol), None)
        current_value = 0
        
        if current_pos:
            quantity = current_pos.get("quantity", 0)
            market_price_data = current_pos.get("market_price", {})
            price = market_price_data.get("amount", 0) if isinstance(market_price_data, dict) else market_price_data
            current_value = quantity * price
        
        difference = target_value_per_stock - current_value
        
        if abs(difference) > total_value * 0.01:  # Only recommend if difference > 1% of total value
            if difference > 0:
                st.write(f"📈 **{symbol}**: Buy {format_currency(abs(difference))} more")
            else:
                st.write(f"📉 **{symbol}**: Sell {format_currency(abs(difference))} worth")
        else:
            st.write(f"✅ **{symbol}**: Current allocation is appropriate")

    # with tab4:
    #     display_analysis_settings()


# def display_performance_analysis(analysis_data):
#     """Display performance analysis and charts"""
#     st.subheader("📈 Performance Analysis")

#     # Target vs Current weights comparison
#     current_positions = analysis_data.get("current_positions", [])
#     target_weights = analysis_data.get("target_weights", [])

#     if current_positions and target_weights:
#         display_weight_comparison_chart(current_positions, target_weights)

    # Historical performance (simulated)
    # if st.checkbox("Show Historical Performance", value=False):
    #     display_simulated_performance()


# def display_simulated_performance():
#     """Display simulated historical performance"""
#     import pandas as pd
#     import plotly.express as px
#     import numpy as np

#     st.markdown("#### 📊 Historical Performance (Simulated)")

#     # Generate sample data
#     dates = pd.date_range(start="2024-01-01", end=datetime.now(), freq="D")
#     np.random.seed(42)  # For consistent results

#     returns = np.random.normal(0.0008, 0.02, len(dates))  # Daily returns
#     cumulative_returns = np.cumprod(1 + returns)
#     portfolio_values = cumulative_returns * 100000  # Starting with $100k

#     df_performance = pd.DataFrame(
#         {
#             "Date": dates,
#             "Portfolio Value": portfolio_values,
#             "Daily Return": returns * 100,
#         }
#     )

#     # Portfolio value chart
#     fig_performance = px.line(
#         df_performance, x="Date", y="Portfolio Value", title="Portfolio Value Over Time"
#     )

#     fig_performance.update_layout(
#         xaxis_title="Date", yaxis_title="Portfolio Value ($)", height=400
#     )

#     st.plotly_chart(fig_performance, use_container_width=True)

#     # Performance metrics
#     total_return = (portfolio_values[-1] / portfolio_values[0] - 1) * 100
#     max_value = portfolio_values.max()
#     min_value = portfolio_values.min()

#     col1, col2, col3 = st.columns(3)
#     with col1:
#         st.metric("Total Return", f"{total_return:.2f}%")
#     with col2:
#         st.metric("Peak Value", format_currency(max_value))
#     with col3:
#         st.metric("Trough Value", format_currency(min_value))


# def display_analysis_settings():
#     """Display analysis settings and configuration"""
#     st.subheader("⚙️ Analysis Settings")

#     col1, col2 = st.columns(2)

#     with col1:
#         st.markdown("#### 📊 Strategy Configuration")

#         # Weight tolerance
#         weight_tolerance = st.slider(
#             "Weight Tolerance (%)",
#             min_value=0.5,
#             max_value=5.0,
#             value=2.0,
#             step=0.1,
#             help="Minimum weight difference to trigger a trade recommendation",
#         )

#         # Risk tolerance
#         risk_tolerance = st.selectbox(
#             "Risk Tolerance", ["Conservative", "Moderate", "Aggressive"], index=1
#         )

#         # Maximum position size
#         max_position_size = st.slider(
#             "Maximum Position Size (%)",
#             min_value=5.0,
#             max_value=20.0,
#             value=10.0,
#             step=0.5,
#         )

#     with col2:
#         st.markdown("#### 🔔 Notification Settings")

#         # Telegram notifications
#         telegram_enabled = st.checkbox("Enable Telegram Notifications", value=True)

#         # Email notifications
#         email_enabled = st.checkbox("Enable Email Notifications", value=False)

#         # Notification frequency
#         notification_freq = st.selectbox(
#             "Notification Frequency", ["Real-time", "Daily", "Weekly"], index=1
#         )

#         # Send test notification
#         # if st.button("Send Test Notification", use_container_width=True):
#         #     if st.session_state.get("broker_account_id"):
#         #         success = send_portfolio_notification(
#         #             st.session_state.broker_account_id,
#         #             st.session_state.get("strategy_type", "market_neutral"),
#         #         )
#         #         if success:
#         #             st.success("Test notification sent!")
#         #         else:
#         #             st.error("Failed to send notification")
#         #     else:
#         #         st.error("Please set broker account ID first")

#     # Save settings button
#     if st.button("💾 Save Settings", use_container_width=True, type="primary"):
#         st.success("Settings saved successfully!")
