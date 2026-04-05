"""
Page 6: Profile
View and edit the user's financial profile.
"""

import streamlit as st
from utils.api import get_my_profile, update_profile

st.set_page_config(page_title="Profile | Portfolio System", page_icon="👤", layout="centered")


def _require_login():
    if not st.session_state.get("token"):
        st.warning("Please log in first.")
        st.switch_page("app.py")


_require_login()

token = st.session_state.token

st.title("👤 My Profile")
st.divider()

with st.spinner("Loading profile…"):
    profile = get_my_profile(token)

if not profile:
    st.info("No profile found. Set up your profile first.")
    if st.button("Go to Onboarding →", type="primary"):
        st.switch_page("pages/1_Onboarding.py")
    st.stop()

# ── Read-only current summary ─────────────────────────────────────────────────
st.subheader("Current Profile")

risk_badge = {
    "Conservative":           "🟢 Conservative",
    "Moderately Conservative": "🟡 Moderately Conservative",
    "Moderate":               "🟠 Moderate",
    "Aggressive":             "🔴 Aggressive",
}

c1, c2, c3 = st.columns(3)
c1.metric("Monthly Income",    f"₹{profile['monthly_income']:,.0f}")
c2.metric("Monthly Expenses",  f"₹{profile['monthly_expenses']:,.0f}")
c3.metric("Investment Amount", f"₹{profile['investment_amount']:,.0f}")

c4, c5, c6 = st.columns(3)
c4.metric("Investment Horizon", f"{profile['investment_horizon_years']} years")
c5.metric("Investment Goal",    profile["investment_goal"])
c6.metric(
    "Risk Profile",
    risk_badge.get(profile.get("risk_profile_name", ""), profile.get("risk_profile_name", "Not assessed")),
)

if profile.get("risk_score") is not None:
    st.progress(profile["risk_score"] / 100)
    st.caption(f"Risk Score: {profile['risk_score']}/100")

st.divider()

# ── Edit form ─────────────────────────────────────────────────────────────────
st.subheader("Update Profile")
st.caption("Updating your profile will reset your risk score. Please retake the questionnaire.")

INVESTMENT_GOALS = [
    "Wealth Creation", "Retirement Planning", "Child Education",
    "Home Purchase", "Emergency Fund", "Regular Income", "Tax Saving",
]
goal_idx = 0
if profile.get("investment_goal") in INVESTMENT_GOALS:
    goal_idx = INVESTMENT_GOALS.index(profile["investment_goal"])

with st.form("profile_update_form"):
    col1, col2 = st.columns(2)
    with col1:
        income = st.number_input(
            "Monthly Income (₹)", min_value=1000.0, max_value=10_000_000.0,
            value=float(profile["monthly_income"]), step=1000.0, format="%.0f",
        )
    with col2:
        expenses = st.number_input(
            "Monthly Expenses (₹)", min_value=500.0, max_value=10_000_000.0,
            value=float(profile["monthly_expenses"]), step=500.0, format="%.0f",
        )

    investment = st.number_input(
        "Total Investment Amount (₹)", min_value=1000.0, max_value=100_000_000.0,
        value=float(profile["investment_amount"]), step=5000.0, format="%.0f",
    )
    horizon = st.slider(
        "Investment Horizon (Years)", min_value=1, max_value=30,
        value=int(profile["investment_horizon_years"]),
    )
    goal = st.selectbox("Primary Investment Goal", INVESTMENT_GOALS, index=goal_idx)

    submitted = st.form_submit_button("Update Profile", use_container_width=True, type="primary")

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
        with st.spinner("Updating…"):
            try:
                update_profile(token, payload)
                st.success("Profile updated! Please retake the questionnaire to refresh your risk score.")
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button("Retake Questionnaire →", type="primary", use_container_width=True):
                        st.switch_page("pages/2_Questionnaire.py")
                with col_b:
                    if st.button("Back to Dashboard", use_container_width=True):
                        st.switch_page("pages/3_Dashboard.py")
            except ValueError as e:
                st.error(str(e))

st.divider()
st.caption(f"Account: {st.session_state.get('user_email', '')}  |  User ID: {st.session_state.get('user_id', '')}")
