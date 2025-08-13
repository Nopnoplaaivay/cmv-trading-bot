import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import Dict, Optional
from datetime import datetime

from frontend.services.portfolio import PortfolioService


def render_portfolio_analysis_page():
    st.subheader("📈 Portfolio Analysis")

    selected_portfolio_id = render_portfolio_selector_for_analysis()

    if not selected_portfolio_id:
        st.info("Please select a portfolio to analyze.")
        return

    strategy = st.radio(
        "Select Strategy",
        options=["LongOnly", "MarketNeutral"],
        index=0,
        horizontal=True,
        key="global_strategy_selector",
    )

    portfolio_data = load_portfolio_data_cached(selected_portfolio_id, strategy)

    if not portfolio_data:
        st.error("Failed to load portfolio data.")
        return

    col1, col2 = st.columns([4, 1])
    with col2:
        if st.button("🗑️ Clear Cache", help="Clear cached data to force refresh"):
            clear_portfolio_cache(selected_portfolio_id)
            st.success("Cache cleared!")
            st.rerun()

    tab1, tab2 = st.tabs(
        ["📊 Performance Chart", "📋 Risk Metrics"]
    )

    with tab1:
        render_performance_comparison_chart_with_data(portfolio_data, strategy)

    with tab2:
        render_risk_metrics_real_with_data(portfolio_data, strategy)

    # with tab3:
    #     render_detailed_risk_analysis_tab_with_data(portfolio_data, strategy)


def load_portfolio_data_cached(portfolio_id: str, strategy: str) -> Optional[Dict]:
    """Central function to load portfolio data with caching"""
    cache_key = f"portfolio_data_{portfolio_id}_{strategy}"
    cache_time_key = f"portfolio_data_time_{portfolio_id}_{strategy}"

    # Show cache status if exists
    if cache_key in st.session_state and cache_time_key in st.session_state:
        cache_time = st.session_state[cache_time_key]
        st.info(f"📅 Using cached data from: {cache_time.strftime('%H:%M:%S')}")

    # Load data if not cached or force refresh
    if cache_key not in st.session_state or st.button(
        "🔄 Refresh Data", key=f"refresh_data_{portfolio_id}_{strategy}"
    ):
        with st.spinner("Loading portfolio data..."):
            try:
                # Get PnL data from API - this includes all data we need
                pnl_data = PortfolioService.get_portfolio_pnl(portfolio_id, strategy)

                if not pnl_data:
                    st.error("Failed to load portfolio data.")
                    return None

                # Cache the complete data
                st.session_state[cache_key] = pnl_data
                st.session_state[cache_time_key] = datetime.now()
                st.success("✅ Data loaded successfully!")

            except Exception as e:
                st.error(f"Error loading portfolio data: {str(e)}")
                return None

    return st.session_state.get(cache_key)


def clear_portfolio_cache(portfolio_id: str):
    """Clear all cached data for a specific portfolio"""
    keys_to_remove = []
    for key in st.session_state.keys():
        if portfolio_id in key and any(
            prefix in key
            for prefix in ["portfolio_data", "risk_metrics", "performance_data"]
        ):
            keys_to_remove.append(key)

    for key in keys_to_remove:
        del st.session_state[key]


def render_portfolio_selector_for_analysis() -> Optional[str]:
    """Render portfolio selector for analysis"""
    personal_portfolios = PortfolioService.get_my_portfolios().get("portfolios")
    system_portfolios = PortfolioService.get_system_portfolios().get("portfolios")
    portfolios = personal_portfolios + system_portfolios

    if not personal_portfolios:
        st.sidebar.info(
            "💡 You can analyze the System Portfolio or create your first custom portfolio!"
        )

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

    selected_display_name = st.selectbox(
        "📊 Select Portfolio to Analyze",
        options=list(portfolio_options.keys()),
        key="analysis_portfolio_selector",
    )

    return portfolio_options[selected_display_name] if selected_display_name else None


