# EconExp (EconLab Classroom)

A modular [oTree](https://www.otree.org/) toolkit for running interactive classroom experiments in microeconomics and behavioral economics. Students participate directly from their smartphones, tablets, or laptops with no client-side installation, while instructors project live class distributions, interactive charts, and optional AI-assisted feedback for same-lesson debriefing.

---

## Experiment Modules

The repository contains four self-contained classroom experiment apps:

| Folder | Experiment | Classroom Mechanism | Key Outputs & Debriefing |
| :--- | :--- | :--- | :--- |
| [`BEAUTY_CONTEST/`](BEAUTY_CONTEST/) | **Beauty Contest** (Nagel, 1995) | One-round strategic guessing game: choose an integer in $[0, 100]$; the target is $2/3$ of the class average, and the closest guess wins/splits a 100-point jackpot. | Participant-facing interactive distribution chart, distance-to-target metrics, and optional plain-language **participant AI feedback** (`Results.html`), plus an aggregate instructor dashboard (`admin_report.html`). |
| [`PGG/`](PGG/) | **Public Goods Game** | Repeated voluntary contribution mechanism (groups of 3, 3 rounds, 100-point endowment, multiplier $M = 2$, $\text{MPCR} = 2/3$). Includes an interactive pre-play payoff calculator. | Round-by-round contribution trajectories, group heterogeneity, free-riding vs. conditional cooperation dynamics, and optional **instructor AI commentary** (`admin_report.html`). |
| [`Market/`](Market/) | **Double Auction Market** | Live continuous double auction where Participant 1 is the instructor (opening/closing trading rounds) and students trade single units as buyers or sellers with private induced values/costs. | Competitive supply/demand step functions, live order book, transaction price path, realized surplus vs. theoretical competitive equilibrium, and optional **instructor AI commentary** (`admin_report.html`). |
| [`RISK_PREFS/`](RISK_PREFS/) | **Three Risk Tasks** | Within-subject risk preference elicitation after a short interactive probability tutorial: Holt–Laury Multiple Price List (2002), Bomb Risk Elicitation Task (Crosetto & Filippin, 2013), and Gneezy–Potters investment task (1997) in randomized order, followed by the SOEP general risk question (0–10). | Cross-task CRRA parameter estimation, within-subject consistency comparison, interactive payoff resolution (`Summary.html`), participant & instructor **AI feedback**, and class correlation matrix (`admin_report.html`). |

All four apps support **Italian (`it`)** and **English (`en`)** student interfaces via the session configuration.

---

## Folder Structure

```text
EconExp/
├── settings.py              # oTree project settings and SESSION_CONFIGS
├── requirements.txt         # Python dependencies (otree, openai, psycopg2-binary)
├── BEAUTY_CONTEST/          # p-Beauty Contest app (Nagel, 1995)
├── PGG/                     # Repeated Public Goods Game app
├── Market/                  # Live Continuous Double Auction Market app
├── RISK_PREFS/              # Combined Three Risk Tasks app (MPL, BRET, Investment)
├── _static/                 # Shared CSS stylesheets across apps
└── docs/                    # Static GitHub Pages project website & working paper
```

---

## Available Session Configurations

Defined in [`settings.py`](settings.py) under `SESSION_CONFIGS`:

| Session Name | Display Name | App | Language | Default Demo Participants |
| :--- | :--- | :--- | :---: | :---: |
| `beauty_contest_eng` | Beauty Contest (ENG) | `BEAUTY_CONTEST` | `en` | 6 |
| `beauty_contest_ita` | Beauty Contest (ITA) | `BEAUTY_CONTEST` | `it` | 6 |
| `public_goods_eng` | Public Goods Game (ENG) | `PGG` | `en` | 3 |
| `public_goods_ita` | Public Goods Game (ITA) | `PGG` | `it` | 3 |
| `market_eng` | Market (ENG) | `Market` | `en` | 7 (1 instructor + 6 traders) |
| `market_ita` | Market (ITA) | `Market` | `it` | 7 (1 instructor + 6 traders) |
| `Risk_Prefs_Random_Order` | Risk Preferences Random Order (ENG) | `RISK_PREFS` | `en` | 3 |
| `Risk_Prefs_Random_Order_ITA` | Risk Preferences Random Order (ITA) | `RISK_PREFS` | `it` | 3 |

Each session config can be customized directly in the oTree Admin UI when creating a classroom session (e.g., toggling `enable_ai_commentary` / `enable_ai_feedback` or switching `language` between `'it'` and `'en'`).

---

## Quick Start

1. **Install dependencies** (Python 3.9+ recommended):

   ```bash
   pip install -r requirements.txt
   ```

2. **Start the local oTree development server**:

   ```bash
   otree devserver
   ```

3. **Open the interface** in your browser at:

   ```text
   http://localhost:8000
   ```

   Select any demo session from the landing page, or go to **Sessions → Create New Session** to launch a classroom session with a shareable student link.

---

## Optional Environment Variables & Security

The project reads configuration secrets exclusively from environment variables—**no API keys, passwords, or participant databases (`db.sqlite3`) are stored in this repository**:

- `OPENAI_API_KEY`: Enables optional OpenAI-generated feedback/commentary (`gpt-5.4-mini` by default). If `OPENAI_API_KEY` or the `openai` package is not present, all experiments run normally and gracefully omit or display a fallback notice for the AI section.
- `OTREE_ADMIN_PASSWORD`: Password for the oTree admin interface in production.
- `OTREE_SECRET_KEY`: Django/oTree secret key for production deployments (a development fallback is used locally).
- `OPENAI_BEAUTY_MODEL` / `OPENAI_PGG_MODEL` / `OPENAI_MARKET_MODEL` / `OPENAI_RISK_PREFS_MODEL`: Optional environment overrides for the OpenAI model name.

Example setup in a terminal or virtual environment:

```bash
export OPENAI_API_KEY="your-openai-api-key"
export OTREE_ADMIN_PASSWORD="your-admin-password"
export OTREE_SECRET_KEY="a-long-random-secret-string"
```

---

## Project Website (GitHub Pages)

The [`docs/`](docs/) directory contains a static project website suitable for GitHub Pages (`master` branch → `/docs` folder), summarizing the pedagogical workflow, the four apps, and linking to the companion working paper ([`docs/assets/DRAFT.pdf`](docs/assets/DRAFT.pdf)).
