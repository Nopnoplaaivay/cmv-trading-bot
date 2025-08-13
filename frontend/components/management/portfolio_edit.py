import streamlit as st
from typing import Dict


from .analysis_cache import (
    clear_all_portfolio_service_cache,
    clear_portfolio_analysis_cache,
)
from frontend.services.portfolio import PortfolioService


def render_edit_portfolio_form(portfolio: Dict):
    st.markdown("---")
    st.markdown("#### ✏️ Edit Portfolio")

    if "all_symbols" not in st.session_state:
        st.session_state["all_symbols"] = PortfolioService.get_all_symbols()

    with st.form(f"edit_portfolio_{portfolio['portfolioId']}"):
        current_symbols = [r["symbol"] for r in portfolio["records"]]
        st.markdown(f"**Current symbols:** {', '.join(current_symbols)}")

        available_symbols = [
            s for s in st.session_state["all_symbols"] if s not in current_symbols
        ]

        new_symbols = st.multiselect(
            "Add new symbols",
            options=available_symbols,
            placeholder="Select symbols to add to portfolio...",
            key=f"new_symbols_{portfolio['portfolioId']}",
            help=f"Choose from {len(available_symbols)} available symbols",
        )

        # Remove symbols
        if current_symbols:
            symbols_to_remove = st.multiselect(
                "Select symbols to remove",
                options=current_symbols,
                key=f"remove_symbols_{portfolio['portfolioId']}",
            )
        else:
            symbols_to_remove = []

        col1, col2, col3 = st.columns(3)
        with col1:
            save_changes = st.form_submit_button("💾 Save Changes", type="primary")

        with col2:
            cancel_edit = st.form_submit_button("❌ Cancel")

        if save_changes:
            updated_symbols = current_symbols.copy()

            if new_symbols:
                for symbol in new_symbols:
                    if symbol not in updated_symbols:
                        updated_symbols.append(symbol)

                st.success(
                    f"Added {len(new_symbols)} new symbols: {', '.join(new_symbols)}"
                )

            updated_symbols = [s for s in updated_symbols if s not in symbols_to_remove]

            if symbols_to_remove:
                st.info(
                    f"Removed {len(symbols_to_remove)} symbols: {', '.join(symbols_to_remove)}"
                )

            if len(updated_symbols) < 2:
                st.error("Portfolio must contain at least 2 symbols")
            else:
                result = PortfolioService.update_portfolio(
                    portfolio["portfolioId"], updated_symbols
                )

                if result["success"]:
                    st.success("Portfolio updated successfully!")

                    # Clear analysis cache for this portfolio
                    clear_portfolio_analysis_cache(portfolio["portfolioId"])

                    # Clear service cache to refresh portfolio lists
                    clear_all_portfolio_service_cache()

                    st.session_state[f"editing_{portfolio['portfolioId']}"] = False
                    # Keep expander open after successful update
                    expander_key = f"expander_{portfolio['portfolioId']}"
                    if expander_key in st.session_state:
                        st.session_state[expander_key] = True

                    # Show additional info about cache clearing
                    st.info(
                        "🔄 Portfolio cache cleared - analysis page will show updated data"
                    )
                    st.rerun()
                else:
                    st.error(f"Failed to update: {result['error']}")

        if cancel_edit:
            st.session_state[f"editing_{portfolio['portfolioId']}"] = False
            # Keep expander open when exiting edit mode
            expander_key = f"expander_{portfolio['portfolioId']}"
            if expander_key in st.session_state:
                st.session_state[expander_key] = True
            st.rerun()
