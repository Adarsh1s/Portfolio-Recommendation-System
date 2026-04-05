"""
Portfolio Recommendation System
Home / Login / Register page
"""

import streamlit as st
from utils.api import login, register

st.set_page_config(
    page_title="Portfolio Recommendation System",
    page_icon="📈",
    layout="centered",
    initial_sidebar_state="collapsed",
)


def _init_session():
    for key in ("token", "user_id", "user_name", "user_email"):
        if key not in st.session_state:
            st.session_state[key] = None


def _is_logged_in() -> bool:
    return bool(st.session_state.get("token"))


def _redirect_if_logged_in():
    if _is_logged_in():
        st.switch_page("pages/3_Dashboard.py")


# ── Main ─────────────────────────────────────────────────────────────────────

_init_session()
_redirect_if_logged_in()

st.title("📈 Portfolio Recommendation System")
st.markdown(
    "A DBMS project demonstrating intelligent, risk-aligned investment portfolio "
    "generation for Indian market instruments."
)
st.divider()

tab_login, tab_register = st.tabs(["Login", "Create Account"])

# ── Login Tab ────────────────────────────────────────────────────────────────
with tab_login:
    st.subheader("Welcome back")
    with st.form("login_form"):
        email    = st.text_input("Email", placeholder="you@example.com")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login", use_container_width=True, type="primary")

    if submitted:
        if not email or not password:
            st.error("Please fill in all fields.")
        else:
            with st.spinner("Logging in…"):
                try:
                    data = login(email, password)
                    st.session_state.token      = data["access_token"]
                    st.session_state.user_id    = data["user_id"]
                    st.session_state.user_name  = data["name"]
                    st.session_state.user_email = data["email"]
                    st.success(f"Welcome back, {data['name']}!")
                    st.switch_page("pages/3_Dashboard.py")
                except ValueError as e:
                    st.error(str(e))

# ── Register Tab ─────────────────────────────────────────────────────────────
with tab_register:
    st.subheader("Create your account")
    with st.form("register_form"):
        name     = st.text_input("Full Name", placeholder="Arjun Sharma")
        email_r  = st.text_input("Email", placeholder="arjun@example.com")
        pass_r   = st.text_input("Password", type="password", help="Minimum 6 characters")
        pass_r2  = st.text_input("Confirm Password", type="password")
        submitted_r = st.form_submit_button("Create Account", use_container_width=True, type="primary")

    if submitted_r:
        if not all([name, email_r, pass_r, pass_r2]):
            st.error("Please fill in all fields.")
        elif pass_r != pass_r2:
            st.error("Passwords do not match.")
        elif len(pass_r) < 6:
            st.error("Password must be at least 6 characters.")
        else:
            with st.spinner("Creating your account…"):
                try:
                    data = register(name, email_r, pass_r)
                    st.session_state.token      = data["access_token"]
                    st.session_state.user_id    = data["user_id"]
                    st.session_state.user_name  = data["name"]
                    st.session_state.user_email = data["email"]
                    st.success("Account created! Let's set up your profile.")
                    st.switch_page("pages/1_Onboarding.py")
                except ValueError as e:
                    st.error(str(e))

st.divider()
st.caption("All instrument data is illustrative. Not financial advice.")
