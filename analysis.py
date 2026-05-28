"""
IPL-Crunch-26 — exploratory analysis pipeline.

Reads the ball-by-ball IPL CSV in `data/`, derives match-level and player-level
stats, writes individual chart PNGs into `charts/`, and assembles a multi-page
`report.pdf` summarizing the findings.
"""

from __future__ import annotations

import glob
import os
import textwrap
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages

ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"
CHARTS_DIR = ROOT / "charts"
REPORT_PATH = ROOT / "report.pdf"

CHARTS_DIR.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# Load
# ---------------------------------------------------------------------------
def find_csv() -> Path:
    csvs = sorted(DATA_DIR.glob("*.csv"))
    if not csvs:
        raise FileNotFoundError(f"No CSV found in {DATA_DIR}")
    return csvs[0]


def load_ball_data(path: Path) -> pd.DataFrame:
    print(f"Reading {path.name} ...")
    df = pd.read_csv(path, low_memory=False)
    print(f"  rows: {len(df):,}  cols: {len(df.columns)}")
    return df


# ---------------------------------------------------------------------------
# Derive match-level frame from ball-by-ball
# ---------------------------------------------------------------------------
MATCH_COLS = [
    "match_id", "date", "season", "event", "venue", "city",
    "team1", "team2", "toss_winner", "toss_decision",
    "winner", "win_by_runs", "win_by_wickets", "player_of_match",
]


def build_match_frame(df: pd.DataFrame) -> pd.DataFrame:
    cols = [c for c in MATCH_COLS if c in df.columns]
    matches = df[cols].drop_duplicates(subset="match_id").reset_index(drop=True)
    matches["date"] = pd.to_datetime(matches["date"], errors="coerce")
    print(f"  unique matches: {len(matches):,}")
    return matches


# ---------------------------------------------------------------------------
# Plot helpers
# ---------------------------------------------------------------------------
def _save(fig: plt.Figure, name: str) -> Path:
    out = CHARTS_DIR / f"{name}.png"
    fig.tight_layout()
    fig.savefig(out, dpi=150, bbox_inches="tight")
    print(f"  wrote {out.relative_to(ROOT)}")
    return out


def chart_toss_impact(matches: pd.DataFrame) -> plt.Figure:
    decided = matches.dropna(subset=["toss_winner", "winner"])
    toss_won = (decided["toss_winner"] == decided["winner"]).sum()
    toss_lost = (decided["toss_winner"] != decided["winner"]).sum()
    fig, ax = plt.subplots(figsize=(7, 5))
    bars = ax.bar(
        ["Toss Winner Won Match", "Toss Winner Lost Match"],
        [toss_won, toss_lost],
        color=["#2a9d8f", "#e76f51"],
    )
    ax.set_title("Toss Impact on Match Result")
    ax.set_ylabel("Number of Matches")
    for b, v in zip(bars, [toss_won, toss_lost]):
        ax.text(b.get_x() + b.get_width() / 2, v, f"{v}",
                ha="center", va="bottom")
    ax.set_ylim(0, max(toss_won, toss_lost) * 1.15)
    return fig


def chart_toss_decision(matches: pd.DataFrame) -> plt.Figure:
    counts = matches["toss_decision"].value_counts()
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.pie(counts, labels=counts.index, autopct="%1.1f%%",
           colors=["#264653", "#f4a261"], startangle=90)
    ax.set_title("Toss Decision: Bat vs Field")
    return fig


def chart_top_teams(matches: pd.DataFrame, n: int = 5) -> plt.Figure:
    top = matches["winner"].dropna().value_counts().head(n)
    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.barh(top.index[::-1], top.values[::-1], color="#1d3557")
    ax.set_title(f"Top {n} IPL Teams by Match Wins")
    ax.set_xlabel("Wins")
    for b, v in zip(bars, top.values[::-1]):
        ax.text(v, b.get_y() + b.get_height() / 2, f" {v}",
                va="center")
    return fig


