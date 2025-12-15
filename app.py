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
BG = "#0a0f1e"
PANEL = "#0f172a"
GRID = "#1e293b"
TEXT = "#e5e7eb"
MUTED = "#94a3b8"
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
        thead tr th {{
            background-color: {PANEL};
            color: {MUTED};
        }}
        tbody tr td {{
            background-color: {BG};
            color: {TEXT};
        }}
        input {{
            max-width: 240px;
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
left, right = st.columns([1.25, 1])

# =====================================================
# LEFT — TABLE (EXTENDED METRICS)
# =====================================================
with left:

    table_show = (
        table_df[
            [
                "playerName",
                "Team within selected timeframe",
                "Position",

                # EPM
                "Offensive EPM",
                "Defensive EPM",
                "Total EPM",

                # Attacking
                "xG",
                "xA",
                "Goals",
                "Assists",
                "Key passes",
                "Shots",
                "Touches in box",

                # Defending / duels
                "Tackles",
                "Interceptions",
                "Shots blocked",
                "Aerial duels won, %",
            ]
        ]
        .rename(columns={
            "playerName": "PLAYER",
            "Team within selected timeframe": "TEAM",
            "Position": "POS",
            "Offensive EPM": "OFF",
            "Defensive EPM": "DEF",
            "Total EPM": "EPM",
            "Touches in box": "BOX TCH",
            "Shots blocked": "BLK",
            "Aerial duels won, %": "AERIAL %",
            "Key passes": "KP",
        })
        .sort_values("EPM", ascending=False)
        .reset_index(drop=True)
    )

    # Rounding
    round_cols = [
        "OFF", "DEF", "EPM", "xG", "xA", "AERIAL %"
    ]
    for c in round_cols:
        if c in table_show.columns:
            table_show[c] = table_show[c].round(2)

    st.dataframe(
        table_show,
        height=820,
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
        height=840,
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
            tickfont=dict(color=TEXT),
            titlefont=dict(color=TEXT),
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
        Extended attacking & defensive metrics • Style inspired by dunksandthrees.com
    </small>
    """,
    unsafe_allow_html=True
)
