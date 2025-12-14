import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(layout="wide", page_title="EPM Player Card")

BG = "#0b1220"
GRID = "#1f2937"
WHITE = "#ffffff"

# =====================================================
# GLOBAL STYLE
# =====================================================
st.markdown(f"""
<style>
body {{
    background-color: {BG};
    color: white;
}}

.metric {{
    border-radius: 6px;
    padding: 20px;
    text-align: center;
    font-weight: 900;
    font-size: 28px;
}}

.big {{
    font-size: 58px;
}}

.label {{
    font-size: 12px;
    opacity: 0.65;
    font-weight: 600;
    letter-spacing: 0.05em;
}}

.info {{
    font-size: 20px;
    font-weight: 700;
    margin-bottom: 10px;
}}

hr {{
    border: none;
    height: 1px;
    background-color: {GRID};
    margin: 18px 0;
}}
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

def pos_group(pos):
    if not isinstance(pos, str): return "Other"
    if any(p in pos for p in ATTACK): return "Attackers"
    if any(p in pos for p in MIDFIELD): return "Midfielders"
    if any(p in pos for p in DEFENSE): return "Defenders"
    return "Other"

def color(p):
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
    df["PosGroup"] = df["Position"].apply(pos_group)
    return df

events = load_events()

# =====================================================
# SIDEBAR
# =====================================================
PLAYER = st.sidebar.selectbox("Player", sorted(events["playerName"].unique()))
ROLE = st.sidebar.text_input("Role", "Advanced Playmaker")

row = events[events["playerName"] == PLAYER].iloc[0]
TEAM = row["Team within selected timeframe"]
POSITION = row["Position"]
AGE = int(row["Age"])
GROUP = row["PosGroup"]

ref = events[events["PosGroup"] == GROUP].copy()

METRICS = [
    "Goals", "Assists", "Key passes",
    "Tackles", "Interceptions", "Aerial duels won, %",
]

for m in METRICS:
    ref[m + "_pct"] = ref[m].rank(pct=True) * 100

player = ref[ref["playerName"] == PLAYER].iloc[0]

# =====================================================
# LOAD EPM
# =====================================================
trend = []

for season, path in EPM_FILES.items():
    df = pd.read_excel(path)
    df = df[df["playerName"].isin(ref["playerName"])]

    for c in ["Offensive EPM", "Defensive EPM", "Total EPM"]:
        df[c + "_pct"] = df[c].rank(pct=True) * 100

    r = df[df["playerName"] == PLAYER]
    if not r.empty:
        trend.append({
            "Season": season,
            "Off": r["Offensive EPM_pct"].values[0],
            "Def": r["Defensive EPM_pct"].values[0],
            "Total": r["Total EPM_pct"].values[0],
        })

trend = pd.DataFrame(trend)
latest = trend.iloc[-1]

# =====================================================
# HEADER
# =====================================================
st.markdown(f"""
<h1 style="margin-bottom:0">{PLAYER.upper()}</h1>
<div style="opacity:.8">{TEAM} • {POSITION}</div>
""", unsafe_allow_html=True)

st.progress(latest["Total"] / 100)
st.markdown(f"**{latest['Total']:.0f}%**")

# =====================================================
# MAIN LAYOUT
# =====================================================
left, right = st.columns([1.4, 1])

# =====================================================
# LEFT SIDE
# =====================================================
with left:
    c1, c2 = st.columns([0.9, 1.1])

    with c1:
        st.markdown(f"""
        <div class="metric big" style="background:{color(latest['Total'])}">
            {latest['Total']:.0f}%
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
        <div class="label">POSITION GROUP</div>
        <div class="info">{GROUP}</div>

        <div class="label">ROLE</div>
        <div class="info">{ROLE}</div>

        <div class="label">AGE</div>
        <div class="info">{AGE}</div>

        <div class="label">TEAM</div>
        <div class="info">{TEAM}</div>
        """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

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
            st.markdown(f"""
            <div class="label">{lab}</div>
            <div class="metric" style="background:{color(val)}">
                {val:.0f}%
            </div>
            """, unsafe_allow_html=True)

    st.caption(f"Percentiles vs {GROUP} • 3-Year Weighted Avg")

# =====================================================
# RIGHT SIDE — GRAPHS
# =====================================================
with right:
    fig, ax = plt.subplots(2, 1, figsize=(6, 7), sharex=True)
    fig.patch.set_facecolor(BG)

    for a in ax:
        a.set_facecolor(BG)
        a.tick_params(colors="white")
        for s in a.spines.values():
            s.set_color(GRID)
        a.grid(color=GRID, alpha=0.3)

    ax[0].plot(trend["Season"], trend["Total"], lw=3, marker="o", color="white")
    ax[0].set_title("WAR PERCENTILE TREND", color="white", fontsize=15, fontweight="bold")
    ax[0].set_ylim(0, 100)

    ax[1].plot(trend["Season"], trend["Off"], "--", color="#38bdf8", label="Offense")
    ax[1].plot(trend["Season"], trend["Def"], "--", color="#fb923c", label="Defense")
    ax[1].plot(trend["Season"], trend["Total"], lw=3, color="#22c55e", label="Total")
    ax[1].set_title("EPM PERCENTILE TREND", color="white", fontsize=15, fontweight="bold")
    ax[1].set_ylim(0, 100)
    ax[1].legend(facecolor=BG, edgecolor=GRID, labelcolor="white")

    st.pyplot(fig)

st.caption("EPM model • Event-based • Eredivisie")
