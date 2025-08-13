import streamlit as st
import time


from .analysis_cache import clear_all_portfolio_service_cache
from frontend.services.portfolio import PortfolioService


def render_create_portfolio_form():
    """Render create new portfolio form"""
    st.markdown("#### ➕ Create New Portfolio")

    with st.form("create_portfolio_form"):
        # Portfolio basic info
        col1, col2 = st.columns(2)

        with col1:
            portfolio_name = st.text_input(
                "Portfolio Name *",
                placeholder="My Tech Portfolio",
                help="Choose a descriptive name for your portfolio",
            )

        with col2:
            max_positions = st.number_input(
                "Max Positions",
                min_value=1,
                max_value=30,
                value=20,
                help="Maximum number of stocks in this portfolio",
            )

        portfolio_description = st.text_area(
            "Description (Optional)",
            placeholder="Brief description of your investment strategy...",
            height=100,
        )

        st.markdown("#### 📈 Select Stocks")

        # Initialize all symbols in session state if not already present
        if "all_symbols" not in st.session_state:
            st.session_state["all_symbols"] = PortfolioService.get_all_symbols()

        all_symbols = st.session_state["all_symbols"]
        selected_symbols = st.multiselect(
            "Select Symbols",
            options=all_symbols,
            default=[],
            max_selections=max_positions,
            placeholder="Choose symbols for your portfolio...",
            help=f"Select up to {max_positions} symbols from {len(all_symbols)} available stocks",
        )

        if selected_symbols:
            st.markdown(
                f"**Selected:** {len(selected_symbols)}/{max_positions} symbols"
            )

            cols = st.columns(5)
            for i, symbol in enumerate(selected_symbols):
                with cols[i % 5]:
                    st.success(f"✅ {symbol}")

        col1, col2, col3 = st.columns([1, 1, 2])

        with col1:
            create_portfolio = st.form_submit_button(
                "🚀 Create Portfolio", type="primary"
            )

        with col2:
            clear_form = st.form_submit_button("🗑️ Clear")

        if clear_form:
            st.rerun()

        if create_portfolio:
            # Use selected symbols from multiselect
            symbols = selected_symbols

            # Validation
            if not portfolio_name:
                st.error("Portfolio name is required!")
            elif len(symbols) < 2:
                st.error("Please select at least 2 symbols!")
            elif len(symbols) > max_positions:
                st.error(f"Too many symbols! Maximum is {max_positions}")
            else:
                # Create portfolio
                with st.spinner("Creating portfolio..."):
                    result = PortfolioService.create_custom_portfolio(
                        portfolio_name=portfolio_name,
                        symbols=symbols,
                        description=portfolio_description,
                    )

                if result["success"]:
                    st.success(f"✅ Portfolio '{portfolio_name}' created successfully!")
                    st.balloons()

                    # Clear service cache to refresh portfolio lists
                    clear_all_portfolio_service_cache()

                    # Auto-refresh portfolio list
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"❌ Failed to create portfolio: {result['error']}")