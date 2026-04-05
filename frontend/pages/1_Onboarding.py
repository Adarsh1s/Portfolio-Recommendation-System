"""
Page 1: Onboarding
Financial profile form — income, expenses, investment, horizon, goal.
"""

import streamlit as st
from utils.api import create_profile, update_profile, get_my_profile

st.set_page_config(page_title="Onboarding | Portfolio System", page_icon="📋", layout="centered")


def _require_login():
    if not st.session_state.get("token"):
        st.warning("Please log in first.")
        st.switch_page("app.py")


_require_login()

token = st.session_state.token

st.title("📋 Financial Profile")
st.markdown("Tell us about your finances so we can calculate the right investment allocation for you.")
st.divider()

# Pre-fill form if profile already exists
existing = get_my_profile(token)
defaults = existing or {}

INVESTMENT_GOALS = [
    "Wealth Creation",
    "Retirement Planning",
    "Child Education",
    "Home Purchase",
    "Emergency Fund",
    "Regular Income",
    "Tax Saving",
]

with st.form("onboarding_form"):
    st.subheader("Monthly Finances")
    col1, col2 = st.columns(2)
    with col1:
        income = st.number_input(
            "Monthly Income (₹)",
            min_value=1000.0, max_value=10_000_000.0,
            value=float(defaults.get("monthly_income", 50000)),
            step=1000.0, format="%.0f",
        )
    with col2:
        expenses = st.number_input(
            "Monthly Expenses (₹)",
            min_value=500.0, max_value=10_000_000.0,
            value=float(defaults.get("monthly_expenses", 30000)),
            step=500.0, format="%.0f",
        )

    st.subheader("Investment Details")
    investment = st.number_input(
        "Total Investment Amount (₹)",
        min_value=1000.0, max_value=100_000_000.0,
        value=float(defaults.get("investment_amount", 100000)),
        step=5000.0, format="%.0f",
        help="The lump sum you want to invest in this portfolio.",
    )

    horizon = st.slider(
        "Investment Horizon (Years)",
        min_value=1, max_value=30,
        value=int(defaults.get("investment_horizon_years", 5)),
        help="How long do you plan to stay invested?",
    )

    goal_default_idx = 0
    if defaults.get("investment_goal") in INVESTMENT_GOALS:
        goal_default_idx = INVESTMENT_GOALS.index(defaults["investment_goal"])
    goal = st.selectbox("Primary Investment Goal", INVESTMENT_GOALS, index=goal_default_idx)

    # Computed savings preview
    savings = income - expenses
    st.info(
        f"💡 Monthly Surplus: **₹{savings:,.0f}**  |  "
        f"Investment: **₹{investment:,.0f}**  |  "
        f"Horizon: **{horizon} years**"
    )

    submitted = st.form_submit_button(
        "Save Profile & Continue →",
        use_container_width=True, type="primary",
    )

if submitted:
    if expenses >= income:
        st.error("Monthly expenses must be less than monthly income.")
    else:
        payload = {
            "monthly_income":           income,
            "monthly_expenses":         expenses,
            "investment_amount":        investment,
            "investment_horizon_years": horizon,
            "investment_goal":          goal,
        }
        with st.spinner("Saving your profile…"):
            try:
                if existing:
                    update_profile(token, payload)
                else:
                    create_profile(token, payload)
                st.success("Profile saved!")
                st.switch_page("pages/2_Questionnaire.py")
            except ValueError as e:
                st.error(str(e))

if existing:
    st.divider()
    st.caption("Your profile is already set up. Submitting will update it and reset your risk score.")
