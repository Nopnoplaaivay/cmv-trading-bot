# # frontend/components/portfolio_management.py
# """
# Portfolio management components
# """

# import streamlit as st
# import pandas as pd
# from typing import List, Dict, Optional
# from ..services.portfolio_service import PortfolioService
# from ..utils.helpers import format_currency, format_percentage


# def render_portfolio_selector() -> Optional[str]:
#     """Render portfolio selector in sidebar"""
#     portfolios = PortfolioService.get_my_portfolios()
    
#     if not portfolios:
#         st.sidebar.warning("No portfolios found. Create your first portfolio!")
#         return None
    
#     # Add system portfolio option
#     portfolio_options = ["System Portfolio (Top 20)"] + [
#         f"{p['name']} ({len(p.get('symbols', []))} stocks)" 
#         for p in portfolios if p.get('portfolio_type') == 'CUSTOM'
#     ]
    
#     selected_option = st.sidebar.selectbox(
#         "📊 Select Portfolio",
#         portfolio_options,
#         key="portfolio_selector"
#     )
    
#     if selected_option == "System Portfolio (Top 20)":
#         return "SYSTEM"
#     else:
#         # Find the corresponding portfolio ID
#         for portfolio in portfolios:
#             if portfolio.get('portfolio_type') == 'CUSTOM':
#                 option_text = f"{portfolio['name']} ({len(portfolio.get('symbols', []))} stocks)"
#                 if option_text == selected_option:
#                     return portfolio['id']
    
#     return None


# def render_portfolio_management_page():
#     """Main portfolio management page"""
#     st.subheader("📊 Portfolio Management")
    
#     # Create tabs
#     tab1, tab2, tab3 = st.tabs(["📋 My Portfolios", "➕ Create New", "⚙️ Settings"])
    
#     with tab1:
#         render_portfolio_list()
    
#     with tab2:
#         render_create_portfolio_form()
    
#     with tab3:
#         render_portfolio_settings()


# def render_portfolio_list():
#     """Display list of user portfolios"""
#     st.markdown("#### 📋 Your Portfolios")
    
#     portfolios = PortfolioService.get_my_portfolios()
    
#     if not portfolios:
#         st.info("🎯 You don't have any custom portfolios yet. Create your first one!")
#         return
    
#     # System portfolio info
#     with st.expander("🏢 System Portfolio (Default)", expanded=False):
#         st.markdown("""
#         **System Portfolio** contains the top 20 stocks selected by our algorithm each month:
#         - ✅ Automatically updated monthly
#         - 📊 Based on fundamental analysis
#         - 🎯 Optimized for Vietnamese market
#         """)
    
#     # Custom portfolios
#     custom_portfolios = [p for p in portfolios if p.get('portfolio_type') == 'CUSTOM']
    
#     if not custom_portfolios:
#         st.info("No custom portfolios found.")
#         return
    
#     for portfolio in custom_portfolios:
#         render_portfolio_card(portfolio)


# def render_portfolio_card(portfolio: Dict):
#     """Render individual portfolio card"""
#     with st.expander(f"📁 {portfolio['name']}", expanded=False):
#         col1, col2, col3 = st.columns([2, 2, 1])
        
#         with col1:
#             st.markdown(f"**Portfolio ID:** `{portfolio['id'][:8]}...`")
#             st.markdown(f"**Type:** {portfolio['portfolio_type']}")
#             st.markdown(f"**Status:** {'🟢 Active' if portfolio.get('is_active') else '🔴 Inactive'}")
            
#         with col2:
#             symbols = portfolio.get('symbols', [])
#             st.markdown(f"**Stocks Count:** {len(symbols)}")
#             if symbols:
#                 st.markdown(f"**Symbols:** {', '.join(symbols[:5])}")
#                 if len(symbols) > 5:
#                     st.markdown(f"*... and {len(symbols) - 5} more*")
        
#         with col3:
#             if st.button("✏️ Edit", key=f"edit_{portfolio['id']}"):
#                 st.session_state[f"editing_{portfolio['id']}"] = True
#                 st.rerun()
            
#             if st.button("🗑️ Delete", key=f"delete_{portfolio['id']}"):
#                 if st.session_state.get(f"confirm_delete_{portfolio['id']}", False):
#                     # Actually delete
#                     result = PortfolioService.delete_portfolio(portfolio['id'])
#                     if result['success']:
#                         st.success("Portfolio deleted successfully!")
#                         st.rerun()
#                     else:
#                         st.error(f"Failed to delete: {result['error']}")
#                 else:
#                     # Ask for confirmation
#                     st.session_state[f"confirm_delete_{portfolio['id']}"] = True
#                     st.warning("Click again to confirm deletion!")
#                     st.rerun()
        
