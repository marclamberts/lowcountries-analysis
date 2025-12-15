import streamlit as st
import pandas as pd
import numpy as np

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
BG = "#0a0f1e"
PANEL = "#0f172a"
TEXT = "#e5e7eb"
MUTED = "#94a3b8"

GREEN_RGB = (34, 197, 94)  # subtle green

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
            font-size: 12px;
        }}

        tbody tr:hover td {{
            background-color: rgba(148,163,184,0.08);
        }}

        tbody tr td {{
            font-size: 12px;
        }}

        /* Sticky first 3 columns */
        th:nth-child(-n+3), td:nth-child(-n+3) {{
            position: sticky;
            left: 0;
            background-color: {BG};
            z-index: 2;
        }}

        th:nth-child(1), td:nth-child(1) {{ left: 0px; }}
        th:nth-child(2), td:nth-child(2) {{ left: 140px; }}
        th:nth-child(3), td:nth-child(3) {{ left: 260px; }}
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
# LOAD DATA
# =====================================================
@st.cache_data
def load_data():
    events = pd.read_excel(EVENT_FILE)
    epm = pd.read_excel(EPM_FILE)

    if "Season" in events.columns:
        events = events[events["Season"] == "2025-2026"]
    if "Season" in epm.columns:
        epm = epm[epm["Season"] == "2025-2026"]

    return events.merge(
        epm[["playerName", "Offensive EPM", "Defensive EPM", "Total EPM"]],
        on="playerName",
        how="left"
    )

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
        Eredivisie • 2025–26 • Advanced player impact
    </p>
    """,
    unsafe_allow_html=True
)

# =====================================================
# CONTROLS
# =====================================================
c1, c2 = st.columns([3, 1])

with c1:
    search = st.text_input(
        "Search player",
        placeholder="Search player",
        label_visibility="collapsed"
    )

with c2:
    pos_pct = st.toggle("Position percentiles", value=True)

if search:
    df = df[df["playerName"].str.lower().str.contains(search.lower())]

# =====================================================
# TABLE DATA
# =====================================================
table = (
    df[
        [
            "playerName",
            "Team within selected timeframe",
            "Position",

            "Offensive EPM",
            "Defensive EPM",
            "Total EPM",

            "xG",
            "xA",
            "Goals",
            "Assists",
            "Key passes",
            "Shots",
            "Touches in box",

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
        "Touches in box": "BOX",
        "Key passes": "KP",
        "Shots blocked": "BLK",
        "Aerial duels won, %": "AERIAL %",
    })
    .sort_values("EPM", ascending=False)
    .reset_index(drop=True)
)

numeric_cols = table.select_dtypes(include=np.number).columns

# =====================================================
# POSITION-BASED PERCENTILES
# =====================================================
def percentile(series, val):
    return series.rank(pct=True)[series == val].iloc[0]

def green_shade(val, col, pos):
    if pd.isna(val):
        return ""

    if pos_pct:
        group = table[table["POS"] == pos][col]
    else:
        group = table[col]

    pct = percentile(group, val)
    alpha = 0.06 + (pct ** 2) * 0.32

    r, g, b = GREEN_RGB
    return f"background-color: rgba({r},{g},{b},{alpha}); color:{TEXT};"

styler = (
    table.style
    .apply(
        lambda s: [
            green_shade(v, s.name, table.loc[i, "POS"])
            for i, v in enumerate(s)
        ],
        subset=numeric_cols
    )
    .format("{:.1f}", subset=numeric_cols)
)

# =====================================================
# DISPLAY
# =====================================================
st.dataframe(
    styler,
    height=900,
    use_container_width=True,
)

# =====================================================
# FOOTER
# =====================================================
st.markdown(
    """
    <hr style="border-color:#1e293b;">
    <small style="color:#94a3b8;">
        Percentile-based shading • Position-adjusted • One-decimal precision
    </small>
    """,
    unsafe_allow_html=True
)
