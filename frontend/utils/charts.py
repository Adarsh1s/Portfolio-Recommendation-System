"""
Chart Builders
--------------
All Plotly chart factory functions used across Streamlit pages.
"""

import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


ASSET_CLASS_COLORS = {
    "Equity":        "#4C72B0",
    "Debt":          "#55A868",
    "Gold":          "#C44E52",
    "Cash & Liquid": "#8172B2",
    "International": "#CCB974",
    "Real Estate":   "#64B5CD",
}

DEFAULT_COLORS = px.colors.qualitative.Set2


def pie_chart(labels: list, values: list, title: str = "") -> go.Figure:
    """Single pie chart for asset class allocation."""
    colors = [ASSET_CLASS_COLORS.get(l, DEFAULT_COLORS[i % len(DEFAULT_COLORS)])
              for i, l in enumerate(labels)]
    fig = go.Figure(
        go.Pie(
            labels=labels,
            values=values,
            hole=0.38,
            marker=dict(colors=colors, line=dict(color="#ffffff", width=2)),
            textinfo="label+percent",
            hovertemplate="<b>%{label}</b><br>%{percent}<br>₹%{value:,.0f}<extra></extra>",
        )
    )
    fig.update_layout(
        title=dict(text=title, x=0.5, font=dict(size=16)),
        showlegend=True,
        legend=dict(orientation="v", x=1.02, y=0.5),
        margin=dict(l=20, r=120, t=50, b=20),
        height=380,
    )
    return fig


def side_by_side_pie(
    left_labels: list, left_values: list, left_title: str,
    right_labels: list, right_values: list, right_title: str,
) -> go.Figure:
    """Two donut pies side by side for the Compare page."""
    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{"type": "domain"}, {"type": "domain"}]],
        subplot_titles=[left_title, right_title],
    )

    def _colors(labels):
        return [ASSET_CLASS_COLORS.get(l, "#aaaaaa") for l in labels]

    fig.add_trace(
        go.Pie(
            labels=left_labels, values=left_values,
            hole=0.38, marker=dict(colors=_colors(left_labels)),
            textinfo="label+percent", name=left_title,
            hovertemplate="<b>%{label}</b><br>%{percent}<extra></extra>",
        ),
        row=1, col=1,
    )
    fig.add_trace(
        go.Pie(
            labels=right_labels, values=right_values,
            hole=0.38, marker=dict(colors=_colors(right_labels)),
            textinfo="label+percent", name=right_title,
            hovertemplate="<b>%{label}</b><br>%{percent}<extra></extra>",
        ),
        row=1, col=2,
    )
    fig.update_layout(
        showlegend=False,
        margin=dict(l=20, r=20, t=60, b=20),
        height=360,
    )
    return fig


def returns_bar(returns: dict) -> go.Figure:
    """Horizontal bar chart showing 1Y / 3Y / 5Y blended returns."""
    periods = ["1 Year", "3 Years", "5 Years"]
    values  = [
        returns.get("weighted_return_1y", 0),
        returns.get("weighted_return_3y", 0),
        returns.get("weighted_return_5y", 0),
    ]
    colors = ["#4C72B0", "#55A868", "#C44E52"]
    fig = go.Figure(
        go.Bar(
            x=values, y=periods,
            orientation="h",
            marker_color=colors,
            text=[f"{v:.2f}%" for v in values],
            textposition="outside",
            hovertemplate="<b>%{y}</b>: %{x:.2f}%<extra></extra>",
        )
    )
    fig.update_layout(
        title=dict(text="Expected Blended Returns", x=0.5),
        xaxis=dict(title="Return %", ticksuffix="%", range=[0, max(values) * 1.3 + 2]),
        yaxis=dict(title=""),
        margin=dict(l=80, r=60, t=50, b=40),
        height=220,
        showlegend=False,
    )
    return fig


def history_bar(history: list) -> go.Figure:
    """Bar chart of total investment amount per portfolio version."""
    versions     = [f"v{h['version']}" for h in history]
    investments  = [h["total_investment"] for h in history]
    active_flags = [h["is_active"] for h in history]
    colors       = ["#4C72B0" if a else "#cccccc" for a in active_flags]

    fig = go.Figure(
        go.Bar(
            x=versions, y=investments,
            marker_color=colors,
            text=[f"₹{v:,.0f}" for v in investments],
            textposition="outside",
            hovertemplate="<b>%{x}</b><br>₹%{y:,.0f}<extra></extra>",
        )
    )
    fig.update_layout(
        title=dict(text="Portfolio Versions — Investment Amount", x=0.5),
        xaxis_title="Version",
        yaxis_title="Investment (₹)",
        margin=dict(l=60, r=40, t=50, b=40),
        height=280,
        showlegend=False,
    )
    return fig
