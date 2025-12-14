import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Rectangle
from io import BytesIO

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="Eredivisie EPM",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================================================
# THEME
# =====================================================
BG = "#0b1220"
GRID = "#334155"
TEXT = "white"

st.markdown(
    f"""
    <style>
    .stApp {{
        background-color: {BG};
        color: {TEXT};
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# =====================================================
# COLOR SCALE
# =====================================================
def percentile_color(p):
    if p >= 90: return "#22c55e"
    if p >= 75: return "#38bdf8"
    if p >= 50: return "#64748b"
    if p >= 25: return "#475569"
    return "#1f2937"

# =====================================================
# FILES
# =====================================================
EVENT_FILE = "data/eredivisie_event_metrics_merged_final.xlsx"
EPM_FILES = {
    "22–23": "data/Eredivisie EPM 2022-2023.xlsx",
    "23–24": "data/Eredivisie EPM 2023-2024.xlsx",
    "24–25": "data/Eredivisie EPM 2024-2025.xlsx",
    "25–26": "data/Eredivisie EPM 2025-2026.xlsx",
}

# =====================================================
# SESSION STATE
# =====================================================
if "page" not in st.session_state:
    st.session_state.page = "landing"

if "player" not in st.session_state:
    st.session_state.player = None

# =====================================================
# LOAD DATA
# =====================================================
events = pd.read_excel(EVENT_FILE)

# =====================================================
# POSITION GROUP LOGIC
# =====================================================
def position_group(pos):
    if any(p in pos for p in ["CF", "ST", "RW", "LW"]):
        return "Attackers", ["CF", "ST", "RW", "LW"]
    if any(p in pos for p in ["CB", "RB", "LB", "RCB", "LCB"]):
        return "Defenders", ["CB", "RB", "LB", "RCB", "LCB"]
    return "Midfielders", ["AMF", "CM", "DMF", "RCMF", "LCMF", "AM"]

# =====================================================
# LANDING PAGE (TABLE)
# =====================================================
if st.session_state.page == "landing":

    st.markdown("## Estimated Plus-Minus (EPM)")
    st.markdown(
        "<small>Expected impact based on Eredivisie event-level data</small>",
        unsafe_allow_html=True
    )

    season = st.selectbox("Season", list(EPM_FILES.keys()), index=3)
    epm = pd.read_excel(EPM_FILES[season])

    df = epm.merge(
        events[[
            "playerName", "Position", "Team within selected timeframe",
            "Goals", "Assists", "Key passes"
        ]],
        on="playerName",
        how="left"
    )

    search = st.text_input("Search player")
    if search:
        df = df[df["playerName"].str.contains(search, case=False)]

    df = df.sort_values("Total EPM", ascending=False)

    def epm_color(val):
        if val >= 2: return "background-color:#14532d"
        if val >= 1: return "background-color:#166534"
        if val >= 0: return "background-color:#1f2937"
        if val >= -1: return "background-color:#7f1d1d"
        return "background-color:#450a0a"

    styled = (
        df[[
            "playerName", "Position",
            "Offensive EPM", "Defensive EPM", "Total EPM",
            "Goals", "Assists", "Key passes"
        ]]
        .style
        .applymap(epm_color, subset=["Offensive EPM", "Defensive EPM", "Total EPM"])
        .format(precision=2)
    )

    st.dataframe(styled, use_container_width=True, height=720)

    player = st.selectbox("Open player card", df["playerName"].unique())
    if st.button("View Player"):
        st.session_state.player = player
        st.session_state.page = "player"

# =====================================================
# PLAYER PAGE (CARD)
# =====================================================
if st.session_state.page == "player":

    PLAYER = st.session_state.player
    row = events[events["playerName"] == PLAYER].iloc[0]

    POSITION = row["Position"]
    AGE = int(row["Age"])
    TEAM = row["Team within selected timeframe"]

    GROUP, POOL = position_group(POSITION)

    ref = events[
        events["Position"].astype(str).apply(lambda x: any(p in x for p in POOL))
    ].copy()

    METRICS = [
        "Goals", "Assists", "Key passes",
        "Tackles", "Interceptions", "Aerial duels won, %",
    ]

    for m in METRICS:
        ref[m + "_pct"] = ref[m].rank(pct=True) * 100

    player_row = ref[ref["playerName"] == PLAYER].iloc[0]

    trend = []
    for season, file in EPM_FILES.items():
        df = pd.read_excel(file)
        df = df[df["playerName"].isin(ref["playerName"])].copy()

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

    # ================= FIGURE =================
    fig = plt.figure(figsize=(12, 8))
    fig.patch.set_facecolor(BG)

    # ---------- LEFT ----------
    ax = fig.add_axes([0.03, 0.05, 0.52, 0.9])
    ax.axis("off")

    ax.text(0, 0.96, PLAYER.upper(), fontsize=30, fontweight="bold")
    ax.text(0, 0.92, f"{TEAM} • {POSITION}", fontsize=13, alpha=0.8)

    # WAR BAR
    ax.add_patch(Rectangle((0, 0.88), 0.8, 0.02, color="#1e293b"))
    ax.add_patch(Rectangle(
        (0, 0.88),
        0.8 * latest["Total"] / 100,
        0.02,
        color=percentile_color(latest["Total"])
    ))
    ax.text(0.83, 0.885, f"{latest['Total']:.0f}%", fontsize=12)

    # BIG TILE
    ax.add_patch(Rectangle((0, 0.62), 0.35, 0.18,
                           color=percentile_color(latest["Total"])))
    ax.text(0.175, 0.71, f"{latest['Total']:.0f}%",
            fontsize=44, fontweight="bold", ha="center", va="center")

    info_x = 0.4
    info = [
        ("POSITION GROUP", GROUP),
        ("ROLE", "Advanced Playmaker"),
        ("AGE", AGE),
        ("TEAM", TEAM),
    ]

    for i, (k, v) in enumerate(info):
        ax.text(info_x, 0.75 - i * 0.08, k, fontsize=10, alpha=0.6)
        ax.text(info_x, 0.72 - i * 0.08, v, fontsize=14, fontweight="bold")

    # SMALL TILES
    tiles = [
        ("OFF EPM", latest["Off"]),
        ("DEF EPM", latest["Def"]),
        ("GOALS", player_row["Goals_pct"]),
        ("ASSISTS", player_row["Assists_pct"]),
        ("KEY PASSES", player_row["Key passes_pct"]),
        ("TACKLES", player_row["Tackles_pct"]),
        ("INTERCEPTIONS", player_row["Interceptions_pct"]),
        ("AERIAL DUELS", player_row["Aerial duels won, %_pct"]),
    ]

    x0, y0 = 0, 0.4
    w, h = 0.16, 0.12
    gap = 0.02

    for i, (lab, val) in enumerate(tiles):
        r, c = divmod(i, 4)
        x = x0 + c * (w + gap)
        y = y0 - r * (h + 0.08)

        ax.add_patch(Rectangle((x, y), w, h,
                               color=percentile_color(val)))
        ax.text(x + w/2, y + h/2, f"{val:.0f}%",
                ha="center", va="center",
                fontsize=22, fontweight="bold")
        ax.text(x, y + h + 0.02, lab, fontsize=10, alpha=0.7)

    ax.text(0, 0.02,
            f"Percentiles vs {GROUP}\n3-Year Weighted Avg • Eredivisie",
            fontsize=11, alpha=0.6)

    # ---------- RIGHT GRAPHS ----------
    ax1 = fig.add_axes([0.6, 0.55, 0.36, 0.35])
    ax2 = fig.add_axes([0.6, 0.1, 0.36, 0.35])

    for a in [ax1, ax2]:
        a.set_facecolor(BG)
        a.grid(color=GRID, alpha=0.25)
        a.tick_params(colors="white")
        for s in a.spines.values():
            s.set_color(GRID)

    ax1.plot(trend["Season"], trend["Total"],
             color="white", lw=3, marker="o")
    ax1.set_ylim(0, 100)
    ax1.set_title("WAR PERCENTILE TREND",
                  color="white", fontsize=15, fontweight="bold")

    ax2.plot(trend["Season"], trend["Off"],
             "--", color="#38bdf8", label="Offense")
    ax2.plot(trend["Season"], trend["Def"],
             "--", color="#fb923c", label="Defense")
    ax2.plot(trend["Season"], trend["Total"],
             color="#22c55e", lw=3, label="Total")

    ax2.set_ylim(0, 100)
    ax2.set_title("EPM PERCENTILE TREND",
                  color="white", fontsize=15, fontweight="bold")
    ax2.legend(facecolor=BG, labelcolor="white")

    # EXPORT PNG
    buf = BytesIO()
    fig.savefig(buf, dpi=200, bbox_inches="tight", facecolor=BG)
    buf.seek(0)

    st.pyplot(fig)
    st.download_button(
        "Download PNG",
        data=buf,
        file_name=f"{PLAYER}_EPM_Card.png",
        mime="image/png"
    )

    if st.button("← Back to table"):
        st.session_state.page = "landing"
