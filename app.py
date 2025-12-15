import streamlit as st
import pandas as pd
import numpy as np

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="Estimated Plus-Minus",
    layout="wide",
)

# =====================================================
# COLORS
# =====================================================
BG = "#0a0f1e"
PANEL = "#0f172a"
TEXT = "#e5e7eb"
MUTED = "#94a3b8"

GREEN_RGB = (34, 197, 94)

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

        tbody tr td {{
            font-size: 12px;
            color: {TEXT};
        }}

        tbody tr:hover td {{
            background-color: rgba(148,163,184,0.05);
        }}

        .league-btn {{
            padding: 6px 16px;
            border-radius: 6px;
            border: 1px solid #1e293b;
            background-color: #020617;
            color: #cbd5f5;
            font-weight: 500;
            cursor: pointer;
        }}

        .league-btn-active {{
            background-color: #1e293b;
            border-color: #38bdf8;
            color: #e5e7eb;
        }}
    </style>
    """,
    unsafe_allow_html=True
)

# =====================================================
# DATA CONFIG
# =====================================================
LEAGUES = {
    "eredivisie": {
        "label": "🇳🇱 Eredivisie",
        "event_file": "data/eredivisie_event_metrics_merged_final.xlsx",
        "epm_file": "data/Eredivisie EPM 2025-2026.xlsx",
        "title": "Eredivisie",
    },
    "belgium": {
        "label": "🇧🇪 Belgium",
        "event_file": "data/belgium_event_metrics_merged_final.xlsx",
        "epm_file": "data/Belgium EPM 2025-2026.xlsx",
        "title": "Belgium Pro League",
    },
}

# =====================================================
# SESSION STATE
# =====================================================
if "league" not in st.session_state:
    st.session_state.league = "eredivisie"

# =====================================================
# LEAGUE SWITCH BUTTONS
# =====================================================
b1, b2, _ = st.columns([1, 1, 6])

with b1:
    if st.button(LEAGUES["eredivisie"]["label"], use_container_width=True):
        st.session_state.league = "eredivisie"

with b2:
    if st.button(LEAGUES["belgium"]["label"], use_container_width=True):
        st.session_state.league = "belgium"

league = LEAGUES[st.session_state.league]

# =====================================================
# LOAD DATA
# =====================================================
@st.cache_data
def load_data(event_file, epm_file):
    events = pd.read_excel(event_file)
    epm = pd.read_excel(epm_file)

    if "Season" in events.columns:
        events = events[events["Season"] == "2025-2026"]

    if "Season" in epm.columns:
        epm = epm[epm["Season"] == "2025-2026"]

    return events.merge(
        epm[["playerName", "Offensive EPM", "Defensive EPM", "Total EPM"]],
        on="playerName",
        how="left"
    )

df = load_data(league["event_file"], league["epm_file"])

# =====================================================
# HEADER
# =====================================================
st.markdown(
    f"""
    <h1 style="margin-bottom:0;font-weight:600;">
        Estimated Plus-Minus
    </h1>
    <p style="color:#94a3b8;margin-top:6px;">
        {league["title"]} • 2025–26 • Advanced player impact
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
# TABLE
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
# PERCENTILES
# =====================================================
if pos_pct:
    pct_table = table.groupby("POS")[numeric_cols].rank(pct=True)
else:
    pct_table = table[numeric_cols].rank(pct=True)

# =====================================================
# SHADING (THRESHOLDED)
# =====================================================
def green_shade(pct):
    if pd.isna(pct) or pct < 0.60:
        return ""

    if pct < 0.80:
        alpha = 0.012
    elif pct < 0.95:
        alpha = 0.025
    else:
        alpha = 0.040

    r, g, b = GREEN_RGB
    return f"background-color: rgba({r},{g},{b},{alpha}); color:{TEXT};"

styler = table.style

for col in numeric_cols:
    styler = styler.applymap(
        green_shade,
        subset=pd.IndexSlice[:, col]
    )

styler = styler.format("{:.1f}", subset=numeric_cols)

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
        Percentile-based shading • Click buttons to switch leagues
    </small>
    """,
    unsafe_allow_html=True
)
