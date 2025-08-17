
import streamlit as st

from frontend.utils.helpers import init_session_state
from frontend.components.auth import render_login_form, render_register_form, logout_and_redirect


def render_auth_page():
    st.markdown(
        '<div class="main-header"><h1>🔐 CMV Portfolio Management Website</h1><p>Professional Portfolio Management System</p></div>',
        unsafe_allow_html=True,
    )
    init_session_state()
    if st.session_state.get("authenticated", False):
        st.success("✅ You are already logged in!")
        if st.button("🚪 Logout", key="auth_logout_btn_1"):
            logout_and_redirect()
        return

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        with st.container():
            if "auth_mode" not in st.session_state:
                st.session_state.auth_mode = "login"

            if st.session_state.auth_mode == "login":
                render_login_form()
            else:
                render_register_form()

            st.markdown("</div>", unsafe_allow_html=True)
