import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO

# =====================================================
# APP CONFIG
# =====================================================
st.set_page_config(page_title="EPM Player Card", layout="wide")

# =====================================================
# COLORS
# =====================================================
BG = "#0b1220"
GRID = "#334155"
TEXT = "#ffffff"
MUTED = "#94a3b8"

def percentile_color(p):
    if p >= 90: return "#22c55e"
    if p >= 75: return "#38bdf8"
    if p >= 50: return "#e5e7eb"
    if p >= 25: return "#94a3b8"
    return "#64748b"

st.markdown(
    f"""
    <style>
        .stApp {{
            background-color: {BG};
            color: {TEXT};
        }}
        h1, h2, h3, h4 {{
            color: {TEXT};
        }}
        small {{
            color: {MUTED};
        }}
    </style>
    """,
    unsafe_allow_html=True
)

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
# LOAD DATA
# =====================================================
events = pd.read_excel(EVENT_METRICS_FILE)

# =====================================================
# SIDEBAR FILTERS
# =====================================================
st.sidebar.header("Filters")

PLAYER = st.sidebar.selectbox(
    "Player",
    sorted(events["playerName"].unique())
)

SEASONS = st.sidebar.multiselect(
    "Seasons",
    list(EPM_FILES.keys()),
    default=list(EPM_FILES.keys())
)

# =====================================================
# PLAYER INFO
# =====================================================
row = events[events["playerName"] == PLAYER].iloc[0]
POSITION = row["Position"]
AGE = int(row["Age"])
TEAM = row["Team within selected timeframe"]

# =====================================================
# POSITION GROUP
# =====================================================
def position_group(pos):
    if any(p in pos for p in ["CF", "ST", "RW", "LW"]):
        return "Attackers", ["CF", "ST", "RW", "LW"]
    if any(p in pos for p in ["CB", "RB", "LB", "RCB", "LCB"]):
        return "Defenders", ["CB", "RB", "LB", "RCB", "LCB"]
    return "Midfielders", ["AMF", "CM", "DMF", "RCMF", "LCMF", "AM"]

GROUP, POOL = position_group(POSITION)

ref_events = events[
    events["Position"].astype(str).apply(lambda x: any(p in x for p in POOL))
].copy()

# =====================================================
# EVENT METRICS (POSITION PEERS)
# =====================================================
METRICS = [
    "Goals", "Assists", "Key passes",
    "Tackles", "Interceptions", "Aerial duels won, %",
]

for m in METRICS:
    ref_events[m + "_pct"] = ref_events[m].rank(pct=True) * 100

player = ref_events[ref_events["playerName"] == PLAYER].iloc[0]

# =====================================================
# EPM TRENDS
# =====================================================
trend = []
position_players = set(ref_events["playerName"])

for season in SEASONS:
    df = pd.read_excel(EPM_FILES[season])
    df = df[df["playerName"].isin(position_players)].copy()

    for c in ["Offensive EPM", "Defensive EPM", "Total EPM"]:
        df[c + "_pct"] = df[c].rank(pct=True) * 100

    p = df[df["playerName"] == PLAYER]
    if not p.empty:
        trend.append({
            "Season": season,
            "Off": p["Offensive EPM_pct"].values[0],
            "Def": p["Defensive EPM_pct"].values[0],
            "Total": p["Total EPM_pct"].values[0],
        })

trend = pd.DataFrame(trend)
latest = trend.iloc[-1]

# =====================================================
# LAYOUT
# =====================================================
left, right = st.columns([1.35, 1])

# =====================================================
# LEFT PANEL
# =====================================================
with left:
    st.markdown(f"## {PLAYER.upper()}")
    st.markdown(f"<small>{TEAM} • {POSITION}</small>", unsafe_allow_html=True)

    # WAR BAR
    st.markdown(
        f"""
        <div style="background:{GRID};height:8px;border-radius:4px;">
            <div style="width:{latest['Total']}%;
                        background:{percentile_color(latest['Total'])};
                        height:8px;border-radius:4px;"></div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # BIG WAR + INFO
    c1, c2 = st.columns([0.9, 1.1])

    with c1:
        st.markdown(
            f"""
            <div style="font-size:64px;font-weight:800;line-height:1;">
                {latest['Total']:.0f}%
            </div>
            <small>WAR Percentile</small>
            """,
            unsafe_allow_html=True
        )

    with c2:
        st.markdown(
            f"""
            <small>POSITION GROUP</small><br>
            <b>{GROUP}</b><br><br>

            <small>AGE</small><br>
            <b>{AGE}</b><br><br>

            <small>TEAM</small><br>
            <b>{TEAM}</b>
            """,
            unsafe_allow_html=True
        )

    st.markdown("---")

    # SMALL TILES (TEXT ONLY)
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
    for i, (label, val) in enumerate(tiles):
        with cols[i % 4]:
            st.markdown(
                f"""
                <div style="font-size:26px;font-weight:700;">
                    {val:.0f}%
                </div>
                <div style="height:3px;width:30px;
                            background:{percentile_color(val)};
                            margin:6px 0;"></div>
                <small>{label}</small>
                """,
                unsafe_allow_html=True
            )

    st.markdown(
        f"""
        <small>
        Percentiles vs {GROUP}<br>
        Eredivisie • 3-Year Weighted Avg
        </small>
        """,
        unsafe_allow_html=True
    )

# =====================================================
# RIGHT PANEL — GRAPHS + EXPORT
# =====================================================
with right:
    fig, ax = plt.subplots(2, 1, figsize=(6, 7), sharex=True)
    fig.patch.set_facecolor(BG)

    for a in ax:
        a.set_facecolor(BG)
        a.tick_params(colors="white")
        for s in a.spines.values():
            s.set_color(GRID)
        a.grid(color=GRID, alpha=0.25)

    ax[0].plot(trend["Season"], trend["Total"], lw=3, marker="o", color="white")
    ax[0].set_ylim(0, 100)
    ax[0].set_title("WAR PERCENTILE TREND", color="white", fontweight="bold")

    ax[1].plot(trend["Season"], trend["Off"], "--", color="#38bdf8", label="Offense")
    ax[1].plot(trend["Season"], trend["Def"], "--", color="#fb923c", label="Defense")
    ax[1].plot(trend["Season"], trend["Total"], lw=3, color="#22c55e", label="Total")
    ax[1].set_ylim(0, 100)
    ax[1].set_title("EPM PERCENTILE TREND", color="white", fontweight="bold")
    ax[1].legend(facecolor=BG, edgecolor=GRID, labelcolor="white")

    st.pyplot(fig)

    # EXPORT PNG
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=200,
                bbox_inches="tight", facecolor=BG)
    buf.seek(0)

    st.download_button(
        "📥 Download PNG",
        data=buf,
        file_name=f"{PLAYER.replace(' ', '_')}_EPM_Card.png",
        mime="image/png"
    )
