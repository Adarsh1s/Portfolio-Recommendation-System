"""
Page 5: Compare
Side-by-side what-if comparison of the user's current portfolio
against any other risk profile model.
"""

import streamlit as st
from utils.api import compare_portfolio, get_my_profile
from utils.charts import side_by_side_pie

st.set_page_config(page_title="Compare | Portfolio System", page_icon="⚖️", layout="wide")


def _require_login():
    if not st.session_state.get("token"):
        st.warning("Please log in first.")
        st.switch_page("app.py")


_require_login()

token = st.session_state.token

st.title("⚖️ Portfolio Comparison")
st.markdown(
    "See how your current portfolio's asset allocation would differ "
    "if you had a different risk profile. Pure read-only — nothing changes."
)
st.divider()

profile = get_my_profile(token)
if not profile or not profile.get("risk_profile_id"):
    st.warning("Complete the risk questionnaire first.")
    st.stop()

# ── Risk level selector ───────────────────────────────────────────────────────
RISK_OPTIONS = {
    "Conservative":            "conservative",
    "Moderately Conservative": "moderately_conservative",
    "Moderate":                "moderate",
    "Aggressive":              "aggressive",
}

col_sel, col_btn = st.columns([3, 1])
with col_sel:
    selected_label = st.selectbox(
        "Compare against:",
        options=list(RISK_OPTIONS.keys()),
        index=2,
        help="Select any risk profile to see how that portfolio model allocates assets.",
    )
with col_btn:
    st.markdown("<br>", unsafe_allow_html=True)
    compare_clicked = st.button("Compare →", type="primary", use_container_width=True)

# ── Comparison result ─────────────────────────────────────────────────────────
if compare_clicked or "compare_data" in st.session_state:
    if compare_clicked:
        risk_key = RISK_OPTIONS[selected_label]
        with st.spinner("Fetching comparison data…"):
            try:
                data = compare_portfolio(token, risk_key)
                st.session_state["compare_data"]  = data
                st.session_state["compare_label"] = selected_label
            except ValueError as e:
                st.error(str(e))
                st.stop()

    data  = st.session_state.get("compare_data", {})
    label = st.session_state.get("compare_label", selected_label)

    current_alloc   = data.get("current_portfolio", [])
    compared_alloc  = data.get("compared_allocations", [])
    compared_model  = data.get("compared_model_name", label)

    if not current_alloc:
        st.error("No active portfolio found. Generate one on the Dashboard first.")
        st.stop()

    # ── Side-by-side pie charts ───────────────────────────────────────────────
    st.subheader(f"Your Portfolio  vs.  {compared_model}")

    left_labels = [a["asset_class"] for a in current_alloc]
    left_values = [a["total_allocation_pct"] for a in current_alloc]

    right_labels = [a["asset_class"] for a in compared_alloc]
    right_values = [a["allocation_percentage"] for a in compared_alloc]

    current_profile = profile.get("risk_profile_name", "Your Profile")

    fig = side_by_side_pie(
        left_labels=left_labels,   left_values=left_values,   left_title=current_profile,
        right_labels=right_labels, right_values=right_values, right_title=compared_model,
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Tabular comparison ────────────────────────────────────────────────────
    st.divider()
    st.subheader("Allocation Breakdown")

    # Merge into a comparison table
    current_map  = {a["asset_class"]: a["total_allocation_pct"] for a in current_alloc}
    compared_map = {a["asset_class"]: a["allocation_percentage"] for a in compared_alloc}
    all_classes  = sorted(set(list(current_map.keys()) + list(compared_map.keys())))

    rows = []
    for ac in all_classes:
        curr = current_map.get(ac, 0.0)
        comp = compared_map.get(ac, 0.0)
        diff = comp - curr
        rows.append({
            "Asset Class":             ac,
            current_profile:           f"{curr:.1f}%",
            compared_model:            f"{comp:.1f}%",
            "Difference":              f"{'+' if diff >= 0 else ''}{diff:.1f}%",
        })

    import pandas as pd
    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.caption("Difference = Compared model % minus your current %")
