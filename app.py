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
GRID = "#1e293b"
TEXT = "#e5e7eb"
MUTED = "#94a3b8"

GREEN_LOW = "#052e16"
GREEN_MID = "#166534"
GREEN_HIGH = "#22c55e"

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
            color: {TEXT};
            font-size: 12px;
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
# LOAD DATA (ONLY 2025–26)
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

# =====================================================
# ROUNDING
# =====================================================
round_cols = ["OFF", "DEF", "EPM", "xG", "xA", "AERIAL %"]
for c in round_cols:
    if c in table.columns:
        table[c] = table[c].round(2)

# =====================================================
# PERCENTILE COLORING
# =====================================================
numeric_cols = table.select_dtypes(include=np.number).columns

def green_scale(val, col):
    if pd.isna(val):
        return ""

    series = table[col]
    pct = (series.rank(pct=True).loc[series == val].iloc[0])

    if pct > 0.85:
        color = GREEN_HIGH
    elif pct > 0.65:
        color = GREEN_MID
    else:
        color = GREEN_LOW

    return f"background-color: {color}; color: #ecfdf5;"

styler = (
    table.style
    .apply(
        lambda s: [green_scale(v, s.name) for v in s],
        subset=numeric_cols
    )
)

# =====================================================
# FULL-WIDTH TABLE
# =====================================================
st.dataframe(
    styler,
    height=860,
    use_container_width=True,
)

# =====================================================
# FOOTER
# =====================================================
st.markdown(
    """
    <hr style="border-color:#1e293b;">
    <small style="color:#94a3b8;">
        Green-shaded values represent relative performance (percentile-based)
    </small>
    """,
    unsafe_allow_html=True
)
