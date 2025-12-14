import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.offsetbox import OffsetImage, AnnotationBbox

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="EPM Player Profiles",
    layout="wide",
)

# =====================================================
# STYLE (DunksAndThrees inspired)
# =====================================================
st.markdown("""
<style>
body {
    background-color: #0b1220;
    color: white;
}
h1, h2, h3 {
    font-family: Inter, sans-serif;
}
</style>
""", unsafe_allow_html=True)

# =====================================================
# FILES
# =====================================================
EVENT_METRICS_FILE = "data/eredivisie_event_metrics_merged_final.xlsx"

EPM_FILES = {
    "22–23": "data/Eredivisie EPM 2022-2023.xlsx",
    "23–24": "data/Eredivisie EPM 2023-2024.xlsx",
    "24–25": "data/Eredivisie EPM 2024-2025.xlsx",
    "25–26": "data/Eredivisie EPM 2025-2026.xlsx",
}

# =====================================================
# HELPERS
# =====================================================
ATTACK = ["CF", "ST", "LW", "RW", "SS"]
MIDFIELD = ["AMF", "CM", "DMF", "RCMF", "LCMF"]
DEFENSE = ["CB", "LB", "RB", "LCB", "RCB", "LWB", "RWB"]

def detect_position_group(pos):
    if isinstance(pos, str):
        if any(p in pos for p in ATTACK):
            return "Attackers"
        if any(p in pos for p in MIDFIELD):
            return "Midfielders"
        if any(p in pos for p in DEFENSE):
            return "Defenders"
    return "Other"

def percentile_color(p):
    if p >= 90: return "#22c55e"
    if p >= 75: return "#38bdf8"
    if p >= 50: return "#64748b"
    if p >= 25: return "#475569"
    return "#1f2937"

# =====================================================
# LOAD DATA
# =====================================================
@st.cache_data
def load_events():
    return pd.read_excel(EVENT_METRICS_FILE)

events = load_events()
events["PosGroup"] = events["Position"].apply(detect_position_group)

# =====================================================
# SIDEBAR (LIKE DUNKSANDTHREES)
# =====================================================
st.sidebar.title("EPM Explorer")

player = st.sidebar.selectbox(
    "Select player",
    sorted(events["playerName"].unique())
)

role = st.sidebar.text_input("Role", "Advanced Playmaker")

player_row = events[events["playerName"] == player].iloc[0]

team = player_row["Team within selected timeframe"]
age = int(player_row["Age"])
position = player_row["Position"]
pos_group = player_row["PosGroup"]

# =====================================================
# POSITIONAL REFERENCE GROUP
# =====================================================
ref_events = events[events["PosGroup"] == pos_group].copy()

METRICS = [
    "Goals", "Assists", "Key passes",
    "Tackles", "Interceptions", "Aerial duels won, %",
]

for m in METRICS:
    ref_events[m + "_pct"] = ref_events[m].rank(pct=True) * 100

player_event = ref_events[ref_events["playerName"] == player].iloc[0]

# =====================================================
# LOAD EPM (POSITION FILTERED)
# =====================================================
trend = []

for season, path in EPM_FILES.items():
    df = pd.read_excel(path)
    df = df[df["playerName"].isin(ref_events["playerName"])]

    for c in ["Offensive EPM", "Defensive EPM", "Total EPM"]:
        df[c + "_pct"] = df[c].rank(pct=True) * 100

    row = df[df["playerName"] == player]
    if not row.empty:
        trend.append({
            "Season": season,
            "Off": row["Offensive EPM_pct"].values[0],
            "Def": row["Defensive EPM_pct"].values[0],
            "Total": row["Total EPM_pct"].values[0],
        })

trend_df = pd.DataFrame(trend)
latest = trend_df.iloc[-1]

# =====================================================
# HEADER
# =====================================================
st.markdown(f"""
<h1>{player}</h1>
<b>{team}</b> • {position} • Age {age}<br>
<small>{pos_group} percentile ranks</small>
""", unsafe_allow_html=True)

# WAR BAR
st.progress(latest["Total"] / 100)
st.caption(f"Projected WAR percentile: **{latest['Total']:.0f}%**")

st.divider()

# =====================================================
# MAIN LAYOUT
# =====================================================
col_left, col_right = st.columns([1.3, 1])

# =====================================================
# LEFT – METRIC TILES
# =====================================================
with col_left:
    st.subheader("Player Impact Profile")

    tiles = [
        ("Offensive EPM", latest["Off"]),
        ("Defensive EPM", latest["Def"]),
        ("Goals", player_event["Goals_pct"]),
        ("Assists", player_event["Assists_pct"]),
        ("Key Passes", player_event["Key passes_pct"]),
        ("Tackles", player_event["Tackles_pct"]),
        ("Interceptions", player_event["Interceptions_pct"]),
        ("Aerial Duels", player_event["Aerial duels won, %_pct"]),
    ]

    cols = st.columns(4)
    for i, (label, val) in enumerate(tiles):
        with cols[i % 4]:
            st.markdown(
                f"""
                <div style="
                    background:{percentile_color(val)};
                    padding:12px;
                    border-radius:6px;
                    text-align:center;">
                <div style="font-size:22px;font-weight:800;">{val:.0f}%</div>
                <div style="font-size:11px;opacity:0.85;">{label}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

# =====================================================
# RIGHT – GRAPHS
# =====================================================
with col_right:
    st.subheader("Trends")

    fig, ax = plt.subplots(2, 1, figsize=(5, 6), sharex=True)

    ax[0].plot(trend_df["Season"], trend_df["Total"], marker="o", lw=3)
    ax[0].set_title("WAR Percentile")
    ax[0].set_ylim(0, 100)
    ax[0].grid(alpha=0.25)

    ax[1].plot(trend_df["Season"], trend_df["Off"], "--", label="Off")
    ax[1].plot(trend_df["Season"], trend_df["Def"], "--", label="Def")
    ax[1].plot(trend_df["Season"], trend_df["Total"], lw=3, label="Total")
    ax[1].set_title("EPM Percentiles")
    ax[1].set_ylim(0, 100)
    ax[1].legend()
    ax[1].grid(alpha=0.25)

    st.pyplot(fig)

# =====================================================
# FOOTER
# =====================================================
st.caption(
    "Estimated Plus-Minus (EPM) • Position-adjusted percentiles • Eredivisie"
)
