import streamlit as st

from frontend.components.user_management import (
    render_create_user_form,
    render_edit_user_form,
    render_delete_user_form,
    render_users_list
)


def user_management_page():
    if not st.session_state.get("authenticated", False):
        st.error("❌ Please login to access this page")
        return

    if st.session_state.get("role") != "admin":
        st.error("❌ Access denied. This page is only accessible by administrators.")
        return

    st.title("👥 User Management")
    st.markdown("---")

    # Create tabs for different management functions
    tab1, tab2, tab3, tab4 = st.tabs(
        ["📋 All Users", "➕ Create User", "✏️ Edit User", "🗑️ Delete User"]
    )

    with tab1:
        render_users_list()

    with tab2:
        render_create_user_form()

    with tab3:
        render_edit_user_form()

    with tab4:
        render_delete_user_form()