def render_performance_comparison_chart_with_data(portfolio_data: Dict, strategy: str):
    """Render performance comparison chart using cached data"""
    st.subheader("📊 Portfolio vs VN-Index Performance")

    if not portfolio_data:
        st.warning("No performance data available.")
        return

    # Extract data from cached portfolio_data
    portfolio_pnl = portfolio_data.get("portfolio", [])
    vnindex_pnl = portfolio_data.get("vnindex", [])
    metadata = portfolio_data.get("metadata", {})

    if not portfolio_pnl or not vnindex_pnl:
        st.warning("No PnL data available for the selected portfolio.")
        return

    # Create comparison chart
    fig = create_comparison_chart(portfolio_pnl, vnindex_pnl, metadata)
    st.plotly_chart(fig, use_container_width=True)

    # Display metadata
    render_performance_metadata(metadata)

    # Display risk metrics summary if available
    if "risk_metrics" in portfolio_data:
        render_risk_metrics_summary(portfolio_data["risk_metrics"])


def render_risk_metrics_real_with_data(portfolio_data: Dict, strategy: str):
    """Render actual risk metrics using cached data"""
    st.subheader("📊 Risk Metrics Analysis")

    if not portfolio_data or "risk_metrics" not in portfolio_data:
        st.warning("No risk metrics data available.")
        return

    risk_metrics = portfolio_data["risk_metrics"]
    portfolio_metrics = risk_metrics.get("portfolio", {})
    vnindex_metrics = risk_metrics.get("vnindex", {})

    # Risk Metrics Comparison
    render_risk_metrics_comparison(portfolio_metrics, vnindex_metrics)

    # Detailed Risk Analysis
    render_detailed_risk_analysis(portfolio_metrics, vnindex_metrics)

    # Risk vs Return Chart
    render_risk_return_chart(portfolio_metrics, vnindex_metrics)


def render_detailed_risk_analysis_tab_with_data(portfolio_data: Dict, strategy: str):
    """Render detailed risk analysis tab using cached data"""
    st.subheader("📈 Detailed Analysis")

    if not portfolio_data or "risk_metrics" not in portfolio_data:
        st.warning("No risk metrics data available for detailed analysis.")
        return

    risk_metrics = portfolio_data["risk_metrics"]
    portfolio_metrics = risk_metrics.get("portfolio", {})
    vnindex_metrics = risk_metrics.get("vnindex", {})

    # Show data freshness
    cache_time = st.session_state.get(
        f"portfolio_data_time_{portfolio_data.get('metadata', {}).get('portfolio_id', 'unknown')}_{strategy}"
    )
    if cache_time:
        st.caption(f"📊 Data from: {cache_time.strftime('%H:%M:%S')}")

    # Call the existing detailed analysis function
    render_detailed_risk_analysis(portfolio_metrics, vnindex_metrics)

    # Additional detailed charts
    render_additional_detailed_analysis(portfolio_data)


def render_additional_detailed_analysis(portfolio_data: Dict):
    """Render additional detailed analysis charts"""
    st.subheader("📈 Additional Analysis")

    metadata = portfolio_data.get("metadata", {})

    # Portfolio composition
    symbols = metadata.get("symbols", [])
    if symbols:
        st.markdown("#### 📋 Portfolio Composition Details")

        col1, col2 = st.columns(2)

        with col1:
            st.metric("Total Stocks", len(symbols))
            st.metric("Trading Days Analyzed", metadata.get("total_dates", 0))

        with col2:
            st.metric(
                "Data Period",
                f"{metadata.get('from_date', 'N/A')} to {metadata.get('to_date', 'N/A')}",
            )
            st.metric("Strategy Used", metadata.get("strategy", "N/A"))

        # Show all symbols
        st.markdown("**Symbols in Portfolio:**")
        symbols_text = ", ".join(symbols)
        st.text_area(
            "", symbols_text, height=80, disabled=True, label_visibility="collapsed"
        )


