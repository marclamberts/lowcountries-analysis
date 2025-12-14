import streamlit as st
import pandas as pd

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="Eredivisie Estimated Plus-Minus",
    layout="wide"
)

# =====================================================
# THEME
# =====================================================
BG = "#0f1117"
GRID = "#2a2f3a"
TEXT = "#e5e7eb"

st.markdown(
    f"""
    <style>
    .stApp {{
        background-color: {BG};
        color: {TEXT};
    }}

    /* Table */
    thead tr th {{
        background-color: {BG} !important;
        color: {TEXT} !important;
        font-size: 12px;
    }}
    tbody tr td {{
        font-size: 12px;
        padding: 6px;
    }}

    /* Inputs */
    div[data-baseweb="input"] > div {{
        background-color: #111827;
        border-radius: 6px;
        height: 36px;
    }}

    div[data-baseweb="select"] > div {{
        background-color: #111827;
        border-radius: 6px;
        height: 36px;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# =====================================================
# FILES
# =====================================================
EVENT_FILE = "data/eredivisie_event_metrics_merged_final.xlsx"

EPM_FILES = {
    "2022–23": "data/Eredivisie EPM 2022-2023.xlsx",
    "2023–24": "data/Eredivisie EPM 2023-2024.xlsx",
    "2024–25": "data/Eredivisie EPM 2024-2025.xlsx",
    "2025–26": "data/Eredivisie EPM 2025-2026.xlsx",
}

# =====================================================
# COLOR FUNCTIONS
# =====================================================
def epm_bg(val):
    if val >= 2.5: return "background-color:#14532d"
    if val >= 1.5: return "background-color:#166534"
    if val >= 0.5: return "background-color:#1f2937"
    if val >= -0.5: return "background-color:#374151"
    if val >= -1.5: return "background-color:#7f1d1d"
    return "background-color:#450a0a"

def neutral_bg(_):
    return "background-color:#111827"

# =====================================================
# HEADER
# =====================================================
st.markdown("## Estimated Plus-Minus (EPM)")
st.markdown(
    "<small>Expected impact using event-level Eredivisie data</small>",
    unsafe_allow_html=True
)

# =====================================================
# CONTROLS (RIGHT-ALIGNED)
# =====================================================
ctrl_l, ctrl_r = st.columns([5, 2])

with ctrl_r:
    c1, c2 = st.columns([1, 1.4])

    with c1:
        season = st.selectbox(
            "Season",
            list(EPM_FILES.keys()),
            index=3,
            label_visibility="collapsed"
        )

    with c2:
        search = st.text_input(
            "🔍",
            placeholder="Search player",
            label_visibility="collapsed"
        )

# =====================================================
# LOAD DATA
# =====================================================
epm = pd.read_excel(EPM_FILES[season])
events = pd.read_excel(EVENT_FILE)

df = epm.merge(
    events[
        [
            "playerName",
            "Position",
            "Team within selected timeframe",
            "Goals",
            "Assists",
            "Key passes"
        ]
    ],
    on="playerName",
    how="left"
)

# =====================================================
# FILTER
# =====================================================
if search:
    df = df[df["playerName"].str.contains(search, case=False, na=False)]

df = df.sort_values("Total EPM", ascending=False).reset_index(drop=True)

# =====================================================
# TABLE
# =====================================================
table = df[
    [
        "playerName",
        "Team within selected timeframe",
        "Position",
        "Offensive EPM",
        "Defensive EPM",
        "Total EPM",
        "Goals",
        "Assists",
        "Key passes",
    ]
].copy()

table.columns = [
    "PLAYER",
    "TEAM",
    "POS",
    "OFF",
    "DEF",
    "EPM",
    "G",
    "A",
    "KP",
]

styled = (
    table.style
    .applymap(epm_bg, subset=["OFF", "DEF", "EPM"])
    .applymap(neutral_bg, subset=["PLAYER", "TEAM", "POS", "G", "A", "KP"])
    .format({
        "OFF": "{:+.2f}",
        "DEF": "{:+.2f}",
        "EPM": "{:+.2f}",
        "G": "{:.0f}",
        "A": "{:.0f}",
        "KP": "{:.0f}",
    })
    .set_properties(**{
        "color": TEXT,
        "border": f"1px solid {GRID}",
        "text-align": "center",
    })
    .set_table_styles([
        {"selector": "th", "props": [("border", f"1px solid {GRID}")]}
    ])
)

st.dataframe(
    styled,
    use_container_width=True,
    height=760
)

# =====================================================
# FOOTER
# =====================================================
st.markdown(
    """
    <small>
    Expected Plus-Minus • Eredivisie  
    Modeled from event-level data
    </small>
    """,
    unsafe_allow_html=True
)
