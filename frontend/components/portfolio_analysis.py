import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, Optional
from datetime import datetime

from frontend.services.portfolio import PortfolioService


def render_portfolio_analysis_page():
    """Portfolio analysis page with risk metrics and comparison charts"""
    st.subheader("📈 Portfolio Analysis")

    # Portfolio selector
    selected_portfolio_id = render_portfolio_selector_for_analysis()

    if not selected_portfolio_id:
        st.info("Please select a portfolio to analyze.")
        return

    # Strategy selector - moved to top level to affect all tabs
    strategy = st.radio(
        "Select Strategy",
        options=["long-only", "market-neutral"],
        index=0,
        horizontal=True,
        key="global_strategy_selector",
    )

    # Load data once for all tabs
    portfolio_data = load_portfolio_data_cached(selected_portfolio_id, strategy)

    if not portfolio_data:
        st.error("Failed to load portfolio data.")
        return

    # Add cache management
    col1, col2 = st.columns([4, 1])
    with col2:
        if st.button("🗑️ Clear Cache", help="Clear cached data to force refresh"):
            clear_portfolio_cache(selected_portfolio_id)
            st.success("Cache cleared!")
            st.rerun()

    # Create tabs for different analysis views
    tab1, tab2, tab3 = st.tabs(
        ["📊 Performance Chart", "📋 Risk Metrics", "📈 Detailed Analysis"]
    )

    with tab1:
        render_performance_comparison_chart_with_data(portfolio_data, strategy)

    with tab2:
        render_risk_metrics_real_with_data(portfolio_data, strategy)

    with tab3:
        render_detailed_risk_analysis_tab_with_data(portfolio_data, strategy)


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
    print(system_portfolios)
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
        options=["long-only", "market-neutral"],
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
    strategy = metadata.get("strategy", "long-only")

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


def render_risk_metrics_real(portfolio_id: str, strategy: str = "long-only"):
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
        (
            "Downside Volatility",
            "downside_volatility_pct",
            "%",
            "Volatility of negative returns",
        ),
        ("Max Drawdown", "max_dd_pct", "%", "Maximum peak-to-trough decline"),
        (
            "Avg DD Duration",
            "avg_dd_duration_days",
            "days",
            "Average drawdown duration",
        ),
        (
            "Max DD Duration",
            "max_dd_duration_days",
            "days",
            "Maximum drawdown duration",
        ),
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
        options=["long-only", "market-neutral"],
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


#     # Get analysis data
#     analysis_data = get_analysis_data(selected_portfolio_id, strategy_type)

#     if not analysis_data:
#         st.error("❌ Failed to load portfolio analysis")
#         return

#     # Analysis dashboard
#     render_analysis_dashboard(analysis_data, selected_portfolio_id)


# def render_advanced_portfolio_selector():
#     """Advanced portfolio selector with search and filtering"""
#     portfolios = PortfolioService.get_my_portfolios()

#     if not portfolios:
#         st.warning("👈 Create your first portfolio to start analysis")
#         return None

#     # Create portfolio options
#     portfolio_options = []
#     portfolio_map = {}

#     # System portfolio
#     system_option = "🏢 System Portfolio (Top 20 Monthly)"
#     portfolio_options.append(system_option)
#     portfolio_map[system_option] = "SYSTEM"

#     # Custom portfolios
#     custom_portfolios = [p for p in portfolios if p.get('portfolio_type') == 'CUSTOM']
#     for portfolio in custom_portfolios:
#         symbols_count = len(portfolio.get('symbols', []))
#         status = "🟢" if portfolio.get('is_active', True) else "🔴"
#         option_text = f"{status} {portfolio['name']} ({symbols_count} stocks)"
#         portfolio_options.append(option_text)
#         portfolio_map[option_text] = portfolio['id']

#     # Portfolio selector
#     selected_option = st.selectbox(
#         "📊 Select Portfolio for Analysis",
#         portfolio_options,
#         key="portfolio_analysis_selector",
#         help="Choose a portfolio to analyze. System portfolio is updated monthly with top 20 stocks."
#     )

#     return portfolio_map.get(selected_option)


# def render_no_portfolio_selected():
#     """Render when no portfolio is selected"""
#     st.info("📊 Select a portfolio from the dropdown above to view analysis")

#     # Quick stats about available portfolios
#     portfolios = PortfolioService.get_my_portfolios()
#     custom_portfolios = [p for p in portfolios if p.get('portfolio_type') == 'CUSTOM']

#     if custom_portfolios:
#         st.markdown("#### 📋 Your Available Portfolios:")

#         for portfolio in custom_portfolios[:5]:  # Show first 5
#             col1, col2, col3 = st.columns([3, 1, 1])

#             with col1:
#                 status = "🟢 Active" if portfolio.get('is_active', True) else "🔴 Inactive"
#                 st.markdown(f"**{portfolio['name']}** - {status}")

#             with col2:
#                 st.markdown(f"{len(portfolio.get('symbols', []))} stocks")

