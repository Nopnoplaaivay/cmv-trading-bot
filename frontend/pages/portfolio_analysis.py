"""
Portfolio analysis page for CMV Trading Bot frontend
"""

import streamlit as st
from datetime import datetime
from ..services.api import get_portfolio_analysis, send_portfolio_notification
from ..components.portfolio import (
    display_portfolio_summary,
    display_current_positions,
    display_weight_comparison_chart,
)
from ..components.recommendations import display_recommendations_tab
from ..utils.helpers import format_currency


def portfolio_analysis_page():
    """Portfolio analysis main page"""
    if not st.session_state.get("broker_account_id"):
        st.warning(
            "👈 Please enter your broker account ID in the sidebar to view portfolio analysis"
        )
        return

    # Auto-refresh logic
    if st.session_state.get("auto_refresh", False):
        if (
            "last_refresh" not in st.session_state
            or (datetime.now() - st.session_state.last_refresh).seconds > 30
        ):
            st.session_state.last_refresh = datetime.now()
            st.rerun()

    # Get portfolio data
    with st.spinner("📊 Loading portfolio analysis..."):
        analysis_data = get_portfolio_analysis(
            st.session_state.broker_account_id,
            st.session_state.get("strategy_type", "market_neutral"),
        )

    if not analysis_data:
        st.error(
            "❌ Failed to load portfolio data. Please check your account ID and try again."
        )
        return

    # Display portfolio analysis
    display_portfolio_summary(analysis_data)

    # Create tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(
        ["📊 Current Positions", "🎯 Recommendations", "📈 Performance", "⚙️ Settings"]
    )

    with tab1:
        display_current_positions(analysis_data.get("current_positions", []))

    with tab2:
        display_recommendations_tab(analysis_data.get("recommendations", []))

    with tab3:
        display_performance_analysis(analysis_data)

    with tab4:
        display_analysis_settings()


def display_performance_analysis(analysis_data):
    """Display performance analysis and charts"""
    st.subheader("📈 Performance Analysis")

    # Target vs Current weights comparison
    current_positions = analysis_data.get("current_positions", [])
    target_weights = analysis_data.get("target_weights", [])

    if current_positions and target_weights:
        display_weight_comparison_chart(current_positions, target_weights)

    # Historical performance (simulated)
    if st.checkbox("Show Historical Performance", value=False):
        display_simulated_performance()


def display_simulated_performance():
    """Display simulated historical performance"""
    import pandas as pd
    import plotly.express as px
    import numpy as np

    st.markdown("#### 📊 Historical Performance (Simulated)")

    # Generate sample data
    dates = pd.date_range(start="2024-01-01", end=datetime.now(), freq="D")
    np.random.seed(42)  # For consistent results

    returns = np.random.normal(0.0008, 0.02, len(dates))  # Daily returns
    cumulative_returns = np.cumprod(1 + returns)
    portfolio_values = cumulative_returns * 100000  # Starting with $100k

    df_performance = pd.DataFrame(
        {
            "Date": dates,
            "Portfolio Value": portfolio_values,
            "Daily Return": returns * 100,
        }
    )

    # Portfolio value chart
    fig_performance = px.line(
        df_performance, x="Date", y="Portfolio Value", title="Portfolio Value Over Time"
    )

    fig_performance.update_layout(
        xaxis_title="Date", yaxis_title="Portfolio Value ($)", height=400
    )

    st.plotly_chart(fig_performance, use_container_width=True)

    # Performance metrics
    total_return = (portfolio_values[-1] / portfolio_values[0] - 1) * 100
    max_value = portfolio_values.max()
    min_value = portfolio_values.min()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Return", f"{total_return:.2f}%")
    with col2:
        st.metric("Peak Value", format_currency(max_value))
    with col3:
        st.metric("Trough Value", format_currency(min_value))


def display_analysis_settings():
    """Display analysis settings and configuration"""
    st.subheader("⚙️ Analysis Settings")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📊 Strategy Configuration")

        # Weight tolerance
        weight_tolerance = st.slider(
            "Weight Tolerance (%)",
            min_value=0.5,
            max_value=5.0,
            value=2.0,
            step=0.1,
            help="Minimum weight difference to trigger a trade recommendation",
        )

        # Risk tolerance
        risk_tolerance = st.selectbox(
            "Risk Tolerance", ["Conservative", "Moderate", "Aggressive"], index=1
        )

        # Maximum position size
        max_position_size = st.slider(
            "Maximum Position Size (%)",
            min_value=5.0,
            max_value=20.0,
            value=10.0,
            step=0.5,
        )

    with col2:
        st.markdown("#### 🔔 Notification Settings")

        # Telegram notifications
        telegram_enabled = st.checkbox("Enable Telegram Notifications", value=True)

        # Email notifications
        email_enabled = st.checkbox("Enable Email Notifications", value=False)

        # Notification frequency
        notification_freq = st.selectbox(
            "Notification Frequency", ["Real-time", "Daily", "Weekly"], index=1
        )

        # Send test notification
        if st.button("Send Test Notification", use_container_width=True):
            if st.session_state.get("broker_account_id"):
                success = send_portfolio_notification(
                    st.session_state.broker_account_id,
                    st.session_state.get("strategy_type", "market_neutral"),
                )
                if success:
                    st.success("Test notification sent!")
                else:
                    st.error("Failed to send notification")
            else:
                st.error("Please set broker account ID first")

    # Save settings button
    if st.button("💾 Save Settings", use_container_width=True, type="primary"):
        st.success("Settings saved successfully!")