def render_performance_comparison_chart(portfolio_id: str):
    """Render performance comparison chart between portfolio and VN-Index"""
    st.subheader("📊 Portfolio vs VN-Index Performance")

    # Strategy selector
    strategy = st.radio(
        "Select Strategy",
        options=["LongOnly", "MarketNeutral"],
        index=0,
        horizontal=True,
        key=f"strategy_selector_{portfolio_id}",
    )

    # Cache key for performance data
    cache_key = f"performance_data_{portfolio_id}_{strategy}"

    # Load data with caching
    if cache_key not in st.session_state or st.button(
        "🔄 Refresh Data", key=f"refresh_perf_{portfolio_id}"
    ):
        with st.spinner("Loading portfolio performance data..."):
            try:
                # Get PnL data from API
                pnl_data = PortfolioService.get_portfolio_pnl(portfolio_id, strategy)

                if not pnl_data:
                    st.error("Failed to load portfolio PnL data.")
                    return

                # Cache the data
                st.session_state[cache_key] = pnl_data

            except Exception as e:
                st.error(f"Error loading portfolio performance: {str(e)}")
                return

    # Get cached data
    pnl_data = st.session_state.get(cache_key)
    if not pnl_data:
        st.warning("No performance data available.")
        return

    # Extract data
    portfolio_pnl = pnl_data.get("portfolio", [])
    vnindex_pnl = pnl_data.get("vnindex", [])
    metadata = pnl_data.get("metadata", {})

    if not portfolio_pnl or not vnindex_pnl:
        st.warning("No PnL data available for the selected portfolio.")
        return

    # Create comparison chart
    fig = create_comparison_chart(portfolio_pnl, vnindex_pnl, metadata)
    st.plotly_chart(fig, use_container_width=True)

    # Display metadata
    render_performance_metadata(metadata)

    # Display risk metrics summary if available
    if "risk_metrics" in pnl_data:
        render_risk_metrics_summary(pnl_data["risk_metrics"])


def render_risk_metrics_summary(risk_metrics: dict):
    """Render a summary of key risk metrics on performance tab"""
    st.subheader("📊 Quick Risk Metrics Summary")

    portfolio_metrics = risk_metrics.get("portfolio", {})
    vnindex_metrics = risk_metrics.get("vnindex", {})

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        portfolio_sharpe = portfolio_metrics.get("sharpe_ratio", 0)
        vnindex_sharpe = vnindex_metrics.get("sharpe_ratio", 0)
        delta_sharpe = portfolio_sharpe - vnindex_sharpe
        st.metric(
            "Sharpe Ratio", f"{portfolio_sharpe:.2f}", delta=f"{delta_sharpe:+.2f}"
        )

    with col2:
        portfolio_mdd = portfolio_metrics.get("max_dd_pct", 0)
        vnindex_mdd = vnindex_metrics.get("max_dd_pct", 0)
        delta_mdd = portfolio_mdd - vnindex_mdd
        st.metric("Max Drawdown", f"{portfolio_mdd:.1f}%", delta=f"{delta_mdd:+.1f}%")

    with col3:
        portfolio_winrate = portfolio_metrics.get("win_rate_pct", 0)
        vnindex_winrate = vnindex_metrics.get("win_rate_pct", 0)
        delta_winrate = portfolio_winrate - vnindex_winrate
        st.metric(
            "Win Rate", f"{portfolio_winrate:.1f}%", delta=f"{delta_winrate:+.1f}%"
        )

    with col4:
        portfolio_vol = portfolio_metrics.get("annualized_volatility_pct", 0)
        vnindex_vol = vnindex_metrics.get("annualized_volatility_pct", 0)
        delta_vol = portfolio_vol - vnindex_vol
        st.metric("Volatility", f"{portfolio_vol:.1f}%", delta=f"{delta_vol:+.1f}%")


