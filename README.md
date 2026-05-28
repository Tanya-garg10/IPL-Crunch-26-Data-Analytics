<div align="center">

# 🏏 IPL-Crunch-26

### Crunching 19 seasons of IPL ball-by-ball data into charts and insights

![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![Pandas](https://img.shields.io/badge/Pandas-2.3-150458?logo=pandas&logoColor=white)
![Matplotlib](https://img.shields.io/badge/Matplotlib-3.10-11557c)
![Jupyter](https://img.shields.io/badge/Jupyter-Notebook-F37626?logo=jupyter&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

</div>

---

## 📌 Overview

**IPL-Crunch-26** is an end-to-end exploratory data analysis project on the Indian Premier League's ball-by-ball dataset.
It reads a single CSV (~290k ball records across 1,218 matches), derives match-level and player-level statistics, generates a curated set of charts, and stitches everything into a multi-page PDF report — all from one command.

> 🎯 **Goal:** turn raw ball-level data into a clean, presentation-ready story about toss impact, team dominance, player legends, and league-wide trends.

---

## 📂 Project Structure

```text
IPL-Crunch-26/
├── 📊 analysis.py         # One-shot pipeline: CSV → charts → PDF
├── 📓 notebook.ipynb       # Colab / Jupyter walkthrough
├── 📁 data/                # Raw IPL ball-by-ball CSV
│   └── att_0_*.csv
├── 🖼  charts/              # Auto-generated PNG charts
│   ├── toss_impact.png
│   ├── toss_decision.png
│   ├── top_teams.png
│   ├── top_player_of_match.png
│   ├── top_run_scorers.png
│   ├── top_wicket_takers.png
│   ├── matches_per_season.png
│   └── top_venues.png
├── 📄 IPL_Crunch_26_Report.pdf   # Multi-page report (re-runs create `report.pdf`)
└── 📝 README.md
```

---

## 🗂  About the Data

| Property | Value |
| :-- | :-- |
| **Granularity** | Ball-by-ball (one row per delivery) |
| **Rows** | ~289,673 |
| **Columns** | 30 |
| **Matches covered** | 1,218 |
| **Seasons** | 19 |
| **Venues** | 59 |

> ⚠️ **Heads-up:** because the CSV is ball-level, match-level fields (`toss_winner`, `winner`, `player_of_match`, etc.) repeat across every delivery of the same match. A naive `df.dropna()` would erase almost everything — `wicket_kind` is NaN on every ball where no wicket falls.
>
> ✅ **What this project does instead:**
> - **Match-level stats** → deduplicate on `match_id` first, then aggregate.
> - **Player-level stats** → use the raw ball data and group by `batter` / `bowler`.

---

## 🚀 Quick Start

### Option A — Run locally

```bash
# 1. Install dependencies
pip install pandas matplotlib

# 2. Run the full pipeline
python analysis.py
```

This rewrites every PNG in `charts/` and regenerates `report.pdf`.

### Option B — Run on Google Colab

1. Open `notebook.ipynb` in [Google Colab](https://colab.research.google.com/).
2. Upload the CSV via the file sidebar (📁 icon on the left).
3. Update `CSV_PATH` in the first cell if your filename differs.
4. **Runtime → Run all**.

---

## 📈 What You Get

### 🎲 Toss analysis
| Chart | Insight |
| :-- | :-- |
| `toss_impact.png` | Toss winners win **~50.5%** of matches — a real but small edge. |
| `toss_decision.png` | **~65.9%** of toss winners chose to field first. |

### 🏆 Team analysis
| Chart | Insight |
| :-- | :-- |
| `top_teams.png` | **Mumbai Indians** lead with **154 wins**. |

### 🌟 Player analysis
| Chart | Insight |
| :-- | :-- |
| `top_player_of_match.png` | **AB de Villiers** — most PoM awards (**25**). |
| `top_run_scorers.png` | **V Kohli** — leading run scorer (**9,050 runs**). |
| `top_wicket_takers.png` | Top 10 bowlers ranked by wickets (excludes run-outs and other dismissals not credited to a bowler). |

### 📅 Trends
| Chart | Insight |
| :-- | :-- |
| `matches_per_season.png` | Match volume across all 19 seasons. |
| `top_venues.png` | Most-used venues across the league's history. |

---

## 💡 Key Takeaways

- 🪙 **Toss is overrated** — only a ~0.5% edge over a coin flip.
- 🛡️ **Field first is the default** — chasing strategy dominates captain decisions.
- 🐬 **Mumbai Indians** are the most successful franchise in this dataset.
- 🦸 **AB de Villiers** delivers match-winning performances most often.
- 👑 **Virat Kohli** is the all-time run-scoring king of the league.

---

## 🛠  Tech Stack

- **Python 3.11**
- **pandas** — data wrangling & aggregation
- **matplotlib** — charts + multi-page PDF (`PdfPages`, no extra deps)
- **Jupyter** — interactive walkthrough

---

## 🔁 Re-running

Drop a fresh CSV into `data/` (the script auto-picks the first `*.csv`), then:

```bash
python analysis.py
```

Charts and the PDF refresh in place. Safe to commit the outputs.

---

## 🧭 Roadmap Ideas

- [ ] Add powerplay vs death-overs run-rate comparison
- [ ] Head-to-head matrix between franchises
- [ ] Strike rate vs average scatter for top batters
- [ ] Economy vs wickets scatter for top bowlers
- [ ] Interactive Plotly version of the dashboard

---

<div align="center">

Built with ☕ and `pandas.groupby` · Generated charts live in [`charts/`](./charts) · Full PDF in [`report.pdf`](./report.pdf)

</div>