#             with col3:
#                 if st.button("📊 Analyze", key=f"quick_analyze_{portfolio['id']}"):
#                     st.session_state.current_portfolio_id = portfolio['id']
#                     st.rerun()

#         if len(custom_portfolios) > 5:
#             st.markdown(f"*... and {len(custom_portfolios) - 5} more portfolios*")

#     else:
#         st.markdown("#### 🎯 Get Started")
#         st.markdown("Create your first custom portfolio to begin analysis!")

#         if st.button("➕ Create Portfolio", use_container_width=True):
#             st.session_state.current_page = "Portfolio Management"
#             st.rerun()


# def get_analysis_data(portfolio_id: str, strategy_type: str) -> Optional[Dict]:
#     """Get analysis data for portfolio"""
#     with st.spinner("📊 Analyzing portfolio..."):
#         if portfolio_id == "SYSTEM":
#             # Use existing system portfolio analysis
#             return get_portfolio_analysis(
#                 st.session_state.get("broker_account_id"),
#                 strategy_type
#             )
#         else:
#             # Get custom portfolio analysis
#             return PortfolioService.get_portfolio_analysis(portfolio_id, strategy_type)


# def render_analysis_dashboard(analysis_data: Dict, portfolio_id: str):
#     """Render comprehensive analysis dashboard"""
#     # Portfolio summary
#     render_enhanced_portfolio_summary(analysis_data, portfolio_id)

#     # Analysis tabs
#     tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
#         "📊 Portfolio Overview",
#         "📈 Holdings Analysis",
#         "🎯 Recommendations",
#         "📉 Risk Metrics",
#         "⚖️ Performance",
#         "🔍 Detailed Report"
#     ])

#     with tab1:
#         render_portfolio_overview_tab(analysis_data)

#     with tab2:
#         render_holdings_analysis_tab(analysis_data)

#     with tab3:
#         render_recommendations_tab(analysis_data)

#     with tab4:
#         render_risk_metrics_tab(analysis_data)

#     with tab5:
#         render_performance_tab(analysis_data)

#     with tab6:
#         render_detailed_report_tab(analysis_data, portfolio_id)


# def render_enhanced_portfolio_summary(analysis_data: Dict, portfolio_id: str):
#     """Enhanced portfolio summary with more metrics"""
#     st.markdown("### 💼 Portfolio Summary")

#     account_balance = analysis_data.get("account_balance", {})
#     current_positions = analysis_data.get("current_positions", [])
#     recommendations = analysis_data.get("recommendations", [])

#     # Key metrics
#     col1, col2, col3, col4, col5 = st.columns(5)

#     with col1:
#         nav = account_balance.get("net_asset_value", 0)
#         st.metric(
#             "💎 Net Asset Value",
#             format_currency(nav),
#             help="Total portfolio value including cash and investments"
#         )

#     with col2:
#         cash = account_balance.get("available_cash", 0)
#         cash_ratio = account_balance.get("cash_ratio", 0)
#         st.metric(
#             "💵 Available Cash",
#             format_currency(cash),
#             delta=f"{cash_ratio:.1f}% of portfolio",
#             help="Cash available for new investments"
#         )

#     with col3:
#         positions_count = len(current_positions)
#         st.metric(
#             "📊 Active Positions",
#             positions_count,
#             help="Number of currently held stocks"
#         )

#     with col4:
#         recommendations_count = len(recommendations)
#         buy_count = len([r for r in recommendations if r.get("action") == "BUY"])
#         st.metric(
#             "🎯 Recommendations",
#             recommendations_count,
#             delta=f"{buy_count} Buy signals",
#             help="Current trade recommendations"
#         )

#     with col5:
#         strategy = analysis_data.get("strategy_type", "N/A").replace("_", " ").title()
#         concentration = calculate_portfolio_concentration(current_positions)
#         st.metric(
#             "📈 Strategy",
#             strategy,
#             delta=f"HHI: {concentration:.3f}",
#             help="Current optimization strategy and concentration index"
#         )


# def render_portfolio_overview_tab(analysis_data: Dict):
#     """Portfolio overview with charts and key metrics"""
#     current_positions = analysis_data.get("current_positions", [])

#     if not current_positions:
#         st.info("📊 No current positions to display")
#         return

#     # Portfolio allocation chart
#     col1, col2 = st.columns(2)

#     with col1:
#         render_portfolio_allocation_chart(current_positions)

#     with col2:
#         render_sector_allocation_chart(current_positions)

#     # Top holdings table
#     st.markdown("#### 🏆 Top Holdings")
#     render_top_holdings_table(current_positions)

#     # Portfolio statistics
#     render_portfolio_statistics(current_positions)


# def render_portfolio_allocation_chart(positions: List[Dict]):
#     """Render portfolio allocation pie chart"""
#     if not positions:
#         return

#     # Prepare data
#     df_positions = pd.DataFrame(positions)