#         # Edit mode
#         if st.session_state.get(f"editing_{portfolio['id']}", False):
#             render_edit_portfolio_form(portfolio)


# def render_edit_portfolio_form(portfolio: Dict):
#     """Render edit form for portfolio"""
#     st.markdown("---")
#     st.markdown("#### ✏️ Edit Portfolio")
    
#     with st.form(f"edit_portfolio_{portfolio['id']}"):
#         # Current symbols
#         current_symbols = portfolio.get('symbols', [])
#         st.markdown(f"**Current symbols:** {', '.join(current_symbols)}")
        
#         # Symbol management
#         col1, col2 = st.columns([3, 1])
        
#         with col1:
#             new_symbol = st.text_input(
#                 "Add new symbol",
#                 placeholder="Enter symbol (e.g., VIC)",
#                 key=f"new_symbol_{portfolio['id']}"
#             ).upper()
        
#         with col2:
#             add_symbol = st.form_submit_button("➕ Add")
        
#         # Remove symbols
#         if current_symbols:
#             symbols_to_remove = st.multiselect(
#                 "Select symbols to remove",
#                 options=current_symbols,
#                 key=f"remove_symbols_{portfolio['id']}"
#             )
#         else:
#             symbols_to_remove = []
        
#         # Form actions
#         col1, col2, col3 = st.columns(3)
        
#         with col1:
#             save_changes = st.form_submit_button("💾 Save Changes", type="primary")
        
#         with col2:
#             cancel_edit = st.form_submit_button("❌ Cancel")
        
#         if add_symbol and new_symbol:
#             if new_symbol not in current_symbols:
#                 current_symbols.append(new_symbol)
#                 st.success(f"Added {new_symbol}")
#             else:
#                 st.warning(f"{new_symbol} already in portfolio")
        
#         if save_changes:
#             # Remove selected symbols
#             updated_symbols = [s for s in current_symbols if s not in symbols_to_remove]
            
#             if len(updated_symbols) == 0:
#                 st.error("Portfolio must contain at least 1 symbol")
#             else:
#                 result = PortfolioService.update_portfolio_symbols(
#                     portfolio['id'], updated_symbols
#                 )
                
#                 if result['success']:
#                     st.success("Portfolio updated successfully!")
#                     st.session_state[f"editing_{portfolio['id']}"] = False
#                     st.rerun()
#                 else:
#                     st.error(f"Failed to update: {result['error']}")
        
#         if cancel_edit:
#             st.session_state[f"editing_{portfolio['id']}"] = False
#             st.rerun()


# def render_create_portfolio_form():
#     """Render create new portfolio form"""
#     st.markdown("#### ➕ Create New Portfolio")
    
#     with st.form("create_portfolio_form"):
#         # Portfolio basic info
#         col1, col2 = st.columns(2)
        
#         with col1:
#             portfolio_name = st.text_input(
#                 "Portfolio Name *",
#                 placeholder="My Tech Portfolio",
#                 help="Choose a descriptive name for your portfolio"
#             )
        
#         with col2:
#             max_positions = st.number_input(
#                 "Max Positions",
#                 min_value=1,
#                 max_value=50,
#                 value=20,
#                 help="Maximum number of stocks in this portfolio"
#             )
        
#         portfolio_description = st.text_area(
#             "Description (Optional)",
#             placeholder="Brief description of your investment strategy...",
#             height=100
#         )
        
#         # Symbol selection
#         st.markdown("#### 📈 Select Stocks")
        
#         # Symbol search
#         search_query = st.text_input(
#             "🔍 Search Symbols",
#             placeholder="Type to search (e.g., VIC, VCB, FPT...)",
#             help="Search for Vietnamese stock symbols"
#         )
        
#         # Show available symbols
#         if search_query:
#             available_symbols = PortfolioService.search_symbols(search_query)
#             if available_symbols:
#                 st.markdown("**Search Results:**")
#                 cols = st.columns(5)
#                 for i, symbol in enumerate(available_symbols[:10]):
#                     with cols[i % 5]:
#                         if st.button(f"➕ {symbol}", key=f"add_{symbol}"):
#                             if 'selected_symbols' not in st.session_state:
#                                 st.session_state.selected_symbols = []
#                             if symbol not in st.session_state.selected_symbols:
#                                 st.session_state.selected_symbols.append(symbol)
#                                 st.rerun()
        