def create_comparison_chart(
    portfolio_pnl: list, vnindex_pnl: list, metadata: dict
) -> go.Figure:
    """Create PnL comparison chart"""

    # Convert to DataFrames
    portfolio_df = pd.DataFrame(portfolio_pnl)
    vnindex_df = pd.DataFrame(vnindex_pnl)

    # Convert date columns
    portfolio_df["date"] = pd.to_datetime(portfolio_df["date"])
    vnindex_df["date"] = pd.to_datetime(vnindex_df["date"])

    fig = go.Figure()

    # Portfolio PnL line
    fig.add_trace(
        go.Scatter(
            x=portfolio_df["date"],
            y=portfolio_df["pnl_pct"],
            mode="lines",
            name="Portfolio PnL (%)",
            line=dict(color="#1f77b4", width=2.5),
            hovertemplate="<b>Portfolio</b><br>Date: %{x}<br>PnL: %{y:.2f}%<extra></extra>",
        )
    )

    # VN-Index PnL line
    fig.add_trace(
        go.Scatter(
            x=vnindex_df["date"],
            y=vnindex_df["pnl_pct"],
            mode="lines",
            name="VN-Index PnL (%)",
            line=dict(color="#ff7f0e", width=2.5),
            hovertemplate="<b>VN-Index</b><br>Date: %{x}<br>PnL: %{y:.2f}%<extra></extra>",
        )
    )

    # Zero line
    fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)

    # Get date range for title
    from_date = metadata.get("from_date", "N/A")
    to_date = metadata.get("to_date", "N/A")
    portfolio_name = metadata.get("portfolio_id", "Portfolio")
    strategy = metadata.get("strategy", "LongOnly")

    fig.update_layout(
        title=f"Performance Comparison: {portfolio_name} vs VN-Index<br>"
        f"<sub>Strategy: {strategy} | Period: {from_date} to {to_date}</sub>",
        xaxis_title="Date",
        yaxis_title="PnL (%)",
        hovermode="x unified",
        legend=dict(x=0.02, y=0.98),
        height=600,
        showlegend=True,
        template="plotly_white",
        xaxis=dict(showgrid=True, gridwidth=1, gridcolor="rgba(128,128,128,0.2)"),
        yaxis=dict(
            showgrid=True,
            gridwidth=1,
            gridcolor="rgba(128,128,128,0.2)",
            ticksuffix="%",
        ),
    )

    return fig


def render_performance_metadata(metadata: dict):
    """Render performance metadata"""
    st.subheader("📊 Performance Summary")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        symbols = metadata.get("symbols", [])
        st.metric("Portfolio Stocks", len(symbols))

    with col2:
        st.metric("Trading Days", metadata.get("total_dates", 0))

    with col3:
        st.metric("From Date", metadata.get("from_date", "N/A"))

    with col4:
        st.metric("To Date", metadata.get("to_date", "N/A"))

    if symbols:
        st.subheader("📋 Portfolio Composition")
        symbols_text = ", ".join(symbols)
        st.text_area("Stocks in Portfolio", symbols_text, height=100, disabled=True)


