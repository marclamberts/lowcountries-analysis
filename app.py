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

# RGBA GREEN (DARK, SUBTLE)
GREEN_RGB = (34, 197, 94)  # tailwind green-500

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
# NUMERIC COLUMNS
# =====================================================
numeric_cols = table.select_dtypes(include=np.number).columns

# =====================================================
# SUBTLE PERCENTILE SHADING (RGBA)
# =====================================================
def green_shade(val, col):
    if pd.isna(val):
        return ""

    s = table[col]
    pct = s.rank(pct=True)[s == val].iloc[0]

    # opacity range: very subtle → slightly visible
    alpha = 0.08 + (pct ** 2) * 0.35

    r, g, b = GREEN_RGB
    return (
        f"background-color: rgba({r},{g},{b},{alpha});"
        f"color: {TEXT};"
    )

styler = (
    table.style
    .apply(
        lambda s: [green_shade(v, s.name) for v in s],
        subset=numeric_cols
    )
    .format("{:.1f}", subset=numeric_cols)  # 🔑 ONE DECIMAL EVERYWHERE
)

# =====================================================
# FULL-WIDTH TABLE
# =====================================================
st.dataframe(
    styler,
    height=880,
    use_container_width=True,
)

# =====================================================
# FOOTER
# =====================================================
st.markdown(
    """
    <hr style="border-color:#1e293b;">
    <small style="color:#94a3b8;">
        Subtle green shading reflects percentile performance • One decimal precision
    </small>
    """,
    unsafe_allow_html=True
)
