import streamlit as st
import pandas as pd
import plotly.express as px

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="Eredivisie EPM",
    layout="wide",
)

# =====================================================
# COLORS
# =====================================================
BG = "#0b1220"
GRID = "#334155"
TEXT = "#e5e7eb"
DOT = "#e5e7eb"

# =====================================================
# GLOBAL STYLE
# =====================================================
st.markdown(
    f"""
    <style>
        .stApp {{
            background-color: {BG};
            color: {TEXT};
        }}

        div[data-baseweb="select"] {{
            max-width: 200px;
        }}

        input {{
            max-width: 200px;
        }}
    </style>
    """,
    unsafe_allow_html=True
)

# =====================================================
# FILES
# =====================================================
EVENT_FILE = "data/eredivisie_event_metrics_merged_final.xlsx"
EPM_FILE = "data/Eredivisie EPM 2023-2024.xlsx"

# =====================================================
# LOAD DATA
# =====================================================
@st.cache_data
def load_data():
    events = pd.read_excel(EVENT_FILE)
    epm = pd.read_excel(EPM_FILE)

    df = events.merge(
        epm[["playerName", "Offensive EPM", "Defensive EPM", "Total EPM"]],
        on="playerName",
        how="left"
    )
    return df

df = load_data()

# =====================================================
# HEADER
# =====================================================
st.markdown(
    """
    <h1 style="margin-bottom:0;">Eredivisie Estimated Plus-Minus</h1>
    <p style="color:#9ca3af;margin-top:4px;">
        Player impact model • Percentiles • Interactive
    </p>
    """,
    unsafe_allow_html=True
)

# =====================================================
# FILTER BAR
# =====================================================
f1, f2, f3 = st.columns([3, 1, 1])

with f2:
    season = st.selectbox(
        "Season",
        ["2023–2024"],
        label_visibility="collapsed"
    )

with f3:
    search = st.text_input(
        "🔍",
        placeholder="Search player",
        label_visibility="collapsed"
    )

# =====================================================
# FILTER DATA
# =====================================================
table_df = df.copy()

if search:
    table_df = table_df[
        table_df["playerName"]
        .str.lower()
        .str.contains(search.lower())
    ]

# =====================================================
# MAIN LAYOUT
# =====================================================
left, right = st.columns([1.15, 1])

# =====================================================
# LEFT — TABLE ONLY
# =====================================================
with left:

    table_show = (
        table_df[[
            "playerName",
            "Team within selected timeframe",
            "Position",
            "Offensive EPM",
            "Defensive EPM",
            "Total EPM",
        ]]
        .rename(columns={
            "playerName": "PLAYER",
            "Team within selected timeframe": "TEAM",
            "Position": "POS",
            "Offensive EPM": "OFF",
            "Defensive EPM": "DEF",
            "Total EPM": "EPM",
        })
        .sort_values("EPM", ascending=False)
        .reset_index(drop=True)
    )

    st.dataframe(
        table_show,
        height=780,
        width="stretch",
    )

# =====================================================
# RIGHT — BEESWARM (NO COLOR SCALE ❗)
# =====================================================
with right:

    fig = px.strip(
        df,
        y="Total EPM",
        hover_data={
            "playerName": True,
            "Team within selected timeframe": True,
            "Position": True,
            "Total EPM": ":.2f",
        },
    )

    fig.update_traces(
        jitter=0.35,
        marker=dict(
            size=7,
            color=DOT,
            opacity=0.85,
        )
    )

    fig.update_layout(
        height=820,
        paper_bgcolor=BG,
        plot_bgcolor=BG,
        margin=dict(l=40, r=40, t=10, b=40),
        xaxis=dict(
            showgrid=False,
            showticklabels=False,
            zeroline=False,
        ),
        yaxis=dict(
            title="Estimated Plus-Minus",
            gridcolor=GRID,
            zerolinecolor=GRID,
            tickfont=dict(color=TEXT),
            titlefont=dict(color=TEXT),
        ),
        showlegend=False,
    )

    st.plotly_chart(fig, width="stretch")

# =====================================================
# FOOTER
# =====================================================
st.markdown(
    """
    <hr style="border-color:#334155;">
    <small style="color:#9ca3af;">
        Hover dots for player details • Inspired by dunksandthrees.com
    </small>
    """,
    unsafe_allow_html=True
)