#     # Handle weight column (could be nested dict)
#     weights = []
#     symbols = []

#     for position in positions:
#         symbol = position.get("symbol", "Unknown")
#         weight = position.get("weight", {})

#         if isinstance(weight, dict):
#             weight_value = weight.get("percentage", 0)
#         else:
#             weight_value = float(weight) if weight else 0

#         symbols.append(symbol)
#         weights.append(weight_value)

#     # Create pie chart
#     fig = px.pie(
#         values=weights,
#         names=symbols,
#         title="Portfolio Allocation by Weight",
#         color_discrete_sequence=px.colors.qualitative.Set3
#     )

#     fig.update_traces(
#         textposition="inside",
#         textinfo="percent+label",
#         hovertemplate="<b>%{label}</b><br>Weight: %{percent}<br>Value: %{value:.2f}%<extra></extra>"
#     )

#     fig.update_layout(
#         showlegend=True,
#         height=400,
#         font=dict(size=12)
#     )

#     st.plotly_chart(fig, use_container_width=True)


# def render_sector_allocation_chart(positions: List[Dict]):
#     """Render sector allocation chart (mock data for now)"""
#     # Mock sector data - in real implementation, this would come from the API
#     sectors = ["Technology", "Banking", "Real Estate", "Industrial", "Consumer", "Energy"]
#     sector_weights = [25, 20, 18, 15, 12, 10]  # Mock percentages

#     fig = px.bar(
#         x=sectors,
#         y=sector_weights,
#         title="Sector Allocation",
#         color=sector_weights,
#         color_continuous_scale="Blues"
#     )

#     fig.update_layout(
#         xaxis_title="Sectors",
#         yaxis_title="Weight (%)",
#         height=400,
#         showlegend=False
#     )

#     st.plotly_chart(fig, use_container_width=True)


# def render_top_holdings_table(positions: List[Dict]):
#     """Render top holdings table with enhanced information"""
#     if not positions:
#         return

#     # Prepare data
#     holdings_data = []

#     for position in positions:
#         symbol = position.get("symbol", "")
#         quantity = position.get("quantity", 0)

#         # Handle nested dict structure
#         market_price = position.get("market_price", {})
#         if isinstance(market_price, dict):
#             price_value = market_price.get("amount", 0)
#         else:
#             price_value = float(market_price) if market_price else 0

#         weight = position.get("weight", {})
#         if isinstance(weight, dict):
#             weight_value = weight.get("percentage", 0)
#         else:
#             weight_value = float(weight) if weight else 0

#         market_value = price_value * quantity

#         holdings_data.append({
#             "Symbol": symbol,
#             "Quantity": f"{quantity:,}",
#             "Price": f"{price_value:,.0f}",
#             "Market Value": f"{market_value:,.0f}",
#             "Weight": f"{weight_value:.2f}%",
#             "P&L": f"{position.get('unrealized_profit', {}).get('amount', 0):,.0f}" if isinstance(position.get('unrealized_profit'), dict) else f"{position.get('unrealized_profit', 0):,.0f}"
#         })

#     # Sort by weight and show top 10
#     df_holdings = pd.DataFrame(holdings_data)

#     # Custom styling
#     st.dataframe(
#         df_holdings.head(10),
#         use_container_width=True,
#         hide_index=True,
#         column_config={
#             "Symbol": st.column_config.TextColumn("Symbol", width="small"),
#             "Quantity": st.column_config.TextColumn("Quantity", width="small"),
#             "Price": st.column_config.TextColumn("Price (VND)", width="medium"),
#             "Market Value": st.column_config.TextColumn("Value (VND)", width="medium"),
#             "Weight": st.column_config.TextColumn("Weight", width="small"),
#             "P&L": st.column_config.TextColumn("P&L (VND)", width="medium")
#         }
#     )


# def render_portfolio_statistics(positions: List[Dict]):
#     """Render portfolio statistics"""
#     if not positions:
#         return

#     st.markdown("#### 📊 Portfolio Statistics")

#     # Calculate statistics
#     weights = []
#     for position in positions:
#         weight = position.get("weight", {})
#         if isinstance(weight, dict):
#             weight_value = weight.get("percentage", 0)
#         else:
#             weight_value = float(weight) if weight else 0
#         weights.append(weight_value)

#     concentration = calculate_portfolio_concentration(positions)
#     max_weight = max(weights) if weights else 0
#     min_weight = min([w for w in weights if w > 0]) if weights else 0

#     col1, col2, col3, col4 = st.columns(4)

#     with col1:
#         st.metric(
#             "🎯 Concentration (HHI)",
#             f"{concentration:.4f}",
#             help="Herfindahl-Hirschman Index: Lower values indicate better diversification"
#         )

#     with col2:
#         st.metric(
#             "📈 Largest Position",
#             f"{max_weight:.2f}%",
#             help="Weight of the largest holding"
#         )

