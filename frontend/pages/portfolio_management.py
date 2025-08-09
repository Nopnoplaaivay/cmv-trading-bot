import streamlit as st
import time
from datetime import datetime
from ..components.portfolio_management import (
    render_portfolio_list,
    render_create_portfolio_form,
    render_portfolio_settings,
    render_portfolio_comparison
)
from frontend.services.portfolio import PortfolioService


# def portfolio_management_page():
#     """Main portfolio management page"""
#     st.title("📊 Portfolio Management")
#     st.markdown("Create, manage, and analyze your custom investment portfolios")
    
#     # Quick stats at the top
#     render_portfolio_overview()
    
#     # Main content tabs
#     tab1, tab2, tab3, tab4 = st.tabs([
#         "📋 My Portfolios", 
#         "➕ Create New", 
#         "📊 Compare", 
#         "⚙️ Settings"
#     ])
    
#     with tab1:
#         render_my_portfolios_tab()
    
#     with tab2:
#         render_create_portfolio_tab()
    
#     with tab3:
#         render_comparison_tab()
    
#     with tab4:
#         render_settings_tab()


# def render_portfolio_overview():
#     """Render portfolio overview dashboard"""
#     portfolios = PortfolioService.get_my_portfolios()
    
#     if not portfolios:
#         st.info("🎯 Welcome! Create your first custom portfolio to get started.")
#         return
    
#     custom_portfolios = [p for p in portfolios if p.get('portfolio_type') == 'CUSTOM']
    
#     # Overview metrics
#     col1, col2, col3, col4 = st.columns(4)
    
#     with col1:
#         st.metric(
#             "📁 Total Portfolios",
#             len(custom_portfolios),
#             help="Number of custom portfolios you've created"
#         )
    
#     with col2:
#         total_symbols = sum(len(p.get('symbols', [])) for p in custom_portfolios)
#         st.metric(
#             "📈 Total Stocks",
#             total_symbols,
#             help="Total number of stocks across all portfolios"
#         )
    
#     with col3:
#         active_portfolios = sum(1 for p in custom_portfolios if p.get('is_active', True))
#         st.metric(
#             "🟢 Active Portfolios",
#             active_portfolios,
#             help="Number of currently active portfolios"
#         )
    
#     with col4:
#         avg_size = total_symbols / len(custom_portfolios) if custom_portfolios else 0
#         st.metric(
#             "📊 Avg Portfolio Size",
#             f"{avg_size:.1f}",
#             help="Average number of stocks per portfolio"
#         )
    
#     # Recent activity
#     if custom_portfolios:
#         st.markdown("#### 🕒 Recent Activity")
        
#         # Sort by creation date (mock for now)
#         recent_portfolio = custom_portfolios[0]  # Most recent
        
#         col1, col2 = st.columns([3, 1])
#         with col1:
#             st.info(f"📁 Last created: **{recent_portfolio['name']}** with {len(recent_portfolio.get('symbols', []))} stocks")
#         with col2:
#             if st.button("🔍 View Details", key="view_recent"):
#                 st.session_state.current_portfolio_id = recent_portfolio['id']
#                 st.rerun()


# def render_my_portfolios_tab():
#     """Enhanced my portfolios tab"""
#     st.markdown("### 📋 Your Investment Portfolios")
    
#     # Portfolio filter and search
#     col1, col2, col3 = st.columns([2, 2, 1])
    
#     with col1:
#         search_term = st.text_input(
#             "🔍 Search Portfolios",
#             placeholder="Search by name...",
#             key="portfolio_search"
#         )
    
#     with col2:
#         sort_by = st.selectbox(
#             "Sort by",
#             ["Name", "Date Created", "Number of Stocks", "Status"],
#             key="portfolio_sort"
#         )
    
#     with col3:
#         if st.button("🔄 Refresh", use_container_width=True):
#             PortfolioService.get_my_portfolios.clear()
#             st.rerun()
    
#     # Portfolio list
#     render_portfolio_list()
    
#     # Bulk actions
#     render_bulk_actions()