def render_risk_metrics_real(portfolio_id: str, strategy: str = "LongOnly"):
    """Render actual risk metrics from API response"""
    st.subheader("📊 Risk Metrics Analysis")

    # Check if we have cached data for this portfolio and strategy
    cache_key = f"risk_metrics_{portfolio_id}_{strategy}"
    cache_time_key = f"risk_metrics_time_{portfolio_id}_{strategy}"

    # Show cache status
    if cache_key in st.session_state and cache_time_key in st.session_state:
        cache_time = st.session_state[cache_time_key]
        st.info(f"📅 Data cached at: {cache_time.strftime('%Y-%m-%d %H:%M:%S')}")

    if cache_key not in st.session_state or st.button(
        "🔄 Refresh Risk Metrics", key=f"refresh_risk_{portfolio_id}"
    ):
        with st.spinner("Loading risk metrics..."):
            try:
                # Get PnL data which includes risk_metrics
                pnl_data = PortfolioService.get_portfolio_pnl(portfolio_id, strategy)

                if pnl_data and "risk_metrics" in pnl_data:
                    st.session_state[cache_key] = pnl_data["risk_metrics"]
                    st.session_state[cache_time_key] = datetime.now()
                else:
                    st.error("Failed to load risk metrics data.")
                    return
            except Exception as e:
                st.error(f"Error loading risk metrics: {str(e)}")
                return

    risk_metrics = st.session_state.get(cache_key)
    if not risk_metrics:
        st.warning("No risk metrics data available.")
        return

    portfolio_metrics = risk_metrics.get("portfolio", {})
    vnindex_metrics = risk_metrics.get("vnindex", {})

    # Risk Metrics Comparison
    render_risk_metrics_comparison(portfolio_metrics, vnindex_metrics)

    # Detailed Risk Analysis
    render_detailed_risk_analysis(portfolio_metrics, vnindex_metrics)

    # Risk vs Return Chart
    render_risk_return_chart(portfolio_metrics, vnindex_metrics)


def render_risk_metrics_comparison(portfolio_metrics: dict, vnindex_metrics: dict):
    """Render key risk metrics comparison"""
    st.subheader("🔄 Portfolio vs VN-Index Risk Comparison")

    # Key metrics row 1
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        portfolio_sharpe = portfolio_metrics.get("sharpe_ratio", 0)
        vnindex_sharpe = vnindex_metrics.get("sharpe_ratio", 0)
        delta_sharpe = portfolio_sharpe - vnindex_sharpe
        st.metric(
            "Sharpe Ratio",
            f"{portfolio_sharpe:.2f}",
            delta=f"{delta_sharpe:+.2f} vs VN-Index",
            help="Risk-adjusted return (higher is better)",
        )

    with col2:
        portfolio_sortino = portfolio_metrics.get("sortino_ratio", 0)
        vnindex_sortino = vnindex_metrics.get("sortino_ratio", 0)
        delta_sortino = portfolio_sortino - vnindex_sortino
        st.metric(
            "Sortino Ratio",
            f"{portfolio_sortino:.2f}",
            delta=f"{delta_sortino:+.2f} vs VN-Index",
            help="Downside risk-adjusted return",
        )

    with col3:
        portfolio_mdd = portfolio_metrics.get("max_dd_pct", 0)
        vnindex_mdd = vnindex_metrics.get("max_dd_pct", 0)
        delta_mdd = portfolio_mdd - vnindex_mdd
        st.metric(
            "Max Drawdown",
            f"{portfolio_mdd:.2f}%",
            delta=f"{delta_mdd:+.2f}% vs VN-Index",
            help="Maximum peak-to-trough decline",
        )

    with col4:
        portfolio_winrate = portfolio_metrics.get("win_rate_pct", 0)
        vnindex_winrate = vnindex_metrics.get("win_rate_pct", 0)
        delta_winrate = portfolio_winrate - vnindex_winrate
        st.metric(
            "Win Rate",
            f"{portfolio_winrate:.1f}%",
            delta=f"{delta_winrate:+.1f}% vs VN-Index",
            help="Percentage of profitable days",
        )

    # Key metrics row 2
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        portfolio_vol = portfolio_metrics.get("annualized_volatility_pct", 0)
        vnindex_vol = vnindex_metrics.get("annualized_volatility_pct", 0)
        delta_vol = portfolio_vol - vnindex_vol
        st.metric(
            "Volatility (Annual)",
            f"{portfolio_vol:.1f}%",
            delta=f"{delta_vol:+.1f}% vs VN-Index",
            help="Annualized price volatility",
        )

    with col2:
        portfolio_var = portfolio_metrics.get("var_95_daily_pct", 0)
        vnindex_var = vnindex_metrics.get("var_95_daily_pct", 0)
        delta_var = portfolio_var - vnindex_var
        st.metric(
            "VaR (95%)",
            f"{portfolio_var:.2f}%",
            delta=f"{delta_var:+.2f}% vs VN-Index",
            help="Value at Risk - 95% confidence daily loss",
        )

    with col3:
        portfolio_return = portfolio_metrics.get("total_return_pct", 0)
        vnindex_return = vnindex_metrics.get("total_return_pct", 0)
        delta_return = portfolio_return - vnindex_return
        st.metric(
            "Total Return",
            f"{portfolio_return:.1f}%",
            delta=f"{delta_return:+.1f}% vs VN-Index",
            help="Total cumulative return",
        )

    with col4:
        portfolio_calmar = portfolio_metrics.get("calmar_ratio", 0)
        vnindex_calmar = vnindex_metrics.get("calmar_ratio", 0)
        delta_calmar = portfolio_calmar - vnindex_calmar
        st.metric(
            "Calmar Ratio",
            f"{portfolio_calmar:.2f}",
            delta=f"{delta_calmar:+.2f} vs VN-Index",
            help="Return / Max Drawdown ratio",
        )