#     with col3:
#         st.metric(
#             "📉 Smallest Position",
#             f"{min_weight:.2f}%",
#             help="Weight of the smallest holding"
#         )

#     with col4:
#         avg_weight = sum(weights) / len(weights) if weights else 0
#         st.metric(
#             "📊 Average Weight",
#             f"{avg_weight:.2f}%",
#             help="Average position size"
#         )


# def calculate_portfolio_concentration(positions: List[Dict]) -> float:
#     """Calculate Herfindahl-Hirschman Index for portfolio concentration"""
#     if not positions:
#         return 0

#     weights = []
#     for position in positions:
#         weight = position.get("weight", {})
#         if isinstance(weight, dict):
#             weight_value = weight.get("percentage", 0) / 100  # Convert to decimal
#         else:
#             weight_value = float(weight) / 100 if weight else 0
#         weights.append(weight_value)

#     # HHI = sum of squared weights
#     hhi = sum(w ** 2 for w in weights)
#     return hhi


# def render_holdings_analysis_tab(analysis_data: Dict):
#     """Detailed holdings analysis tab"""
#     current_positions = analysis_data.get("current_positions", [])

#     if not current_positions:
#         st.info("📊 No holdings to analyze")
#         return

#     # Performance analysis
#     render_holdings_performance_analysis(current_positions)

#     # Weight distribution analysis
#     render_weight_distribution_analysis(current_positions)

#     # Holdings comparison
#     render_holdings_comparison(current_positions)


# def render_holdings_performance_analysis(positions: List[Dict]):
#     """Render holdings performance analysis"""
#     st.markdown("#### 🎯 Performance Analysis")

#     # Mock performance data - in real implementation, get from API
#     performance_data = []

#     for position in positions:
#         symbol = position.get("symbol", "")

#         # Mock data
#         daily_return = np.random.normal(0.001, 0.02)
#         ytd_return = np.random.normal(0.05, 0.15)
#         volatility = np.random.uniform(0.15, 0.35)

#         performance_data.append({
#             "Symbol": symbol,
#             "Daily Return": f"{daily_return:.2%}",
#             "YTD Return": f"{ytd_return:.2%}",
#             "Volatility": f"{volatility:.2%}",
#             "Beta": f"{np.random.uniform(0.5, 1.5):.2f}"
#         })

#     df_performance = pd.DataFrame(performance_data)

#     st.dataframe(
#         df_performance,
#         use_container_width=True,
#         hide_index=True
#     )


# def render_recommendations_tab(analysis_data: Dict):
#     """Enhanced recommendations tab"""
#     from ..components.recommendations import display_recommendations_tab

#     recommendations = analysis_data.get("recommendations", [])
#     display_recommendations_tab(recommendations)

#     # Additional recommendation insights
#     if recommendations:
#         render_recommendation_insights(recommendations)


# def render_recommendation_insights(recommendations: List[Dict]):
#     """Render additional insights about recommendations"""
#     st.markdown("#### 🔍 Recommendation Insights")

#     # Categorize recommendations
#     buy_recs = [r for r in recommendations if r.get("action") == "BUY"]
#     sell_recs = [r for r in recommendations if r.get("action") == "SELL"]

#     high_priority = [r for r in recommendations if r.get("priority") == "HIGH"]
#     medium_priority = [r for r in recommendations if r.get("priority") == "MEDIUM"]
#     low_priority = [r for r in recommendations if r.get("priority") == "LOW"]

#     col1, col2 = st.columns(2)

#     with col1:
#         st.markdown("**🎯 Action Distribution**")
#         fig_actions = px.pie(
#             values=[len(buy_recs), len(sell_recs)],
#             names=["Buy", "Sell"],
#             title="Recommended Actions",
#             color_discrete_map={"Buy": "#4CAF50", "Sell": "#F44336"}
#         )
#         fig_actions.update_layout(height=300)
#         st.plotly_chart(fig_actions, use_container_width=True)

#     with col2:
#         st.markdown("**⚡ Priority Distribution**")
#         fig_priority = px.pie(
#             values=[len(high_priority), len(medium_priority), len(low_priority)],
#             names=["High", "Medium", "Low"],
#             title="Priority Levels",
#             color_discrete_map={"High": "#F44336", "Medium": "#FF9800", "Low": "#4CAF50"}
#         )
#         fig_priority.update_layout(height=300)
#         st.plotly_chart(fig_priority, use_container_width=True)


# def render_risk_metrics_tab(analysis_data: Dict):
#     """Render risk metrics and analysis"""
#     st.markdown("#### ⚠️ Risk Analysis")

#     # Mock risk data - in real implementation, calculate from portfolio data
#     col1, col2, col3 = st.columns(3)

#     with col1:
#         st.metric(
#             "📊 Portfolio Beta",
#             "0.95",
#             delta="-0.05 vs Market",
#             help="Sensitivity to market movements"
#         )

#     with col2:
#         st.metric(
#             "📈 Sharpe Ratio",
#             "1.24",
#             delta="+0.18",
#             help="Risk-adjusted return"
#         )