# def render_create_portfolio_tab():
#     """Enhanced create portfolio tab"""
#     st.markdown("### ➕ Create New Portfolio")
    
#     # Quick start templates
#     with st.expander("🚀 Quick Start Templates", expanded=True):
#         render_portfolio_templates()
    
#     # Main creation form
#     render_create_portfolio_form()


# def render_comparison_tab():
#     """Enhanced portfolio comparison"""
#     st.markdown("### 📊 Portfolio Comparison")
#     render_portfolio_comparison()
    
#     # Additional comparison features
#     with st.expander("🔧 Advanced Comparison Options", expanded=False):
#         st.markdown("#### Comparison Metrics")
        
#         metrics = st.multiselect(
#             "Select metrics to compare",
#             [
#                 "Expected Return",
#                 "Volatility",
#                 "Sharpe Ratio",
#                 "Maximum Drawdown",
#                 "Beta",
#                 "Alpha",
#                 "Correlation with Market"
#             ],
#             default=["Expected Return", "Volatility", "Sharpe Ratio"]
#         )
        
#         time_period = st.selectbox(
#             "Time period for analysis",
#             ["1 Month", "3 Months", "6 Months", "1 Year", "All Time"],
#             index=2
#         )
        
#         if st.button("📊 Generate Advanced Comparison"):
#             st.success("Advanced comparison generated! (Feature coming soon)")


# def render_settings_tab():
#     """Enhanced settings tab"""
#     st.markdown("### ⚙️ Portfolio Settings")
#     render_portfolio_settings()
    
#     # Additional settings
#     with st.expander("🔧 Advanced Settings", expanded=False):
#         st.markdown("#### Optimization Settings")
        
#         col1, col2 = st.columns(2)
        
#         with col1:
#             risk_aversion = st.slider(
#                 "Risk Aversion",
#                 min_value=0.1,
#                 max_value=2.0,
#                 value=1.0,
#                 step=0.1,
#                 help="Higher values prefer lower risk"
#             )
            
#             rebalance_frequency = st.selectbox(
#                 "Rebalancing Frequency",
#                 ["Daily", "Weekly", "Monthly", "Quarterly"],
#                 index=2
#             )
        
#         with col2:
#             transaction_cost = st.number_input(
#                 "Transaction Cost (%)",
#                 min_value=0.0,
#                 max_value=1.0,
#                 value=0.25,
#                 step=0.01,
#                 help="Estimated transaction cost per trade"
#             )
            
#             min_position_size = st.number_input(
#                 "Minimum Position Size (%)",
#                 min_value=0.1,
#                 max_value=10.0,
#                 value=1.0,
#                 step=0.1,
#                 help="Minimum weight for any position"
#             )
        
#         if st.button("💾 Save Advanced Settings"):
#             st.success("Settings saved successfully!")


# def render_portfolio_templates():
#     """Render portfolio templates for quick start"""
#     st.markdown("Choose a template to get started quickly:")
    
#     templates = {
#         "🏢 Vietnamese Blue Chips": {
#             "symbols": ["VIC", "VHM", "VCB", "TCB", "BID", "HPG", "VNM", "MSN", "GAS", "PLX"],
#             "description": "Large-cap stocks with strong fundamentals and market leadership"
#         },
#         "🏦 Banking Sector": {
#             "symbols": ["VCB", "TCB", "BID", "CTG", "MBB", "STB", "TPB", "ACB", "HDB", "LPB"],
#             "description": "Diversified banking portfolio covering major Vietnamese banks"
#         },
#         "🏗️ Real Estate Focus": {
#             "symbols": ["VHM", "VRE", "DXG", "KDH", "NVL", "PDR", "IDI", "IJC", "NBB", "CEO"],
#             "description": "Real estate developers and property companies"
#         },
#         "💻 Technology & Innovation": {
#             "symbols": ["FPT", "CMG", "ELC", "ITD", "CMT", "SAM", "VCG", "CMC", "VGI", "YEG"],
#             "description": "Technology, telecommunications, and innovation-focused companies"
#         },
#         "🏭 Industrial & Manufacturing": {
#             "symbols": ["HPG", "HSG", "POM", "DGC", "TVS", "DRC", "TLG", "BCM", "CTD", "HT1"],
#             "description": "Steel, manufacturing, and industrial companies"
#         },
#         "🛒 Consumer & Retail": {
#             "symbols": ["VNM", "SAB", "MSN", "MWG", "PNJ", "VRE", "DGW", "FRT", "VGC", "QNS"],
#             "description": "Consumer goods, retail, and food & beverage companies"
#         }
#     }
    