def render_detailed_risk_analysis(portfolio_metrics: dict, vnindex_metrics: dict):
    """Render detailed risk analysis tables"""
    st.subheader("📋 Detailed Risk Analysis")

    # Create comparison table
    risk_comparison_data = []

    metrics_config = [
        ("Total Return", "total_return_pct", "%", "Total cumulative return"),
        ("Max Return", "max_return_pct", "%", "Maximum return reached"),
        ("Min Return", "min_return_pct", "%", "Minimum return (maximum loss)"),
        ("Daily Volatility", "daily_volatility_pct", "%", "Daily price volatility"),
        ("Downside Volatility", "downside_volatility_pct", "%", "Volatility of negative returns"),
        ("Max Drawdown", "max_dd_pct", "%", "Maximum peak-to-trough decline"),
        ("CVaR (95%)", "cvar_95_daily_pct", "%", "Conditional Value at Risk"),
        ("Best Day", "best_day_pct", "%", "Best single day return"),
        ("Worst Day", "worst_day_pct", "%", "Worst single day return"),
        ("Skewness", "skewness", "", "Distribution skewness"),
        ("Kurtosis", "kurtosis", "", "Distribution kurtosis"),
    ]

    for display_name, key, unit, description in metrics_config:
        portfolio_val = portfolio_metrics.get(key, 0)
        vnindex_val = vnindex_metrics.get(key, 0)

        # Handle extreme values display
        if abs(portfolio_val) > 1000:
            portfolio_display = f"{portfolio_val:.0f}{unit}"
        else:
            portfolio_display = f"{portfolio_val:.2f}{unit}"

        if abs(vnindex_val) > 1000:
            vnindex_display = f"{vnindex_val:.0f}{unit}"
        else:
            vnindex_display = f"{vnindex_val:.2f}{unit}"

        # Calculate difference
        diff = portfolio_val - vnindex_val
        if abs(diff) > 1000:
            diff_display = f"{diff:+.0f}{unit}"
        else:
            diff_display = f"{diff:+.2f}{unit}"

        risk_comparison_data.append(
            {
                "Metric": display_name,
                "Portfolio": portfolio_display,
                "VN-Index": vnindex_display,
                "Difference": diff_display,
                "Description": description,
            }
        )

    # Display table
    df_risk = pd.DataFrame(risk_comparison_data)
    st.dataframe(
        df_risk,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Metric": st.column_config.TextColumn("Risk Metric", width="medium"),
            "Portfolio": st.column_config.TextColumn("Portfolio", width="small"),
            "VN-Index": st.column_config.TextColumn("VN-Index", width="small"),
            "Difference": st.column_config.TextColumn("Difference", width="small"),
            "Description": st.column_config.TextColumn("Description", width="large"),
        },
    )