#     with col3:
#         st.metric(
#             "📉 Max Drawdown",
#             "-8.5%",
#             delta="+2.1%",
#             help="Maximum peak-to-trough decline"
#         )

#     # Risk decomposition chart
#     render_risk_decomposition_chart()

#     # Correlation matrix
#     render_correlation_matrix()


# def render_risk_decomposition_chart():
#     """Render risk decomposition chart"""
#     st.markdown("#### 🔍 Risk Decomposition")

#     # Mock risk factors
#     risk_factors = ["Market Risk", "Sector Risk", "Stock Specific", "Currency Risk"]
#     risk_contributions = [45, 25, 20, 10]  # Percentages

#     fig = px.bar(
#         x=risk_factors,
#         y=risk_contributions,
#         title="Risk Factor Contributions",
#         color=risk_contributions,
#         color_continuous_scale="Reds"
#     )

#     fig.update_layout(
#         xaxis_title="Risk Factors",
#         yaxis_title="Contribution (%)",
#         height=400
#     )

#     st.plotly_chart(fig, use_container_width=True)


# def render_correlation_matrix():
#     """Render correlation matrix of holdings"""
#     st.markdown("#### 🔗 Holdings Correlation Matrix")

#     # Mock correlation data
#     symbols = ["VIC", "VCB", "HPG", "VNM", "FPT"]
#     correlations = np.random.uniform(0.1, 0.9, (5, 5))
#     np.fill_diagonal(correlations, 1.0)  # Perfect self-correlation

#     fig = px.imshow(
#         correlations,
#         x=symbols,
#         y=symbols,
#         color_continuous_scale="RdBu",
#         title="Holdings Correlation Matrix"
#     )

#     fig.update_layout(height=400)
#     st.plotly_chart(fig, use_container_width=True)


# def render_performance_tab(analysis_data: Dict):
#     """Render performance analysis tab"""
#     st.markdown("#### 📈 Performance Analysis")

#     # Performance chart
#     render_portfolio_performance_chart()

#     # Performance metrics
#     render_performance_metrics()

#     # Benchmark comparison
#     render_benchmark_comparison()


# def render_portfolio_performance_chart():
#     """Render portfolio performance chart"""
#     # Mock performance data
#     dates = pd.date_range(start="2024-01-01", periods=100, freq="D")
#     portfolio_returns = np.random.normal(0.001, 0.02, 100)
#     benchmark_returns = np.random.normal(0.0008, 0.018, 100)

#     portfolio_cumulative = np.cumprod(1 + portfolio_returns) * 100
#     benchmark_cumulative = np.cumprod(1 + benchmark_returns) * 100

#     fig = go.Figure()

#     fig.add_trace(go.Scatter(
#         x=dates,
#         y=portfolio_cumulative,
#         mode='lines',
#         name='Portfolio',
#         line=dict(color='#2a5298', width=2)
#     ))

#     fig.add_trace(go.Scatter(
#         x=dates,
#         y=benchmark_cumulative,
#         mode='lines',
#         name='VN-Index',
#         line=dict(color='#f44336', width=2, dash='dash')
#     ))

#     fig.update_layout(
#         title="Portfolio vs Benchmark Performance",
#         xaxis_title="Date",
#         yaxis_title="Cumulative Return (%)",
#         height=500,
#         hovermode='x unified'
#     )

#     st.plotly_chart(fig, use_container_width=True)


# def render_detailed_report_tab(analysis_data: Dict, portfolio_id: str):
#     """Render detailed analysis report"""
#     st.markdown("#### 📋 Detailed Portfolio Report")

#     # Report generation
#     col1, col2 = st.columns([3, 1])

#     with col1:
#         st.markdown("Generate a comprehensive portfolio analysis report")

#     with col2:
#         if st.button("📄 Generate Report", use_container_width=True):
#             with st.spinner("Generating report..."):
#                 report_content = generate_portfolio_report(analysis_data, portfolio_id)
#                 st.download_button(
#                     label="💾 Download Report",
#                     data=report_content,
#                     file_name=f"portfolio_report_{portfolio_id}_{datetime.now().strftime('%Y%m%d')}.txt",
#                     mime="text/plain"
#                 )

#     # Report preview
#     with st.expander("📖 Report Preview", expanded=False):
#         render_report_preview(analysis_data, portfolio_id)


# def generate_portfolio_report(analysis_data: Dict, portfolio_id: str) -> str:
#     """Generate detailed portfolio report"""
#     report_lines = []

#     report_lines.append("=" * 60)
#     report_lines.append("CMV TRADING BOT - PORTFOLIO ANALYSIS REPORT")
#     report_lines.append("=" * 60)
#     report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
#     report_lines.append(f"Portfolio ID: {portfolio_id}")
#     report_lines.append(f"Strategy: {analysis_data.get('strategy_type', 'N/A')}")
#     report_lines.append("")

