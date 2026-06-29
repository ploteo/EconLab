# EconExp

Short oTree project for classroom experiments in experimental economics.

The project currently contains two experiments:

- `PGG`: a Public Goods Game with groups of 3 participants, 3 rounds, an endowment of 100 points, and a multiplier of 2. Participants choose how much to contribute to a common project; total contributions are multiplied and shared equally within the group.
- `BEAUTY_CONTEST`: a one-round Beauty Contest game based on Nagel (1995). Participants choose an integer between 0 and 100; the target is `2/3` of the average guess, and the closest guess wins/splits a jackpot of 100 points.

Both apps include participant pages, payoff calculation, admin reports, static assets/styles, and optional AI-generated commentary for classroom debriefing.

## Folder Structure

```text
EconExp/
+-- settings.py              # oTree project settings and session configs
+-- PGG/                     # Public Goods Game app
+-- BEAUTY_CONTEST/          # Beauty Contest app
+-- docs/                    # Static GitHub Pages project website
+-- _static/                 # Shared static files
```

Main app files:

- `PGG/__init__.py` and `BEAUTY_CONTEST/__init__.py`: game constants, models, payoff logic, page sequence, admin-report data, and optional OpenAI commentary.
- `*.html`: oTree page templates for instructions, choices, results, and admin reports.
- `static/` and `_static/`: CSS, images, and JavaScript used by the experiment pages.
- `tests.py`: oTree tests for the app.

## Available Sessions

Sessions are defined in `settings.py`:

- `beauty_contest_ita`: Italian Beauty Contest, 6 demo participants.
- `public_goods_ita`: Italian Public Goods Game, 3 demo participants.
- `public_goods_eng`: English Public Goods Game, 3 demo participants.

The interface language is controlled by the session config field `language`, currently `it` or `en`.

## Basic Use

From inside this folder, install the required Python packages in your environment if needed:

```bash
pip install otree
```

Install `openai` as well if you want to use the optional AI commentary in the admin reports.

Then start the oTree development server:

```bash
otree devserver
```

Open the local URL shown by oTree, usually:

```text
http://localhost:8000
```

From the oTree demo/admin page, choose one of the session configs listed above.

## Project Website

The `docs/` folder contains a static website for GitHub Pages. It introduces the project, explains the classroom workflow, lists the apps in this repository, and links to `docs/assets/DRAFT.pdf`.

To publish it on GitHub:

1. Open the repository settings on GitHub.
2. Go to `Pages`.
3. Select `Deploy from a branch`.
4. Choose the `master` branch and the `/docs` folder.

GitHub Pages can host the documentation site only. The oTree experiments still need to run on a Python server.

## Optional Environment Variables

The project reads these environment variables:

- `OTREE_ADMIN_PASSWORD`: admin password for the oTree admin interface.
- `OTREE_SECRET_KEY`: production secret key. If not set, a development fallback is used.
- `OPENAI_API_KEY`: enables AI commentary in admin reports.
- `OPENAI_PGG_MODEL` / `OPENAI_BEAUTY_MODEL`: optional model overrides for AI commentary.

If `openai` or `OPENAI_API_KEY` is missing, the experiments still run; only the automatic AI commentary is unavailable.

## Notes

- This repository contains generated cache files such as `__pycache__`; these are not required to run the experiments.
- The apps are intended for teaching and classroom debriefing, with admin reports summarizing participant choices and results.