def render_risk_return_chart(portfolio_metrics: dict, vnindex_metrics: dict):
    """Render risk vs return scatter plot"""
    st.subheader("📊 Risk vs Return Analysis")

    # Extract risk and return data
    portfolio_return = portfolio_metrics.get("total_return_pct", 0)
    portfolio_risk = portfolio_metrics.get("annualized_volatility_pct", 0)

    vnindex_return = vnindex_metrics.get("total_return_pct", 0)
    vnindex_risk = vnindex_metrics.get("annualized_volatility_pct", 0)

    # Create scatter plot
    fig = go.Figure()

    # Portfolio point
    fig.add_trace(
        go.Scatter(
            x=[portfolio_risk],
            y=[portfolio_return],
            mode="markers",
            name="Portfolio",
            marker=dict(size=15, color="#1f77b4", symbol="circle"),
            hovertemplate="<b>Portfolio</b><br>Risk: %{x:.1f}%<br>Return: %{y:.1f}%<extra></extra>",
        )
    )

    # VN-Index point
    fig.add_trace(
        go.Scatter(
            x=[vnindex_risk],
            y=[vnindex_return],
            mode="markers",
            name="VN-Index",
            marker=dict(size=15, color="#ff7f0e", symbol="diamond"),
            hovertemplate="<b>VN-Index</b><br>Risk: %{x:.1f}%<br>Return: %{y:.1f}%<extra></extra>",
        )
    )

    # Add efficient frontier line (mock)
    risk_range = [
        min(portfolio_risk, vnindex_risk) * 0.5,
        max(portfolio_risk, vnindex_risk) * 1.5,
    ]
    efficient_returns = [r * 0.4 for r in risk_range]  # Mock efficient frontier

    fig.add_trace(
        go.Scatter(
            x=risk_range,
            y=efficient_returns,
            mode="lines",
            name="Efficient Frontier (Estimated)",
            line=dict(dash="dash", color="gray"),
            hovertemplate="Risk: %{x:.1f}%<br>Expected Return: %{y:.1f}%<extra></extra>",
        )
    )

    fig.update_layout(
        title="Risk vs Return Positioning",
        xaxis_title="Risk (Annualized Volatility %)",
        yaxis_title="Return (%)",
        height=500,
        hovermode="closest",
        legend=dict(x=0.02, y=0.98),
        template="plotly_white",
    )

    st.plotly_chart(fig, use_container_width=True)

    # Risk-Return Analysis Insights
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 💡 Risk-Return Insights")

        # Calculate risk-adjusted metrics
        portfolio_sharpe = portfolio_metrics.get("sharpe_ratio", 0)
        vnindex_sharpe = vnindex_metrics.get("sharpe_ratio", 0)

        if portfolio_sharpe > vnindex_sharpe:
            st.success(
                f"✅ Portfolio has better risk-adjusted returns (Sharpe: {portfolio_sharpe:.2f} vs {vnindex_sharpe:.2f})"
            )
        else:
            st.warning(
                f"⚠️ VN-Index has better risk-adjusted returns (Sharpe: {vnindex_sharpe:.2f} vs {portfolio_sharpe:.2f})"
            )

        if portfolio_return > vnindex_return:
            st.info(
                f"📈 Portfolio outperformed VN-Index by {portfolio_return - vnindex_return:.1f}%"
            )
        else:
            st.info(
                f"📉 Portfolio underperformed VN-Index by {vnindex_return - portfolio_return:.1f}%"
            )

    with col2:
        st.markdown("#### 🎯 Risk Profile")

        # Risk level assessment
        if portfolio_risk < vnindex_risk:
            risk_level = "Lower Risk"
            risk_color = "success"
        elif portfolio_risk > vnindex_risk * 1.2:
            risk_level = "Higher Risk"
            risk_color = "error"
        else:
            risk_level = "Similar Risk"
            risk_color = "info"

        getattr(st, risk_color)(f"Portfolio Risk Level: {risk_level}")

        # Drawdown comparison
        portfolio_mdd = abs(portfolio_metrics.get("max_dd_pct", 0))
        vnindex_mdd = abs(vnindex_metrics.get("max_dd_pct", 0))

        if portfolio_mdd < vnindex_mdd:
            st.success(
                f"✅ Lower maximum drawdown ({portfolio_mdd:.1f}% vs {vnindex_mdd:.1f}%)"
            )
        else:
            st.warning(
                f"⚠️ Higher maximum drawdown ({portfolio_mdd:.1f}% vs {vnindex_mdd:.1f}%)"
            )


