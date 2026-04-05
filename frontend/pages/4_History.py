"""
Page 4: History
All previous portfolio versions for the user.
"""

import streamlit as st
import pandas as pd
from utils.api import get_portfolio_history
from utils.charts import history_bar

st.set_page_config(page_title="History | Portfolio System", page_icon="📜", layout="wide")


def _require_login():
    if not st.session_state.get("token"):
        st.warning("Please log in first.")
        st.switch_page("app.py")


_require_login()

token = st.session_state.token

st.title("📜 Portfolio History")
st.markdown("All portfolio versions — newest first. Blue bars are active, grey are archived.")
st.divider()

with st.spinner("Loading history…"):
    history = get_portfolio_history(token)

if not history:
    st.info("No portfolio history yet. Generate your first portfolio on the Dashboard.")
    if st.button("Go to Dashboard →", type="primary"):
        st.switch_page("pages/3_Dashboard.py")
    st.stop()

# ── Summary bar chart ─────────────────────────────────────────────────────────
if len(history) > 1:
    fig = history_bar(history)
    st.plotly_chart(fig, use_container_width=True)
    st.divider()

# ── History table ─────────────────────────────────────────────────────────────
st.subheader(f"Total Versions: {len(history)}")

df = pd.DataFrame(history)
df["generated_at"]    = pd.to_datetime(df["generated_at"]).dt.strftime("%d %b %Y, %H:%M")
df["total_investment"] = df["total_investment"].apply(lambda x: f"₹{x:,.0f}")
df["is_active"]        = df["is_active"].apply(lambda x: "✅ Active" if x else "Archived")

df = df.rename(columns={
    "portfolio_id":     "ID",
    "version":          "Version",
    "total_investment": "Investment",
    "is_active":        "Status",
    "generated_at":     "Generated At",
    "model_name":       "Model",
    "risk_profile":     "Risk Profile",
})

st.dataframe(
    df[["Version", "Status", "Investment", "Model", "Risk Profile", "Generated At"]],
    use_container_width=True,
    hide_index=True,
)

# ── Version detail expander ───────────────────────────────────────────────────
st.divider()
st.subheader("Version Timeline")
for h in history:
    active_label = "🟢 Active" if h["is_active"] else "⚫ Archived"
    with st.expander(f"v{h['version']} — {active_label}  |  ₹{h['total_investment']:,.0f}  |  {h['model_name']}"):
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Version",    h["version"])
        c2.metric("Status",     "Active" if h["is_active"] else "Archived")
        c3.metric("Investment", f"₹{h['total_investment']:,.0f}")
        c4.metric("Generated",  pd.to_datetime(h["generated_at"]).strftime("%d %b %Y"))
        st.caption(f"Model: {h['model_name']}  |  Risk Profile: {h['risk_profile']}")