#     # Portfolio Summary
#     report_lines.append("PORTFOLIO SUMMARY")
#     report_lines.append("-" * 20)
#     account_balance = analysis_data.get("account_balance", {})
#     report_lines.append(f"Net Asset Value: {format_currency(account_balance.get('net_asset_value', 0))}")
#     report_lines.append(f"Available Cash: {format_currency(account_balance.get('available_cash', 0))}")
#     report_lines.append(f"Cash Ratio: {account_balance.get('cash_ratio', 0):.2f}%")
#     report_lines.append("")

#     # Current Positions
#     report_lines.append("CURRENT POSITIONS")
#     report_lines.append("-" * 20)
#     positions = analysis_data.get("current_positions", [])
#     for i, position in enumerate(positions, 1):
#         symbol = position.get("symbol", "")
#         quantity = position.get("quantity", 0)
#         weight = position.get("weight", {})
#         weight_pct = weight.get("percentage", 0) if isinstance(weight, dict) else weight
#         report_lines.append(f"{i:2d}. {symbol:6s} - {quantity:8,d} shares - {weight_pct:6.2f}%")

#     report_lines.append("")

#     # Recommendations
#     recommendations = analysis_data.get("recommendations", [])
#     if recommendations:
#         report_lines.append("TRADE RECOMMENDATIONS")
#         report_lines.append("-" * 20)

#         buy_recs = [r for r in recommendations if r.get("action") == "BUY"]
#         sell_recs = [r for r in recommendations if r.get("action") == "SELL"]

#         if buy_recs:
#             report_lines.append("BUY RECOMMENDATIONS:")
#             for rec in buy_recs:
#                 symbol = rec.get("symbol", "")
#                 priority = rec.get("priority", "")
#                 target_weight = rec.get("target_weight", {})
#                 target_pct = target_weight.get("percentage", 0) if isinstance(target_weight, dict) else target_weight
#                 report_lines.append(f"  - {symbol:6s} (Target: {target_pct:6.2f}%) - Priority: {priority}")

#         if sell_recs:
#             report_lines.append("SELL RECOMMENDATIONS:")
#             for rec in sell_recs:
#                 symbol = rec.get("symbol", "")
#                 priority = rec.get("priority", "")
#                 current_weight = rec.get("current_weight", {})
#                 current_pct = current_weight.get("percentage", 0) if isinstance(current_weight, dict) else current_weight
#                 report_lines.append(f"  - {symbol:6s} (Current: {current_pct:6.2f}%) - Priority: {priority}")

#     report_lines.append("")
#     report_lines.append("=" * 60)
#     report_lines.append("End of Report")

#     return "\n".join(report_lines)


# def render_report_preview(analysis_data: Dict, portfolio_id: str):
#    """Render report preview in the UI"""

#    # Portfolio Overview
#    st.markdown("##### 📊 Portfolio Overview")
#    account_balance = analysis_data.get("account_balance", {})

#    overview_data = {
#        "Metric": [
#            "Net Asset Value",
#            "Available Cash",
#            "Cash Ratio",
#            "Strategy Type",
#            "Analysis Date"
#        ],
#        "Value": [
#            format_currency(account_balance.get("net_asset_value", 0)),
#            format_currency(account_balance.get("available_cash", 0)),
#            f"{account_balance.get('cash_ratio', 0):.2f}%",
#            analysis_data.get("strategy_type", "N/A").replace("_", " ").title(),
#            analysis_data.get("analysis_date", "N/A")
#        ]
#    }

#    st.table(pd.DataFrame(overview_data))

#    # Top Holdings Summary
#    st.markdown("##### 🏆 Top 5 Holdings")
#    positions = analysis_data.get("current_positions", [])

#    if positions:
#        top_holdings = []
#        for position in positions[:5]:
#            symbol = position.get("symbol", "")
#            weight = position.get("weight", {})
#            weight_pct = weight.get("percentage", 0) if isinstance(weight, dict) else weight

#            market_price = position.get("market_price", {})
#            price_value = market_price.get("amount", 0) if isinstance(market_price, dict) else market_price

#            top_holdings.append({
#                "Symbol": symbol,
#                "Weight": f"{weight_pct:.2f}%",
#                "Price": format_currency(price_value),
#                "Quantity": f"{position.get('quantity', 0):,}"
#            })

#        st.table(pd.DataFrame(top_holdings))

#    # Recommendations Summary
#    recommendations = analysis_data.get("recommendations", [])
#    if recommendations:
#        st.markdown("##### 🎯 Recommendations Summary")

#        buy_count = len([r for r in recommendations if r.get("action") == "BUY"])
#        sell_count = len([r for r in recommendations if r.get("action") == "SELL"])
#        high_priority = len([r for r in recommendations if r.get("priority") == "HIGH"])

#        rec_summary = {
#            "Type": ["Buy Recommendations", "Sell Recommendations", "High Priority"],
#            "Count": [buy_count, sell_count, high_priority]
#        }

