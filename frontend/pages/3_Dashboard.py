"""
Page 3: Dashboard
Main portfolio view — risk badge, pie chart, instrument table,
expected returns card, and Regenerate button.
"""

import streamlit as st
import pandas as pd
from utils.api import (
    get_current_portfolio, generate_portfolio,
    get_portfolio_summary, get_expected_returns, get_my_profile,
)
from utils.charts import pie_chart, returns_bar

st.set_page_config(
    page_title="Dashboard | Portfolio System",
    page_icon="📊",
    layout="wide",
)


def _require_login():
    if not st.session_state.get("token"):
        st.warning("Please log in first.")
        st.switch_page("app.py")


_require_login()

token = st.session_state.token

# ── Header ────────────────────────────────────────────────────────────────────
col_title, col_user = st.columns([4, 1])
with col_title:
    st.title("📊 Portfolio Dashboard")
with col_user:
    st.markdown(f"**{st.session_state.get('user_name', '')}**")
    if st.button("Logout", use_container_width=True):
        st.session_state.clear()
        st.switch_page("app.py")

st.divider()

# ── Load profile and portfolio ────────────────────────────────────────────────
profile   = get_my_profile(token)
portfolio = get_current_portfolio(token)

# ── No profile yet ────────────────────────────────────────────────────────────
if not profile:
    st.info("👋 Welcome! Start by setting up your financial profile.")
    if st.button("Complete Onboarding →", type="primary"):
        st.switch_page("pages/1_Onboarding.py")
    st.stop()

# ── Profile exists but no risk score ─────────────────────────────────────────
if not profile.get("risk_score"):
    st.info("🧠 You need to complete the risk questionnaire before generating a portfolio.")
    if st.button("Take Questionnaire →", type="primary"):
        st.switch_page("pages/2_Questionnaire.py")
    st.stop()

# ── Risk profile badge ────────────────────────────────────────────────────────
risk_color_map = {
    "Conservative":           "🟢",
    "Moderately Conservative": "🟡",
    "Moderate":               "🟠",
    "Aggressive":             "🔴",
}
risk_name  = profile.get("risk_profile_name", "Unknown")
risk_score = profile.get("risk_score", 0)
risk_emoji = risk_color_map.get(risk_name, "⚪")

col_r1, col_r2, col_r3 = st.columns(3)
col_r1.metric("Risk Profile", f"{risk_emoji} {risk_name}")
col_r2.metric("Risk Score", f"{risk_score} / 100")
col_r3.metric("Investment Amount", f"₹{profile['investment_amount']:,.0f}")

st.divider()

# ── No portfolio yet — offer to generate ─────────────────────────────────────
if not portfolio:
    st.info("📦 No portfolio generated yet. Click below to create your first portfolio.")
    if st.button("Generate Portfolio →", type="primary", use_container_width=True):
        with st.spinner("Generating your portfolio…"):
            try:
                portfolio = generate_portfolio(token)
                st.success("Portfolio generated!")
                st.rerun()
            except ValueError as e:
                st.error(str(e))
    st.stop()

# ── Portfolio metadata ────────────────────────────────────────────────────────
st.subheader(f"📁 {portfolio['model_name']}  —  Version {portfolio['version']}")
meta_col1, meta_col2, meta_col3, meta_col4 = st.columns(4)
meta_col1.metric("Total Investment", f"₹{portfolio['total_investment']:,.0f}")
meta_col2.metric("Portfolio Version", portfolio["version"])
meta_col3.metric("Risk Profile", portfolio["risk_profile"])
meta_col4.metric(
    "Generated At",
    pd.to_datetime(portfolio["generated_at"]).strftime("%d %b %Y, %H:%M"),
)

st.divider()

# ── Asset class pie chart + Expected returns ──────────────────────────────────
summary = get_portfolio_summary(token)
returns = get_expected_returns(token)

chart_col, returns_col = st.columns([3, 2])

with chart_col:
    if summary:
        labels = [s["asset_class"] for s in summary]
        values = [s["total_allocated_amount"] for s in summary]
        fig    = pie_chart(labels, values, title="Asset Class Allocation")
        st.plotly_chart(fig, use_container_width=True)

with returns_col:
    if returns:
        st.subheader("Expected Returns")
        r1, r3, r5 = st.columns(3)
        r1.metric("1 Year",   f"{returns['weighted_return_1y']:.2f}%")
        r3.metric("3 Years",  f"{returns['weighted_return_3y']:.2f}%")
        r5.metric("5 Years",  f"{returns['weighted_return_5y']:.2f}%")
        fig_r = returns_bar(returns)
        st.plotly_chart(fig_r, use_container_width=True)
    else:
        st.info("Returns data unavailable.")

st.divider()

# ── Instrument allocation table ───────────────────────────────────────────────
st.subheader("📋 Instrument Allocation")

positions = portfolio.get("positions", [])
if positions:
    df = pd.DataFrame(positions)[
        ["asset_class", "instrument_name", "ticker", "instrument_type",
         "fund_house", "allocation_percentage", "allocated_amount"]
    ].rename(columns={
        "asset_class":           "Asset Class",
        "instrument_name":       "Instrument",
        "ticker":                "Ticker",
        "instrument_type":       "Type",
        "fund_house":            "Fund House",
        "allocation_percentage": "Allocation %",
        "allocated_amount":      "Amount (₹)",
    })

    df["Allocation %"] = df["Allocation %"].apply(lambda x: f"{x:.2f}%")
    df["Amount (₹)"]   = df["Amount (₹)"].apply(lambda x: f"₹{x:,.0f}")

    st.dataframe(df, use_container_width=True, hide_index=True)

st.divider()

# ── Regenerate button ─────────────────────────────────────────────────────────
st.subheader("🔄 Regenerate Portfolio")
st.caption(
    "Regenerating creates a new portfolio version based on your current risk profile and investment amount. "
    "Your previous version is archived in History."
)
if st.button("Regenerate Portfolio", use_container_width=True):
    with st.spinner("Generating new portfolio version…"):
        try:
            portfolio = generate_portfolio(token)
            st.success(f"Portfolio v{portfolio['version']} generated!")
            st.rerun()
        except ValueError as e:
            st.error(str(e))
