import streamlit as st

from frontend.utils.config import STREAMLIT_CONFIG

st.set_page_config(**STREAMLIT_CONFIG)

from frontend.styles.main import MAIN_CSS
from frontend.utils.helpers import init_session_state
from frontend.components.auth import render_auth_page, render_user_info_sidebar
from frontend.components.footer import render_footer
from frontend.components.dashboard import render_dashboard


st.markdown(MAIN_CSS, unsafe_allow_html=True)


def main():
    init_session_state()

    if not st.session_state.authenticated:
        render_auth_page()
    else:
        # Show user info in sidebar
        render_user_info_sidebar()
        render_dashboard()

    render_footer()


if __name__ == "__main__":
    main()
