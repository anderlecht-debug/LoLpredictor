# LoL Esports Player Prop Projection System

## Purpose
A locally-run, browser-based tool that projects individual player stat lines for professional League of Legends matches and identifies profitable player prop picks on Underdog Fantasy.

## Target User
A solo bettor who manually enters Underdog Fantasy lines and wants statistically-driven recommendations. The system must be free, local (localhost), and require no external API keys or paid services.

## Core Workflow
1. User downloads/refreshes data from Oracle's Elixir (free CSV exports of all professional LoL match data globally).
2. Data is parsed and stored in a local SQLite database.
3. User opens `localhost:5000` in their browser.
4. User selects an upcoming match (league, team vs team).
5. System displays projected stat lines for every player in that match (kills, deaths, assists, CS).
6. User manually enters Underdog Fantasy lines next to each projection.
7. System calculates edge (model probability vs implied probability) and flags recommended picks.
8. A "Best Picks" view aggregates the strongest edges across all entered matches.
9. System tracks results over time for performance evaluation and model tuning.

## Betting Platform
Underdog Fantasy — player prop pick'ems (higher/lower on individual stat lines), combined into parlays. This is NOT match winner betting. The entire system is oriented around projecting individual player stat distributions.

## Leagues Covered
All professional leagues available on Oracle's Elixir:
- **Tier 1:** LCK (Korea), LPL (China), LEC (Europe), LCS (North America)
- **Tier 2:** PCS (Pacific), VCS (Vietnam), CBLOL (Brazil), LLA (Latin America), LJL (Japan), LCO (Oceania)
- **International:** MSI, Worlds
- **Any additional leagues** Oracle's Elixir adds over time

## Stats Projected
Primary (these are the props Underdog typically offers):
- **Kills** — per player, per game
- **Deaths** — per player, per game
- **Assists** — per player, per game
- **Creep Score (CS)** — per player, per game

Secondary (used as model inputs, may also be projected):
- Damage per minute (DPM)
- Gold per minute (GPM)
- Vision score
- Kill participation %

## Tech Stack
- **Backend:** Python (Flask)
- **Database:** SQLite
- **Frontend:** Single-page HTML/CSS/JS (served by Flask)
- **Data Source:** Oracle's Elixir CSV exports
- **No external API keys, no paid services, no cloud dependencies**

## Key Design Principles
- Everything runs locally on the user's machine
- Single command to start (`python app.py`)
- Data refresh is a single command (`python refresh_data.py`)
- Clean, dark-themed UI optimized for quick decision-making
- Statistical rigor over gut feel — every recommendation has a calculated edge percentage
- Track record accountability — the system logs every pick and outcome
