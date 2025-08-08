# # Update frontend/components/enhanced_dashboard.py
# """
# Integration of enhanced portfolio management
# """

# def render_enhanced_dashboard():
#     """Enhanced dashboard with integrated portfolio management"""
#     st.markdown(
#         '<div class="main-header"><h1>📈 CMV Trading Bot v2.0</h1><p>Advanced Portfolio Management & Trading Platform</p></div>',
#         unsafe_allow_html=True,
#     )

#     # Enhanced sidebar with portfolio features
#     render_enhanced_sidebar()

#     # Main content routing with portfolio support
#     page = st.session_state.get("current_page", "Portfolio Analysis")
    
#     if page == "Portfolio Analysis":
#         from ..components.enhanced_portfolio_analysis import integrate_portfolio_analysis
#         integrate_portfolio_analysis()
#     elif page == "Portfolio Management":
#         from ..pages.portfolio_management_page import portfolio_management_page
#         portfolio_management_page()
#     elif page == "Trade Execution":
#         from ..pages.trade_execution import trade_execution_page
#         trade_execution_page()
#     elif page == "Order History":
#         from ..pages.order_history import order_history_page
#         order_history_page()
#     elif page == "Account Management":
#         from ..pages.account_management import account_management_page
#         account_management_page()


# # Update the main application runner
# # run_enhanced_frontend.py
# """
# Enhanced frontend application runner
# """

# import subprocess
# import sys
# import os

# def run_enhanced_frontend():
#     """Run the enhanced Streamlit frontend"""
#     try:
#         # Set environment variables for enhanced features
#         os.environ["STREAMLIT_THEME_PRIMARY_COLOR"] = "#2a5298"
#         os.environ["STREAMLIT_THEME_BACKGROUND_COLOR"] = "#ffffff"
#         os.environ["STREAMLIT_THEME_SECONDARY_BACKGROUND_COLOR"] = "#f0f2f6"
        
#         # Run enhanced Streamlit app
#         subprocess.run([
#             sys.executable,
#             "-m", "streamlit", "run",
#             "frontend_enhanced.py",
#             "--server.port", "8501",
#             "--server.address", "0.0.0.0",
#             "--theme.primaryColor", "#2a5298",
#             "--theme.backgroundColor", "#ffffff",
#             "--theme.secondaryBackgroundColor", "#f0f2f6"
#         ])
        
#     except KeyboardInterrupt:
#         print("\n🛑 Enhanced frontend stopped by user")
#     except Exception as e:
#         print(f"❌ Error running enhanced frontend: {e}")

# if __name__ == "__main__":
#     run_enhanced_frontend()