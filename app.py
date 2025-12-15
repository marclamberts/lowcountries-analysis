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

        tbody tr td {{
            font-size: 12px;
            color: {TEXT};
        }}

        tbody tr:hover td {{
            background-color: rgba(148,163,184,0.08);
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
# PRECOMPUTE PERCENTILES (SAFE)
# =====================================================
if pos_pct:
    pct_table = (
        table
        .groupby("POS")[numeric_cols]
        .rank(pct=True)
    )
else:
    pct_table = table[numeric_cols].rank(pct=True)

# Safety check (can remove later)
assert table.index.equals(pct_table.index)

# =====================================================
# SUBTLE GREEN SHADING
# =====================================================
def green_shade(pct):
    if pd.isna(pct):
        return ""

    # opacity curve: very subtle
    alpha = 0.06 + (pct ** 2) * 0.32
    r, g, b = GREEN_RGB

    return f"background-color: rgba({r},{g},{b},{alpha}); color:{TEXT};"

styler = (
    table.style
    .apply(
        lambda _: pct_table.applymap(green_shade),
        subset=numeric_cols
    )
    .format("{:.1f}", subset=numeric_cols)
)

# =====================================================
# DISPLAY TABLE (FULL WIDTH)
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