def render_detailed_risk_analysis_tab(portfolio_id: str):
    """Wrapper function for detailed risk analysis tab"""
    st.subheader("📈 Detailed Analysis")

    # Strategy selector
    strategy = st.radio(
        "Select Strategy for Detailed Analysis",
        options=["LongOnly", "MarketNeutral"],
        index=0,
        horizontal=True,
        key="detailed_strategy_selector",
    )

    # Check cache first
    cache_key = f"risk_metrics_{portfolio_id}_{strategy}"
    if cache_key in st.session_state:
        cached_data = st.session_state[cache_key]
        portfolio_data = cached_data["data"]
        cache_time = cached_data.get("timestamp", "unknown")

        if "risk_metrics" in portfolio_data:
            risk_metrics = portfolio_data["risk_metrics"]
            portfolio_metrics = risk_metrics.get("portfolio", {})
            vnindex_metrics = risk_metrics.get("vnindex", {})

            # Show cache info
            st.caption(f"📊 Cached data from: {cache_time}")

            # Call the existing detailed analysis function
            render_detailed_risk_analysis(portfolio_metrics, vnindex_metrics)
            return

    # If no cache, fetch fresh data
    with st.spinner("Loading detailed risk analysis..."):
        try:
            portfolio_data = PortfolioService.get_portfolio_pnl(portfolio_id, strategy)
            if portfolio_data and "risk_metrics" in portfolio_data:
                # Cache the data
                st.session_state[cache_key] = {
                    "data": portfolio_data,
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                }

                risk_metrics = portfolio_data["risk_metrics"]
                portfolio_metrics = risk_metrics.get("portfolio", {})
                vnindex_metrics = risk_metrics.get("vnindex", {})

                render_detailed_risk_analysis(portfolio_metrics, vnindex_metrics)
            else:
                st.error("Unable to load risk metrics data")
        except Exception as e:
            st.error(f"Error loading data: {str(e)}")


def render_detailed_analysis_placeholder():
    """Render detailed analysis section (placeholder)"""
    st.subheader("📈 Detailed Analysis")

    st.info("🚧 Detailed analysis features coming soon:")

    st.markdown(
        """
    **Planned Features:**
    - Monthly/Quarterly performance breakdown
    - Sector allocation analysis
    - Rolling metrics charts
    - Performance attribution
    - Risk-adjusted returns
    - Correlation analysis
    - Factor exposure analysis
    """
    )

    # Sample chart placeholder
    st.subheader("📊 Sample Rolling Sharpe Ratio (Demo)")

    # Create dummy rolling Sharpe data
    dates = pd.date_range(start="2023-01-01", end="2024-12-31", freq="D")[:200]
    sharpe_values = pd.Series(range(len(dates))).apply(
        lambda x: 0.8 + 0.5 * (x % 20) / 20
    )

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=sharpe_values,
            mode="lines",
            name="30-Day Rolling Sharpe",
            line=dict(color="green", width=2),
        )
    )

    fig.update_layout(
        title="30-Day Rolling Sharpe Ratio (Sample)",
        xaxis_title="Date",
        yaxis_title="Sharpe Ratio",
        height=400,
        template="plotly_white",
    )

    st.plotly_chart(fig, use_container_width=True)