#     cols = st.columns(2)
    
#     for i, (name, template) in enumerate(templates.items()):
#         with cols[i % 2]:
#             with st.container():
#                 st.markdown(f"**{name}**")
#                 st.caption(template['description'])
#                 st.markdown(f"*Stocks: {', '.join(template['symbols'][:3])}... ({len(template['symbols'])} total)*")
                
#                 if st.button(f"Use Template", key=f"template_{i}"):
#                     st.session_state.selected_symbols = template['symbols'].copy()
#                     st.success(f"✅ Template loaded: {name}")
#                     time.sleep(1)
#                     st.rerun()
            
#             st.markdown("---")


# def render_bulk_actions():
#     """Render bulk actions for portfolio management"""
#     portfolios = PortfolioService.get_my_portfolios()
#     custom_portfolios = [p for p in portfolios if p.get('portfolio_type') == 'CUSTOM']
    
#     if not custom_portfolios:
#         return
    
#     st.markdown("#### 🔧 Bulk Actions")
    
#     # Portfolio selection for bulk actions
#     selected_portfolios = st.multiselect(
#         "Select portfolios for bulk actions",
#         options=[p['name'] for p in custom_portfolios],
#         key="bulk_select"
#     )
    
#     if selected_portfolios:
#         col1, col2, col3, col4 = st.columns(4)
        
#         with col1:
#             if st.button("📊 Bulk Analysis"):
#                 st.info("Running analysis for selected portfolios...")
#                 # Implementation for bulk analysis
        
#         with col2:
#             if st.button("🔄 Bulk Optimization"):
#                 st.info("Optimizing selected portfolios...")
#                 # Implementation for bulk optimization
        
#         with col3:
#             if st.button("📈 Export Data"):
#                 st.info("Exporting portfolio data...")
#                 # Implementation for data export
        
#         with col4:
#             if st.button("🗑️ Bulk Delete", type="secondary"):
#                 if st.session_state.get("confirm_bulk_delete", False):
#                     # Actually delete selected portfolios
#                     success_count = 0
#                     for portfolio_name in selected_portfolios:
#                         portfolio = next(p for p in custom_portfolios if p['name'] == portfolio_name)
#                         result = PortfolioService.delete_portfolio(portfolio['id'])
#                         if result['success']:
#                             success_count += 1
                    
#                     if success_count == len(selected_portfolios):
#                         st.success(f"✅ Successfully deleted {success_count} portfolios!")
#                     else:
#                         st.warning(f"⚠️ Deleted {success_count}/{len(selected_portfolios)} portfolios")
                    
#                     st.session_state.confirm_bulk_delete = False
#                     time.sleep(2)
#                     st.rerun()
#                 else:
#                     st.session_state.confirm_bulk_delete = True
#                     st.warning("⚠️ Click again to confirm bulk deletion!")


# # Additional utility functions
# def export_portfolio_data(portfolios: list) -> str:
#    """Export portfolio data to CSV format"""
#    import io
#    import csv
   
#    output = io.StringIO()
#    writer = csv.writer(output)
   
#    # Header
#    writer.writerow(['Portfolio Name', 'Type', 'Status', 'Symbols', 'Symbol Count', 'Created Date'])
   
#    # Data
#    for portfolio in portfolios:
#        writer.writerow([
#            portfolio['name'],
#            portfolio['portfolio_type'],
#            'Active' if portfolio.get('is_active', True) else 'Inactive',
#            ', '.join(portfolio.get('symbols', [])),
#            len(portfolio.get('symbols', [])),
#            portfolio.get('created_at', 'Unknown')
#        ])
   
#    return output.getvalue()