def chart_top_player_of_match(matches: pd.DataFrame, n: int = 10) -> plt.Figure:
    top = matches["player_of_match"].dropna().value_counts().head(n)
    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.barh(top.index[::-1], top.values[::-1], color="#e9c46a")
    ax.set_title(f"Top {n} Players — Player of the Match Awards")
    ax.set_xlabel("Awards")
    for b, v in zip(bars, top.values[::-1]):
        ax.text(v, b.get_y() + b.get_height() / 2, f" {v}",
                va="center")
    return fig


def chart_top_run_scorers(df: pd.DataFrame, n: int = 10) -> plt.Figure:
    runs = df.groupby("batter")["runs_batter"].sum().sort_values(ascending=False).head(n)
    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.barh(runs.index[::-1], runs.values[::-1], color="#2a9d8f")
    ax.set_title(f"Top {n} Run Scorers (career across dataset)")
    ax.set_xlabel("Runs")
    for b, v in zip(bars, runs.values[::-1]):
        ax.text(v, b.get_y() + b.get_height() / 2, f" {int(v)}",
                va="center")
    return fig


def chart_top_wicket_takers(df: pd.DataFrame, n: int = 10) -> plt.Figure:
    bowler_wkts = df.dropna(subset=["wicket_kind"])
    # Exclude run-out style dismissals not credited to bowlers
    not_credited = {"run out", "retired hurt", "retired out", "obstructing the field"}
    bowler_wkts = bowler_wkts[~bowler_wkts["wicket_kind"].str.lower().isin(not_credited)]
    wkts = bowler_wkts.groupby("bowler").size().sort_values(ascending=False).head(n)
    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.barh(wkts.index[::-1], wkts.values[::-1], color="#e76f51")
    ax.set_title(f"Top {n} Wicket Takers")
    ax.set_xlabel("Wickets")
    for b, v in zip(bars, wkts.values[::-1]):
        ax.text(v, b.get_y() + b.get_height() / 2, f" {int(v)}",
                va="center")
    return fig


def chart_matches_per_season(matches: pd.DataFrame) -> plt.Figure:
    per = matches.groupby("season").size()
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(per.index.astype(str), per.values, color="#457b9d")
    ax.set_title("Matches per Season")
    ax.set_xlabel("Season")
    ax.set_ylabel("Matches")
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    return fig


def chart_top_venues(matches: pd.DataFrame, n: int = 10) -> plt.Figure:
    top = matches["venue"].dropna().value_counts().head(n)
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(top.index[::-1], top.values[::-1], color="#6a4c93")
    ax.set_title(f"Top {n} Venues by Matches Hosted")
    ax.set_xlabel("Matches")
    for b, v in zip(bars, top.values[::-1]):
        ax.text(v, b.get_y() + b.get_height() / 2, f" {v}",
                va="center")
    return fig


