# # frontend/components/enhanced_portfolio_analysis.py
# """
# Enhanced portfolio analysis components supporting custom portfolios
# """

# import streamlit as st
# import pandas as pd
# import plotly.express as px
# import plotly.graph_objects as go
# from plotly.subplots import make_subplots
# from typing import Dict, List, Optional
# from ..services.portfolio_service import PortfolioService
# from ..services.api import get_portfolio_analysis
# from ..utils.helpers import format_currency, format_percentage


# def render_portfolio_analysis_dashboard():
#     """Main portfolio analysis dashboard"""
#     # Portfolio selection
#     selected_portfolio_id = render_advanced_portfolio_selector()
    
#     if not selected_portfolio_id:
#         render_no_portfolio_selected()
#         return
    
#     # Strategy and analysis settings
#     col1, col2, col3 = st.columns([2, 2, 1])
    
#     with col1:
#         strategy_type = st.selectbox(
#             "📊 Analysis Strategy",
#             ["market_neutral", "long_only"],
#             index=0 if st.session_state.get("strategy_type", "market_neutral") == "market_neutral" else 1,
#             key="analysis_strategy"
#         )
#         st.session_state.strategy_type = strategy_type
    
#     with col2:
#         analysis_period = st.selectbox(
#             "📅 Analysis Period",
#             ["1 Month", "3 Months", "6 Months", "1 Year"],
#             index=2,
#             key="analysis_period"
#         )
    
#     with col3:
#         if st.button("🔄 Refresh Analysis", use_container_width=True):
#             # Clear cache and refresh
#             PortfolioService.get_portfolio_analysis.clear()
#             st.rerun()
    
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