#         # Selected symbols
#         if 'selected_symbols' not in st.session_state:
#             st.session_state.selected_symbols = []
        
#         if st.session_state.selected_symbols:
#             st.markdown("**Selected Symbols:**")
            
#             # Display selected symbols with remove option
#             cols = st.columns(5)
#             for i, symbol in enumerate(st.session_state.selected_symbols):
#                 with cols[i % 5]:
#                     if st.button(f"❌ {symbol}", key=f"remove_{symbol}"):
#                         st.session_state.selected_symbols.remove(symbol)
#                         st.rerun()
            
#             st.markdown(f"**Total selected:** {len(st.session_state.selected_symbols)}/{max_positions}")
        
#         # Manual symbol input
#         st.markdown("#### ✍️ Or Add Manually")
#         manual_symbols = st.text_input(
#             "Enter symbols (comma-separated)",
#             placeholder="VIC, VCB, FPT, HPG",
#             help="Enter stock symbols separated by commas"
#         )
        
#         # Form submission
#         col1, col2, col3 = st.columns([1, 1, 2])
        
#         with col1:
#             create_portfolio = st.form_submit_button("🚀 Create Portfolio", type="primary")
        
#         with col2:
#             clear_form = st.form_submit_button("🗑️ Clear")
        
#         if clear_form:
#             st.session_state.selected_symbols = []
#             st.rerun()
        
#         if create_portfolio:
#             # Combine selected and manual symbols
#             symbols = st.session_state.selected_symbols.copy()
            
#             if manual_symbols:
#                 manual_list = [s.strip().upper() for s in manual_symbols.split(',') if s.strip()]
#                 symbols.extend([s for s in manual_list if s not in symbols])
            
#             # Validation
#             if not portfolio_name:
#                 st.error("Portfolio name is required!")
#             elif not symbols:
#                 st.error("Please select at least 1 symbol!")
#             elif len(symbols) > max_positions:
#                 st.error(f"Too many symbols! Maximum is {max_positions}")
#             else:
#                 # Create portfolio
#                 with st.spinner("Creating portfolio..."):
#                     result = PortfolioService.create_custom_portfolio(
#                         name=portfolio_name,
#                         symbols=symbols,
#                         description=portfolio_description,
#                         max_positions=max_positions
#                     )
                
#                 if result['success']:
#                     st.success(f"✅ Portfolio '{portfolio_name}' created successfully!")
#                     st.balloons()
                    
#                     # Clear form
#                     st.session_state.selected_symbols = []
                    
#                     # Show portfolio info
#                     st.info(f"Portfolio ID: `{result['data']['portfolio_id']}`")
                    
#                     # Auto-refresh portfolio list
#                     time.sleep(2)
#                     st.rerun()
#                 else:
#                     st.error(f"❌ Failed to create portfolio: {result['error']}")


# def render_portfolio_settings():
#     """Render portfolio settings"""
#     st.markdown("#### ⚙️ Portfolio Settings")
    
#     # Global settings
#     with st.expander("🌐 Global Settings", expanded=True):
#         st.checkbox("Auto-optimize portfolios daily", value=True)
#         st.checkbox("Send portfolio notifications", value=True)
#         st.selectbox(
#             "Default strategy",
#             ["market_neutral", "long_only"],
#             index=0
#         )
        
#         st.slider(
#             "Risk tolerance",
#             min_value=1,
#             max_value=10,
#             value=5,
#             help="1 = Conservative, 10 = Aggressive"
#         )
    
#     # Portfolio templates
#     with st.expander("📋 Portfolio Templates", expanded=False):
#         st.markdown("**Quick Start Templates:**")
        
#         templates = {
#             "🏢 Blue Chip": ["VIC", "VHM", "VCB", "TCB", "BID", "HPG", "VNM", "MSN"],
#             "🏦 Banking": ["VCB", "TCB", "BID", "CTG", "MBB", "STB", "TPB", "ACB"],
#             "🏗️ Real Estate": ["VHM", "VRE", "DXG", "KDH", "NVL", "PDR", "IDI", "IJC"],
#             "💻 Technology": ["FPT", "CMG", "ELC", "ITD", "CMT", "SAM", "VCG", "CMC"],
#         }
        
#         for template_name, symbols in templates.items():
#             col1, col2 = st.columns([3, 1])
            
#             with col1:
#                 st.markdown(f"**{template_name}:** {', '.join(symbols)}")
            
#             with col2:
#                 if st.button(f"Use Template", key=f"template_{template_name}"):
#                     st.session_state.selected_symbols = symbols
#                     st.success(f"Template {template_name} loaded!")
#                     st.rerun()