# ---------------------------------------------------------------------------
# Insights
# ---------------------------------------------------------------------------
def compute_insights(df: pd.DataFrame, matches: pd.DataFrame) -> list[str]:
    decided = matches.dropna(subset=["toss_winner", "winner"])
    toss_won = (decided["toss_winner"] == decided["winner"]).sum()
    toss_pct = toss_won / len(decided) * 100 if len(decided) else 0

    field_pct = (matches["toss_decision"].eq("field").mean() * 100)

    top_team = matches["winner"].value_counts().idxmax()
    top_team_wins = int(matches["winner"].value_counts().max())

    top_pom = matches["player_of_match"].value_counts().idxmax()
    top_pom_count = int(matches["player_of_match"].value_counts().max())

    runs = df.groupby("batter")["runs_batter"].sum().sort_values(ascending=False)
    top_scorer = runs.index[0]
    top_runs = int(runs.iloc[0])

    seasons = matches["season"].nunique()
    venues = matches["venue"].nunique()

    return [
        f"Dataset spans {seasons} seasons, {len(matches):,} matches, "
        f"{len(df):,} ball-by-ball records.",
        f"Toss winners go on to win the match {toss_pct:.1f}% of the time — "
        f"a marginal edge, not a decisive one.",
        f"Captains chose to field first {field_pct:.1f}% of the time after winning the toss.",
        f"Most successful franchise: {top_team} with {top_team_wins} wins.",
        f"Most decorated player: {top_pom} won Player of the Match {top_pom_count} times.",
        f"Leading run scorer in the dataset: {top_scorer} with {top_runs:,} runs.",
        f"Matches were played across {venues} unique venues.",
    ]


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
def write_pdf(figs: list[tuple[str, plt.Figure]], insights: list[str]) -> None:
    with PdfPages(REPORT_PATH) as pdf:
        # Cover page
        cover = plt.figure(figsize=(8.5, 11))
        cover.text(0.5, 0.78, "IPL-Crunch-26", ha="center", fontsize=32, weight="bold")
        cover.text(0.5, 0.72, "Exploratory Analysis Report",
                   ha="center", fontsize=16, color="#555")
        cover.text(0.5, 0.66, "Indian Premier League — Ball-by-Ball Dataset",
                   ha="center", fontsize=12, style="italic")
        cover.text(0.1, 0.5, "Sections", fontsize=14, weight="bold")
        toc = [
            "1. Key Insights",
            "2. Toss Analysis",
            "3. Team Analysis",
            "4. Player Analysis",
            "5. Season & Venue Trends",
        ]
        cover.text(0.12, 0.46, "\n".join(toc), fontsize=12, va="top")
        cover.text(0.5, 0.05, "Generated automatically with pandas + matplotlib",
                   ha="center", fontsize=9, color="#888")
        pdf.savefig(cover)
        plt.close(cover)

        # Insights page
        insight_fig = plt.figure(figsize=(8.5, 11))
        insight_fig.text(0.1, 0.92, "Key Insights", fontsize=20, weight="bold")
        y = 0.85
        for i, line in enumerate(insights, 1):
            wrapped = textwrap.fill(f"{i}.  {line}", width=80)
            insight_fig.text(0.1, y, wrapped, fontsize=11, va="top")
            y -= 0.08
        pdf.savefig(insight_fig)
        plt.close(insight_fig)

        # Chart pages
        for title, fig in figs:
            page = plt.figure(figsize=(8.5, 11))
            page.text(0.5, 0.95, title, ha="center", fontsize=16, weight="bold")
            # embed the chart figure as an image-like axes
            tmp_path = CHARTS_DIR / "_tmp_for_pdf.png"
            fig.savefig(tmp_path, dpi=150, bbox_inches="tight")
            img = plt.imread(tmp_path)
            ax = page.add_axes([0.08, 0.1, 0.84, 0.78])
            ax.imshow(img)
            ax.axis("off")
            pdf.savefig(page)
            plt.close(page)
            tmp_path.unlink(missing_ok=True)

    print(f"  wrote {REPORT_PATH.relative_to(ROOT)}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    csv_path = find_csv()
    df = load_ball_data(csv_path)
    matches = build_match_frame(df)

    print("\nGenerating charts ...")
    figs: list[tuple[str, plt.Figure]] = []

    fig = chart_toss_impact(matches)
    _save(fig, "toss_impact")
    figs.append(("Toss Impact on Match Result", fig))

    fig = chart_toss_decision(matches)
    _save(fig, "toss_decision")
    figs.append(("Toss Decision Distribution", fig))

    fig = chart_top_teams(matches)
    _save(fig, "top_teams")
    figs.append(("Top Teams by Wins", fig))

    fig = chart_top_player_of_match(matches)
    _save(fig, "top_player_of_match")
    figs.append(("Top Player of the Match Awardees", fig))

    fig = chart_top_run_scorers(df)
    _save(fig, "top_run_scorers")
    figs.append(("Top Run Scorers", fig))

    fig = chart_top_wicket_takers(df)
    _save(fig, "top_wicket_takers")
    figs.append(("Top Wicket Takers", fig))

    fig = chart_matches_per_season(matches)
    _save(fig, "matches_per_season")
    figs.append(("Matches per Season", fig))

    fig = chart_top_venues(matches)
    _save(fig, "top_venues")
    figs.append(("Top Venues by Matches Hosted", fig))

    print("\nComputing insights ...")
    insights = compute_insights(df, matches)
    for line in insights:
        print(f"  - {line}")

    print("\nBuilding PDF ...")
    write_pdf(figs, insights)

    for _, fig in figs:
        plt.close(fig)

    print("\nDone.")


if __name__ == "__main__":
    main()
