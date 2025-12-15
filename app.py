import streamlit as st
import pandas as pd
import numpy as np

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(page_title="Estimated Plus-Minus", layout="wide")

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
        .stApp {{ background-color: {BG}; color: {TEXT}; }}

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
    </style>
    """,
    unsafe_allow_html=True
)

# =====================================================
# DATA LOADER
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

# =====================================================
# RENDER FUNCTION
# =====================================================
def render_league(league_name, event_file, epm_file, key_prefix):
    df = load_data(event_file, epm_file)

    st.markdown(
        f"""
        <h1 style="margin-bottom:0;font-weight:600;">Estimated Plus-Minus</h1>
        <p style="color:#94a3b8;margin-top:6px;">
            {league_name} • 2025–26 • Advanced player impact
        </p>
        """,
        unsafe_allow_html=True
    )

    c1, c2 = st.columns([3, 1])
    with c1:
        search = st.text_input(
            "Search player",
            key=f"search_{key_prefix}",
            label_visibility="collapsed"
        )
    with c2:
        pos_pct = st.toggle(
            "Position percentiles",
            value=True,
            key=f"pospct_{key_prefix}"
        )

    if search:
        df = df[df["playerName"].str.lower().str.contains(search.lower())]

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

    # Percentiles
    if pos_pct:
        pct_table = table.groupby("POS")[numeric_cols].rank(pct=True)
    else:
        pct_table = table[numeric_cols].rank(pct=True)

    # Thresholded subtle shading
    def green_shade(pct):
        if pd.isna(pct) or pct < 0.60:
            return ""
        if pct < 0.80:
            alpha = 0.010
        elif pct < 0.95:
            alpha = 0.020
        else:
            alpha = 0.030
        r, g, b = GREEN_RGB
        return f"background-color: rgba({r},{g},{b},{alpha}); color:{TEXT};"

    styler = table.style.format("{:.1f}", subset=numeric_cols)

    for col in numeric_cols:
        styler = styler.map(
            green_shade,
            subset=pd.IndexSlice[:, col],
            data=pct_table[col]
        )

    st.dataframe(
        styler,
        height=900,
        width="stretch",   # ✅ correct API
    )

# =====================================================
# TABS
# =====================================================
tab_nl, tab_be = st.tabs(["🇳🇱 Eredivisie", "🇧🇪 Belgium"])

with tab_nl:
    render_league(
        "Eredivisie",
        "data/eredivisie_event_metrics_merged_final.xlsx",
        "data/Eredivisie EPM 2025-2026.xlsx",
        "nl",
    )

with tab_be:
    render_league(
        "Belgium Pro League",
        "data/belgium_event_metrics_merged_final.xlsx",
        "data/Belgium EPM 2025-2026.xlsx",
        "be",
    )

# =====================================================
# FOOTER
# =====================================================
st.markdown(
    """
    <hr style="border-color:#1e293b;">
    <small style="color:#94a3b8;">
        Tabs switch leagues • No deprecated APIs • Warning-free
    </small>
    """,
    unsafe_allow_html=True
)