#        st.table(pd.DataFrame(rec_summary))


# # Additional utility functions
# def render_weight_distribution_analysis(positions: List[Dict]):
#    """Analyze weight distribution of holdings"""
#    st.markdown("#### ⚖️ Weight Distribution Analysis")

#    if not positions:
#        return

#    # Extract weights
#    weights = []
#    symbols = []

#    for position in positions:
#        symbol = position.get("symbol", "")
#        weight = position.get("weight", {})
#        weight_value = weight.get("percentage", 0) if isinstance(weight, dict) else float(weight) if weight else 0

#        weights.append(weight_value)
#        symbols.append(symbol)

#    # Weight distribution histogram
#    fig = px.histogram(
#        x=weights,
#        nbins=10,
#        title="Weight Distribution Across Holdings",
#        labels={"x": "Weight (%)", "y": "Number of Holdings"}
#    )

#    fig.update_layout(height=400)
#    st.plotly_chart(fig, use_container_width=True)

#    # Weight statistics
#    col1, col2, col3, col4 = st.columns(4)

#    with col1:
#        st.metric("📊 Std Deviation", f"{np.std(weights):.2f}%")
#    with col2:
#        st.metric("📈 Max Weight", f"{max(weights):.2f}%")
#    with col3:
#        st.metric("📉 Min Weight", f"{min([w for w in weights if w > 0]):.2f}%")
#    with col4:
#        st.metric("🎯 Median Weight", f"{np.median(weights):.2f}%")


# def render_holdings_comparison(positions: List[Dict]):
#    """Compare holdings across different metrics"""
#    st.markdown("#### 🔍 Holdings Comparison")

#    if not positions:
#        return

#    # Create comparison table
#    comparison_data = []

#    for position in positions:
#        symbol = position.get("symbol", "")
#        quantity = position.get("quantity", 0)

#        # Handle nested structures
#        market_price = position.get("market_price", {})
#        price_value = market_price.get("amount", 0) if isinstance(market_price, dict) else market_price

#        weight = position.get("weight", {})
#        weight_value = weight.get("percentage", 0) if isinstance(weight, dict) else weight

#        unrealized_profit = position.get("unrealized_profit", {})
#        profit_value = unrealized_profit.get("amount", 0) if isinstance(unrealized_profit, dict) else unrealized_profit

#        market_value = price_value * quantity

#        comparison_data.append({
#            "Symbol": symbol,
#            "Market Value": market_value,
#            "Weight": weight_value,
#            "P&L": profit_value,
#            "P&L %": (profit_value / market_value * 100) if market_value > 0 else 0
#        })

#    df_comparison = pd.DataFrame(comparison_data)

#    # Sort options
#    col1, col2 = st.columns(2)

#    with col1:
#        sort_by = st.selectbox(
#            "Sort by",
#            ["Weight", "Market Value", "P&L", "P&L %"],
#            key="holdings_sort"
#        )

#    with col2:
#        ascending = st.checkbox("Ascending order", key="holdings_order")

#    # Sort and display
#    df_sorted = df_comparison.sort_values(sort_by, ascending=ascending)

#    st.dataframe(
#        df_sorted,
#        use_container_width=True,
#        hide_index=True,
#        column_config={
#            "Market Value": st.column_config.NumberColumn("Market Value", format="%.0f"),
#            "Weight": st.column_config.NumberColumn("Weight (%)", format="%.2f"),
#            "P&L": st.column_config.NumberColumn("P&L", format="%.0f"),
#            "P&L %": st.column_config.NumberColumn("P&L %", format="%.2f")
#        }
#    )


# def render_performance_metrics():
#    """Render detailed performance metrics"""
#    st.markdown("#### 📊 Performance Metrics")

#    # Mock performance data - in real implementation, calculate from actual data
#    metrics_data = {
#        "Metric": [
#            "Total Return (YTD)",
#            "Annualized Return",
#            "Volatility",
#            "Sharpe Ratio",
#            "Sortino Ratio",
#            "Maximum Drawdown",
#            "Calmar Ratio",
#            "Information Ratio"
#        ],
#        "Portfolio": [
#            "12.5%",
#            "15.2%",
#            "18.3%",
#            "1.24",
#            "1.67",
#            "-8.5%",
#            "1.79",
#            "0.85"
#        ],
#        "Benchmark": [
#            "8.7%",
#            "11.4%",
#            "20.1%",
#            "0.89",
#            "1.21",
#            "-12.3%",
#            "0.93",
#            "-"
#        ]
#    }

#    st.dataframe(
#        pd.DataFrame(metrics_data),
#        use_container_width=True,
#        hide_index=True
#    )


# def render_benchmark_comparison():
#    """Render benchmark comparison analysis"""
#    st.markdown("#### 🏁 Benchmark Comparison")

#    # Performance comparison chart
#    metrics = ["Return", "Volatility", "Sharpe", "Max DD"]
#    portfolio_values = [12.5, 18.3, 1.24, -8.5]
#    benchmark_values = [8.7, 20.1, 0.89, -12.3]

