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
# COLORS (BLUE THEME)
# =====================================================
BG = "#0a0f1e"        # deep navy
PANEL = "#0f172a"     # slate panel
GRID = "#1e293b"
TEXT = "#e5e7eb"
MUTED = "#94a3b8"

BLUE_MAIN = "#38bdf8"
BLUE_SOFT = "#0ea5e9"
DOT = "#7dd3fc"

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

        section[data-testid="stSidebar"] {{
            background-color: {BG};
        }}

        div[data-baseweb="select"] {{
            max-width: 220px;
        }}

        input {{
            max-width: 220px;
        }}

        thead tr th {{
            background-color: {PANEL};
            color: {MUTED};
        }}

        tbody tr td {{
            background-color: {BG};
            color: {TEXT};
        }}
    </style>
    """,
    unsafe_allow_html=True
)

# =====================================================
# FILES
# =====================================================
EVENT_FILE = "data/eredivisie_event_metrics_merged_final.xlsx"
EPM_FILE = "data/Eredivisie EPM 2025-2026.xlsx"

# =====================================================
# LOAD DATA (ONLY 2025–2026)
# =====================================================
@st.cache_data
def load_data():
    events = pd.read_excel(EVENT_FILE)
    epm = pd.read_excel(EPM_FILE)

    # 🔒 HARD FILTER TO 2025–2026
    if "Season" in events.columns:
        events = events[events["Season"] == "2025-2026"]

    if "Season" in epm.columns:
        epm = epm[epm["Season"] == "2025-2026"]

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
    <h1 style="margin-bottom:0;font-weight:600;">
        Estimated Plus-Minus
    </h1>
    <p style="color:#94a3b8;margin-top:6px;">
        Eredivisie • 2025–26 season • Player impact model
    </p>
    """,
    unsafe_allow_html=True
)

# =====================================================
# SEARCH
# =====================================================
search = st.text_input(
    "Search player",
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
# LEFT — TABLE
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

    table_show["OFF"] = table_show["OFF"].round(2)
    table_show["DEF"] = table_show["DEF"].round(2)
    table_show["EPM"] = table_show["EPM"].round(2)

    st.dataframe(
        table_show,
        height=800,
        use_container_width=True,
    )

# =====================================================
# RIGHT — BEESWARM
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
        jitter=0.28,
        marker=dict(
            size=6,
            color=DOT,
            opacity=0.75,
        )
    )

    fig.update_layout(
        height=820,
        paper_bgcolor=BG,
        plot_bgcolor=BG,
        margin=dict(l=50, r=30, t=10, b=40),
        xaxis=dict(
            showgrid=False,
            showticklabels=False,
            zeroline=False,
        ),
        yaxis=dict(
            title="Estimated Plus-Minus",
            gridcolor=GRID,
            zeroline=True,
            zerolinecolor=GRID,
            tickfont=dict(color=TEXT, size=12),
            titlefont=dict(color=TEXT, size=13),
        ),
        showlegend=False,
    )

    st.plotly_chart(fig, use_container_width=True)

# =====================================================
# FOOTER
# =====================================================
st.markdown(
    """
    <hr style="border-color:#1e293b;">
    <small style="color:#94a3b8;">
        Hover dots for player details • Visual style inspired by dunksandthrees.com
    </small>
    """,
    unsafe_allow_html=True
)
