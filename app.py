import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(layout="wide", page_title="EPM Player Card")

# =====================================================
# STYLE
# =====================================================
st.markdown("""
<style>
body {
    background-color: #0b1220;
    color: white;
}
.metric {
    border-radius: 6px;
    padding: 18px;
    text-align: center;
    font-weight: 900;
    font-size: 26px;
}
.label {
    font-size: 12px;
    opacity: 0.75;
    font-weight: 600;
}
.big {
    font-size: 56px;
}
</style>
""", unsafe_allow_html=True)

# =====================================================
# FILES
# =====================================================
EVENT_FILE = "data/eredivisie_event_metrics_merged_final.xlsx"

EPM_FILES = {
    "24–25": "data/Eredivisie EPM 2024-2025.xlsx",
    "25–26": "data/Eredivisie EPM 2025-2026.xlsx",
}

# =====================================================
# POSITION GROUPS
# =====================================================
ATTACK = ["CF", "ST", "LW", "RW"]
MIDFIELD = ["AMF", "CM", "DMF", "RCMF", "LCMF"]
DEFENSE = ["CB", "LB", "RB", "LCB", "RCB"]

def position_group(pos):
    if not isinstance(pos, str):
        return "Other"
    if any(p in pos for p in ATTACK):
        return "Attackers"
    if any(p in pos for p in MIDFIELD):
        return "Midfielders"
    if any(p in pos for p in DEFENSE):
        return "Defenders"
    return "Other"

def pct_color(p):
    if p >= 90: return "#22c55e"
    if p >= 75: return "#38bdf8"
    if p >= 50: return "#64748b"
    if p >= 25: return "#475569"
    return "#334155"

# =====================================================
# LOAD DATA
# =====================================================
@st.cache_data
def load_events():
    df = pd.read_excel(EVENT_FILE)
    df["PosGroup"] = df["Position"].apply(position_group)
    return df

events = load_events()

# =====================================================
# SIDEBAR
# =====================================================
PLAYER = st.sidebar.selectbox(
    "Player",
    sorted(events["playerName"].unique())
)

ROLE = st.sidebar.text_input("Role", "Advanced Playmaker")

player_row = events[events["playerName"] == PLAYER].iloc[0]

TEAM = player_row["Team within selected timeframe"]
POSITION = player_row["Position"]
AGE = int(player_row["Age"])
POS_GROUP = player_row["PosGroup"]

# =====================================================
# POSITIONAL BENCHMARK
# =====================================================
ref = events[events["PosGroup"] == POS_GROUP].copy()

METRICS = [
    "Goals", "Assists", "Key passes",
    "Tackles", "Interceptions", "Aerial duels won, %",
]

for m in METRICS:
    ref[m + "_pct"] = ref[m].rank(pct=True) * 100

player = ref[ref["playerName"] == PLAYER].iloc[0]

# =====================================================
# LOAD EPM (POSITION FILTERED)
# =====================================================
trend = []

for season, path in EPM_FILES.items():
    df = pd.read_excel(path)
    df = df[df["playerName"].isin(ref["playerName"])]

    for c in ["Offensive EPM", "Defensive EPM", "Total EPM"]:
        df[c + "_pct"] = df[c].rank(pct=True) * 100

    row = df[df["playerName"] == PLAYER]
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
<h1>{PLAYER.upper()}</h1>
<b>{TEAM}</b> • {POSITION}
""", unsafe_allow_html=True)

st.progress(latest["Total"] / 100)
st.markdown(f"**{latest['Total']:.0f}%**")

# =====================================================
# MAIN LAYOUT
# =====================================================
left, right = st.columns([1.35, 1])

# =====================================================
# LEFT COLUMN
# =====================================================
with left:

    # --- BIG TILE + INFO ROW ---
    tile_col, info_col = st.columns([0.9, 1.1])

    with tile_col:
        st.markdown(f"""
        <div class="metric big" style="background:{pct_color(latest['Total'])};">
            {latest['Total']:.0f}%
        </div>
        """, unsafe_allow_html=True)

    with info_col:
        st.markdown(f"""
        <div class="label">POSITION GROUP</div>
        <b>{POS_GROUP}</b><br><br>

        <div class="label">ROLE</div>
        <b>{ROLE}</b><br><br>

        <div class="label">AGE</div>
        <b>{AGE}</b><br><br>

        <div class="label">TEAM</div>
        <b>{TEAM}</b>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # --- SMALL TILES GRID ---
    tiles = [
        ("OFF EPM", latest["Off"]),
        ("DEF EPM", latest["Def"]),
        ("GOALS", player["Goals_pct"]),
        ("ASSISTS", player["Assists_pct"]),
        ("KEY PASSES", player["Key passes_pct"]),
        ("TACKLES", player["Tackles_pct"]),
        ("INTERCEPTIONS", player["Interceptions_pct"]),
        ("AERIAL DUELS", player["Aerial duels won, %_pct"]),
    ]

    cols = st.columns(4)
    for i, (lab, val) in enumerate(tiles):
        with cols[i % 4]:
            st.markdown(
                f"""
                <div class="label">{lab}</div>
                <div class="metric" style="background:{pct_color(val)};">
                    {val:.0f}%
                </div>
                """,
                unsafe_allow_html=True
            )

    st.caption(f"Percentiles vs {POS_GROUP}")

# =====================================================
# RIGHT COLUMN (GRAPHS)
# =====================================================
with right:
    fig, ax = plt.subplots(2, 1, figsize=(6, 7), sharex=True)

    ax[0].plot(trend_df["Season"], trend_df["Total"], lw=3, marker="o")
    ax[0].set_title("WAR PERCENTILE TREND", fontsize=14, fontweight="bold")
    ax[0].set_ylim(0, 100)
    ax[0].grid(alpha=0.25)

    ax[1].plot(trend_df["Season"], trend_df["Off"], "--", label="Offense")
    ax[1].plot(trend_df["Season"], trend_df["Def"], "--", label="Defense")
    ax[1].plot(trend_df["Season"], trend_df["Total"], lw=3, label="Total")
    ax[1].set_title("EPM PERCENTILE TREND", fontsize=14, fontweight="bold")
    ax[1].set_ylim(0, 100)
    ax[1].legend()
    ax[1].grid(alpha=0.25)

    st.pyplot(fig)

# =====================================================
# FOOTER
# =====================================================
st.caption("3-Year Weighted Avg • Position-adjusted percentiles • Eredivisie")
st.caption("Data Source: Opta via StatsBomb • Created by Marc Lambert")