#    fig = go.Figure()

#    fig.add_trace(go.Bar(
#        name='Portfolio',
#        x=metrics,
#        y=portfolio_values,
#        marker_color='#2a5298'
#    ))

#    fig.add_trace(go.Bar(
#        name='VN-Index',
#        x=metrics,
#        y=benchmark_values,
#        marker_color='#f44336'
#    ))

#    fig.update_layout(
#        title="Portfolio vs Benchmark Metrics",
#        xaxis_title="Metrics",
#        yaxis_title="Values",
#        barmode='group',
#        height=400
#    )

#    st.plotly_chart(fig, use_container_width=True)

#    # Alpha and Beta analysis
#    col1, col2 = st.columns(2)

#    with col1:
#        st.metric(
#            "📈 Alpha",
#            "3.8%",
#            delta="vs Benchmark",
#            help="Excess return relative to benchmark"
#        )

#    with col2:
#        st.metric(
#            "📊 Beta",
#            "0.91",
#            delta="Market sensitivity",
#            help="Sensitivity to market movements"
#        )


# # Export and sharing functionality
# def render_export_options(analysis_data: Dict, portfolio_id: str):
#    """Render export and sharing options"""
#    st.markdown("#### 📤 Export & Share")

#    col1, col2, col3 = st.columns(3)

#    with col1:
#        if st.button("📄 Export PDF", use_container_width=True):
#            st.info("PDF export functionality coming soon!")

#    with col2:
#        if st.button("📊 Export Excel", use_container_width=True):
#            excel_data = prepare_excel_export(analysis_data)
#            st.download_button(
#                "💾 Download Excel",
#                data=excel_data,
#                file_name=f"portfolio_analysis_{portfolio_id}.xlsx",
#                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
#            )

#    with col3:
#        if st.button("📱 Share Report", use_container_width=True):
#            share_url = generate_share_url(portfolio_id)
#            st.code(share_url, language="text")
#            st.success("Share URL generated!")


# def prepare_excel_export(analysis_data: Dict) -> bytes:
#    """Prepare Excel export data"""
#    import io
#    from openpyxl import Workbook

#    wb = Workbook()

#    # Summary sheet
#    ws_summary = wb.active
#    ws_summary.title = "Summary"

#    # Add summary data
#    account_balance = analysis_data.get("account_balance", {})
#    ws_summary['A1'] = "Portfolio Summary"
#    ws_summary['A2'] = "Net Asset Value"
#    ws_summary['B2'] = account_balance.get("net_asset_value", 0)
#    ws_summary['A3'] = "Available Cash"
#    ws_summary['B3'] = account_balance.get("available_cash", 0)
#    ws_summary['A4'] = "Cash Ratio"
#    ws_summary['B4'] = account_balance.get("cash_ratio", 0)

#    # Holdings sheet
#    ws_holdings = wb.create_sheet("Holdings")
#    ws_holdings['A1'] = "Symbol"
#    ws_holdings['B1'] = "Quantity"
#    ws_holdings['C1'] = "Weight %"
#    ws_holdings['D1'] = "Market Value"

#    positions = analysis_data.get("current_positions", [])
#    for i, position in enumerate(positions, 2):
#        ws_holdings[f'A{i}'] = position.get("symbol", "")
#        ws_holdings[f'B{i}'] = position.get("quantity", 0)

#        weight = position.get("weight", {})
#        weight_value = weight.get("percentage", 0) if isinstance(weight, dict) else weight
#        ws_holdings[f'C{i}'] = weight_value

#        market_price = position.get("market_price", {})
#        price_value = market_price.get("amount", 0) if isinstance(market_price, dict) else market_price
#        market_value = price_value * position.get("quantity", 0)
#        ws_holdings[f'D{i}'] = market_value

#    # Save to bytes
#    excel_buffer = io.BytesIO()
#    wb.save(excel_buffer)
#    excel_buffer.seek(0)

#    return excel_buffer.getvalue()


# def generate_share_url(portfolio_id: str) -> str:
#    """Generate shareable URL for portfolio analysis"""
#    # In real implementation, this would create a shareable link
#    base_url = "https://cmv-trading-bot.app"
#    return f"{base_url}/shared/portfolio/{portfolio_id}?token={hash(portfolio_id)}"


# # Main integration function
# def integrate_portfolio_analysis():
#    """Main function to integrate enhanced portfolio analysis"""
#    # Apply custom CSS
#    st.markdown(ENHANCED_MAIN_CSS, unsafe_allow_html=True)

#    # Check authentication
#    if not st.session_state.get("authenticated"):
#        st.warning("Please log in to access portfolio analysis")
#        return

#    # Render analysis dashboard
#    render_portfolio_analysis_dashboard()

#    # Auto-refresh functionality
#    if st.session_state.get("auto_refresh", False):
#        st.rerun()