# def render_portfolio_comparison():
#     """Render portfolio comparison view"""
#     st.subheader("📊 Portfolio Comparison")
    
#     portfolios = PortfolioService.get_my_portfolios()
#     if not portfolios or len(portfolios) < 2:
#         st.info("Create at least 2 portfolios to compare performance")
#         return
    
#     # Select portfolios to compare
#     portfolio_names = [p['name'] for p in portfolios]
#     selected_portfolios = st.multiselect(
#         "Select portfolios to compare",
#         options=portfolio_names,
#         default=portfolio_names[:2] if len(portfolio_names) >= 2 else []
#     )
    
#     if len(selected_portfolios) < 2:
#         st.warning("Select at least 2 portfolios for comparison")
#         return
    
#     # Comparison metrics
#     comparison_data = []
#     for portfolio_name in selected_portfolios:
#         portfolio = next(p for p in portfolios if p['name'] == portfolio_name)
        
#         # Get analysis for this portfolio
#         analysis = PortfolioService.get_portfolio_analysis(
#             portfolio['id'],
#             st.session_state.get("strategy_type", "market_neutral")
#         )
        
#         if analysis:
#             comparison_data.append({
#                 "Portfolio": portfolio_name,
#                 "Stocks": len(portfolio.get('symbols', [])),
#                 "Expected Return": f"{analysis.get('expected_return', 0):.2%}",
#                 "Risk (Volatility)": f"{analysis.get('volatility', 0):.2%}",
#                 "Sharpe Ratio": f"{analysis.get('sharpe_ratio', 0):.3f}",
#             })
    
#     if comparison_data:
#         df_comparison = pd.DataFrame(comparison_data)
#         st.dataframe(
#             df_comparison,
#             use_container_width=True,
#             hide_index=True
#         )
        
#         # Visual comparison
#         st.markdown("#### 📈 Performance Visualization")
        
#         # Create mock chart data (replace with real data)
#         import plotly.graph_objects as go
        
#         fig = go.Figure()
        
#         for portfolio_name in selected_portfolios:
#             # Mock performance data
#             dates = pd.date_range(start="2024-01-01", periods=100, freq="D")
#             returns = np.random.normal(0.001, 0.02, 100)
#             cumulative = np.cumprod(1 + returns) * 100
            
#             fig.add_trace(go.Scatter(
#                 x=dates,
#                 y=cumulative,
#                 mode='lines',
#                 name=portfolio_name,
#                 line=dict(width=2)
#             ))
        
#         fig.update_layout(
#             title="Portfolio Performance Comparison",
#             xaxis_title="Date",
#             yaxis_title="Cumulative Return (%)",
#             height=500
#         )
        
#         st.plotly_chart(fig, use_container_width=True)


# # Portfolio analysis with custom portfolios
# def render_enhanced_portfolio_analysis():
#     """Enhanced portfolio analysis supporting custom portfolios"""
#     # Portfolio selector
#     selected_portfolio_id = render_portfolio_selector()
    
#     if not selected_portfolio_id:
#         st.warning("Please select a portfolio to analyze")
#         return
    
#     strategy_type = st.session_state.get("strategy_type", "market_neutral")
    
#     # Get analysis
#     with st.spinner("📊 Analyzing portfolio..."):
#         if selected_portfolio_id == "SYSTEM":
#             # Use existing system portfolio analysis
#             analysis_data = get_portfolio_analysis(
#                 st.session_state.get("broker_account_id"),
#                 strategy_type
#             )
#         else:
#             # Get custom portfolio analysis
#             analysis_data = PortfolioService.get_portfolio_analysis(
#                 selected_portfolio_id, strategy_type
#             )
    
#     if not analysis_data:
#         st.error("Failed to load portfolio analysis")
#         return
    
#     # Display analysis (reuse existing components)
#     display_portfolio_summary(analysis_data)
    
#     # Enhanced tabs for custom portfolios
#     tab1, tab2, tab3, tab4, tab5 = st.tabs([
#         "📊 Positions", "🎯 Recommendations", "📈 Performance", 
#         "⚖️ Comparison", "⚙️ Settings"
#     ])
    
#     with tab1:
#         display_current_positions(analysis_data.get("current_positions", []))
    
#     with tab2:
#         display_recommendations_tab(analysis_data.get("recommendations", []))
    
#     with tab3:
#         display_performance_analysis(analysis_data)
    
#     with tab4:
#         render_portfolio_comparison()
    
#     with tab5:
#         render_portfolio_settings()