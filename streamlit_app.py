"""
IPL-Crunch-26 — Streamlit dashboard.

Run locally:
    streamlit run streamlit_app.py

Deploy:
    Push to GitHub, then connect the repo on https://share.streamlit.io
    (Streamlit Community Cloud).
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="IPL-Crunch-26",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="expanded",
)

ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"

MATCH_COLS = [
    "match_id", "date", "season", "event", "venue", "city",
    "team1", "team2", "toss_winner", "toss_decision",
    "winner", "win_by_runs", "win_by_wickets", "player_of_match",
]

NOT_CREDITED_DISMISSALS = {
    "run out", "retired hurt", "retired out", "obstructing the field",
}


# ---------------------------------------------------------------------------
# Data loading (cached)
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner="Loading IPL ball-by-ball data ...")
def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    csvs = sorted(DATA_DIR.glob("*.csv"))
    if not csvs:
        st.error(f"No CSV found in `{DATA_DIR}`. Add the IPL CSV and reload.")
        st.stop()
    df = pd.read_csv(csvs[0], low_memory=False)
    cols = [c for c in MATCH_COLS if c in df.columns]
    matches = df[cols].drop_duplicates(subset="match_id").reset_index(drop=True)
    matches["date"] = pd.to_datetime(matches["date"], errors="coerce")
    return df, matches


df, matches = load_data()

# ---------------------------------------------------------------------------
# Sidebar — filters
# ---------------------------------------------------------------------------
st.sidebar.header("🎛 Filters")

seasons_sorted = sorted(matches["season"].dropna().unique().tolist())
selected_seasons = st.sidebar.multiselect(
    "Seasons",
    options=seasons_sorted,
    default=seasons_sorted,
    help="Filter every chart by season.",
)

teams_all = sorted(set(matches["team1"].dropna()) | set(matches["team2"].dropna()))
selected_teams = st.sidebar.multiselect(
    "Teams (optional)",
    options=teams_all,
    default=[],
    help="If set, only matches where these teams played are kept.",
)

st.sidebar.divider()
st.sidebar.markdown(
    "**Tip:** clear all team filters to see league-wide stats. "
    "Charts and metrics react to filters in real time."
)

# Apply filters
m_view = matches[matches["season"].isin(selected_seasons)] if selected_seasons else matches
if selected_teams:
    mask = m_view["team1"].isin(selected_teams) | m_view["team2"].isin(selected_teams)
    m_view = m_view[mask]

df_view = df[df["match_id"].isin(m_view["match_id"])]


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title("🏏 IPL-Crunch-26")
st.caption(
    "Interactive analysis of an IPL ball-by-ball dataset. "
    "Filter on the left, explore on the right."
)

# Metric strip
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Matches", f"{len(m_view):,}")
c2.metric("Seasons", f"{m_view['season'].nunique()}")
c3.metric("Venues", f"{m_view['venue'].nunique()}")
c4.metric("Balls bowled", f"{len(df_view):,}")
c5.metric(
    "Total runs",
    f"{int(df_view['runs_total'].sum()):,}" if "runs_total" in df_view else "—",
)

st.divider()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def empty_guard(condition: bool, message: str = "No data after applied filters.") -> bool:
    if condition:
        st.info(message)
        return True
    return False


# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab_toss, tab_team, tab_player, tab_trends, tab_data = st.tabs(
    ["🎲 Toss", "🏆 Teams", "🌟 Players", "📅 Trends", "🔎 Data"]
)


# ---------------- Toss tab ----------------
with tab_toss:
    st.subheader("Toss impact on the match")
    decided = m_view.dropna(subset=["toss_winner", "winner"])
    if not empty_guard(decided.empty):
        won = (decided["toss_winner"] == decided["winner"]).sum()
        lost = (decided["toss_winner"] != decided["winner"]).sum()
        pct = won / len(decided) * 100

        col_a, col_b = st.columns([1, 1])
        with col_a:
            st.metric("Toss winner won the match", f"{won}", f"{pct:.1f}%")
            st.metric("Toss winner lost the match", f"{lost}")
            field_pct = m_view["toss_decision"].eq("field").mean() * 100
            st.metric("Chose to field first", f"{field_pct:.1f}%")
        with col_b:
            fig, ax = plt.subplots(figsize=(6, 4))
            ax.bar(["Toss won → match won", "Toss won → match lost"],
                   [won, lost], color=["#2a9d8f", "#e76f51"])
            ax.set_ylabel("Matches")
            ax.set_title("Toss outcome vs match outcome")
            for i, v in enumerate([won, lost]):
                ax.text(i, v, str(v), ha="center", va="bottom")
            st.pyplot(fig, clear_figure=True)

        st.subheader("Bat vs Field after winning the toss")
        decision = m_view["toss_decision"].value_counts()
        fig, ax = plt.subplots(figsize=(5, 5))
        ax.pie(decision, labels=decision.index, autopct="%1.1f%%",
               colors=["#264653", "#f4a261"], startangle=90)
        ax.set_title("Toss decision distribution")
        st.pyplot(fig, clear_figure=True)


# ---------------- Teams tab ----------------
with tab_team:
    st.subheader("Top franchises by match wins")
    top_n = st.slider("How many teams to show", 3, 10, 5, key="team_n")
    wins = m_view["winner"].dropna().value_counts().head(top_n)
    if not empty_guard(wins.empty):
        fig, ax = plt.subplots(figsize=(9, 0.5 * top_n + 1.5))
        ax.barh(wins.index[::-1], wins.values[::-1], color="#1d3557")
        ax.set_xlabel("Wins")
        ax.set_title(f"Top {top_n} teams")
        for i, v in enumerate(wins.values[::-1]):
            ax.text(v, i, f" {v}", va="center")
        st.pyplot(fig, clear_figure=True)

        st.subheader("Win-loss breakdown for selected teams")
        teams_for_breakdown = selected_teams or wins.index.tolist()
        rows = []
        for team in teams_for_breakdown:
            played = m_view[(m_view["team1"] == team) | (m_view["team2"] == team)]
            won = (played["winner"] == team).sum()
            total = len(played)
            rows.append({
                "Team": team,
                "Played": total,
                "Won": int(won),
                "Lost / NR": int(total - won),
                "Win %": round(won / total * 100, 1) if total else 0.0,
            })
        st.dataframe(pd.DataFrame(rows).sort_values("Win %", ascending=False),
                     use_container_width=True, hide_index=True)


# ---------------- Players tab ----------------
with tab_player:
    pom_col, run_col, wkt_col = st.tabs(["🏅 Player of the Match", "🏏 Run scorers", "🎯 Wicket takers"])

    with pom_col:
        st.subheader("Most Player of the Match awards")
        n = st.slider("Top N", 5, 20, 10, key="pom_n")
        pom = m_view["player_of_match"].dropna().value_counts().head(n)
        if not empty_guard(pom.empty):
            fig, ax = plt.subplots(figsize=(9, 0.4 * n + 1.5))
            ax.barh(pom.index[::-1], pom.values[::-1], color="#e9c46a")
            ax.set_xlabel("Awards")
            for i, v in enumerate(pom.values[::-1]):
                ax.text(v, i, f" {v}", va="center")
            st.pyplot(fig, clear_figure=True)

    with run_col:
        st.subheader("Top run scorers")
        n = st.slider("Top N", 5, 25, 10, key="runs_n")
        runs = (df_view.groupby("batter")["runs_batter"].sum()
                .sort_values(ascending=False).head(n))
        if not empty_guard(runs.empty):
            fig, ax = plt.subplots(figsize=(9, 0.4 * n + 1.5))
            ax.barh(runs.index[::-1], runs.values[::-1], color="#2a9d8f")
            ax.set_xlabel("Runs")
            for i, v in enumerate(runs.values[::-1]):
                ax.text(v, i, f" {int(v)}", va="center")
            st.pyplot(fig, clear_figure=True)

    with wkt_col:
        st.subheader("Top wicket takers")
        st.caption("Run-outs and other dismissals not credited to a bowler are excluded.")
        n = st.slider("Top N", 5, 25, 10, key="wkts_n")
        bowler_wkts = df_view.dropna(subset=["wicket_kind"])
        bowler_wkts = bowler_wkts[
            ~bowler_wkts["wicket_kind"].str.lower().isin(NOT_CREDITED_DISMISSALS)
        ]
        wkts = bowler_wkts.groupby("bowler").size().sort_values(ascending=False).head(n)
        if not empty_guard(wkts.empty):
            fig, ax = plt.subplots(figsize=(9, 0.4 * n + 1.5))
            ax.barh(wkts.index[::-1], wkts.values[::-1], color="#e76f51")
            ax.set_xlabel("Wickets")
            for i, v in enumerate(wkts.values[::-1]):
                ax.text(v, i, f" {int(v)}", va="center")
            st.pyplot(fig, clear_figure=True)


# ---------------- Trends tab ----------------
with tab_trends:
    st.subheader("Matches per season")
    per_season = m_view.groupby("season").size()
    if not empty_guard(per_season.empty):
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.bar(per_season.index.astype(str), per_season.values, color="#457b9d")
        ax.set_xlabel("Season")
        ax.set_ylabel("Matches")
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
        st.pyplot(fig, clear_figure=True)

    st.subheader("Top venues")
    n = st.slider("Top N venues", 5, 20, 10, key="venue_n")
    venues = m_view["venue"].dropna().value_counts().head(n)
    if not empty_guard(venues.empty):
        fig, ax = plt.subplots(figsize=(10, 0.4 * n + 1.5))
        ax.barh(venues.index[::-1], venues.values[::-1], color="#6a4c93")
        ax.set_xlabel("Matches")
        for i, v in enumerate(venues.values[::-1]):
            ax.text(v, i, f" {v}", va="center")
        st.pyplot(fig, clear_figure=True)


# ---------------- Data tab ----------------
with tab_data:
    st.subheader("Match-level table (filtered)")
    st.caption(f"{len(m_view):,} matches after filters")
    st.dataframe(m_view.head(500), use_container_width=True, hide_index=True)
    st.download_button(
        "Download filtered matches as CSV",
        data=m_view.to_csv(index=False).encode("utf-8"),
        file_name="ipl_matches_filtered.csv",
        mime="text/csv",
    )

    with st.expander("Peek at raw ball-by-ball data (first 200 rows)"):
        st.dataframe(df_view.head(200), use_container_width=True, hide_index=True)


# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.divider()
st.caption(
    "Built with pandas + matplotlib + Streamlit · "
    "Source: [GitHub](https://github.com/Tanya-garg10/IPL-Crunch-26-Data-Analytics)"
)
