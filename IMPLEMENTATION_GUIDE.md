# Implementation Guide

## File Structure

```
lol-props-lab/
├── app.py                     # Flask application entry point
├── refresh_data.py            # Data download and ingestion script
├── requirements.txt           # Python dependencies
├── README.md                  # Setup instructions
│
├── config.py                  # Configuration and model parameters
│
├── database/
│   ├── __init__.py
│   ├── db.py                  # SQLite connection and setup
│   ├── schema.sql             # Table creation statements
│   └── queries.py             # Common SQL queries as functions
│
├── ingestion/
│   ├── __init__.py
│   ├── downloader.py          # Downloads CSVs from Oracle's Elixir
│   ├── parser.py              # Parses and normalizes CSV data
│   └── loader.py              # Loads parsed data into SQLite
│
├── engine/
│   ├── __init__.py
│   ├── projections.py         # Main projection pipeline
│   ├── baseline.py            # Stage 1: Player baseline calculation
│   ├── opponent.py            # Stage 2: Opponent adjustments
│   ├── pace.py                # Stage 3: Pace adjustments
│   ├── gamelength.py          # Stage 4: Game length adjustments
│   ├── winprob.py             # Stage 5: Win probability modifier
│   ├── distributions.py       # Stage 6-7: Distribution modeling and over/under calc
│   └── confidence.py          # Confidence level assessment
│
├── recommendations/
│   ├── __init__.py
│   ├── edge.py                # Edge calculation
│   ├── ranker.py              # Pick ranking and sorting
│   ├── correlations.py        # Correlation detection between picks
│   └── parlays.py             # Parlay suggestion logic
│
├── tracking/
│   ├── __init__.py
│   ├── picks.py               # Pick recording and result entry
│   ├── performance.py         # Performance metrics calculation
│   └── calibration.py         # Model calibration analysis
│
├── api/
│   ├── __init__.py
│   ├── routes.py              # Flask API routes
│   ├── matches.py             # Match-related endpoints
│   ├── projections_api.py     # Projection endpoints
│   ├── picks_api.py           # Pick management endpoints
│   └── results_api.py         # Results and performance endpoints
│
├── static/
│   ├── css/
│   │   └── style.css          # Main stylesheet
│   ├── js/
│   │   ├── app.js             # Main application logic
│   │   ├── dashboard.js       # Dashboard view logic
│   │   ├── bestpicks.js       # Best picks view logic
│   │   ├── results.js         # Results view logic
│   │   ├── settings.js        # Settings view logic
│   │   └── charts.js          # Chart rendering (Chart.js or similar)
│   └── img/
│       └── (league icons, role icons, etc.)
│
├── templates/
│   └── index.html             # Single-page app template
│
└── data/
    ├── lol_props.db           # SQLite database (auto-created)
    └── csv_cache/             # Cached CSV downloads
```

---

## Dependencies

### requirements.txt
```
flask>=3.0
pandas>=2.0
numpy>=1.24
scipy>=1.11
requests>=2.31
```

### Key Libraries
| Library | Purpose |
|---------|---------|
| Flask | Web server, API routing, template serving |
| pandas | CSV parsing, data manipulation |
| numpy | Numerical calculations, weighted averages |
| scipy | Statistical distributions (nbinom, norm) for probability calculations |
| requests | Downloading CSVs from Oracle's Elixir |
| sqlite3 | Built-in Python — database (no install needed) |

---

## Setup Instructions

```bash
# 1. Clone or create the project directory
mkdir lol-props-lab && cd lol-props-lab

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Initialize database and download data
python refresh_data.py

# 5. Start the application
python app.py

# 6. Open browser to http://localhost:5000
```

---

## API Endpoints

### Match & Projection Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/leagues` | List all leagues with game counts |
| GET | `/api/matches?league=LCK&status=upcoming` | List matches, filterable by league and status |
| GET | `/api/matches/<match_id>/projections` | Get projections for all players in a match |
| GET | `/api/players/<player_name>/history` | Get player's recent game history |
| GET | `/api/players/<player_name>/trend` | Get player's rolling average trend data |
| GET | `/api/teams/<team_name>/stats` | Get team pace, game length, win rate stats |

### Line Entry & Edge Calculation

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/lines` | Submit a line: `{player, stat, line_value}` → returns edge calc |
| GET | `/api/best-picks` | Get all recommended picks across entered lines |
| POST | `/api/picks` | Record a pick (save to picks table) |
| GET | `/api/picks/pending` | Get all pending (unresolved) picks |

### Results & Tracking

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/results` | Enter actual stats for a completed match |
| GET | `/api/performance/summary` | Overall performance metrics |
| GET | `/api/performance/calibration` | Calibration data for chart |
| GET | `/api/performance/history` | Full pick history with filters |
| GET | `/api/performance/by-stat` | Hit rate broken down by stat type |
| GET | `/api/performance/by-league` | Hit rate broken down by league |

### Settings & Data

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/settings` | Get current model parameters |
| PUT | `/api/settings` | Update model parameters |
| POST | `/api/refresh` | Trigger data refresh |
| GET | `/api/data/status` | Database stats and freshness |

---

## Data Flow

### On Data Refresh
```
Oracle's Elixir (CSV files on web)
        ↓ download
    csv_cache/ (local files)
        ↓ parse & normalize
    pandas DataFrames (in memory)
        ↓ upsert
    SQLite database (lol_props.db)
```

### On Match Selection
```
User selects match in UI
        ↓ GET /api/matches/<id>/projections
    Backend fetches player/team data from SQLite
        ↓
    Projection engine runs full pipeline (Stages 1-7)
        ↓
    Returns JSON: {players: [{name, role, projections: {kills: {mean, std, confidence}, ...}}]}
        ↓
    Frontend renders projection table with input fields
```

### On Line Entry
```
User types line value (e.g., 4.5)
        ↓ POST /api/lines {player: "Chovy", stat: "kills", line: 4.5}
    Backend calculates P(over), P(under), edge, direction
        ↓
    Returns JSON: {direction: "OVER", probability: 0.62, edge: 0.12, confidence: "HIGH"}
        ↓
    Frontend instantly updates that row with edge coloring and recommendation
```

---

## Upcoming Match Handling

### The Problem
Oracle's Elixir provides historical data, not upcoming schedules. The system needs to know which matches are coming up to display them in the match selector.

### Solutions (in order of preference)

**Option 1: Manual Match Entry**
User enters upcoming matches manually: Team A vs Team B, League, Date.
- Simplest to implement
- No external dependency
- UI: A "+" button to add a match, with team name autocomplete from the database

**Option 2: Scrape Schedule from Leaguepedia/Liquipedia**
These wikis maintain current schedules for all leagues.
- More automated but fragile (scraping can break)
- Implement as a secondary feature after Option 1 is working

**Option 3: Riot Esports API (if available)**
Riot's esports APIs have historically been semi-public.
- Most automated but API access may be unreliable or change
- Implement only if stable access is confirmed

**Recommendation:** Start with Option 1 (manual entry). It's reliable and the user is already manually entering lines, so adding a match takes seconds. Add automation later if desired.

### Match Entry Fields
- League (dropdown from known leagues)
- Team A (autocomplete from teams table)
- Team B (autocomplete from teams table)
- Date (date picker)
- Best-of format (Bo1, Bo3, Bo5) — affects whether projections are per-game or per-series

---

## Best-of Series Handling

### Bo1 (Most Regular Season Games)
- Straightforward: one game, one set of projections

### Bo3 / Bo5 (Playoffs)
- Underdog props may be per-game or per-series — the user should indicate which
- For per-game props: projections are the same as Bo1
- For per-series props (if offered): multiply per-game projections by expected number of games
  - Expected games in Bo3: 2.0 + (2 * p_3games) where p_3games is probability of going to game 3
  - Expected games in Bo5: 3.0 + complexity...
  - Simpler: average games in the teams' recent Bo3/Bo5 series

### Implementation
- Match entry includes a "Format" field (Bo1/Bo3/Bo5)
- A toggle for "Props are per-game" vs "Props are per-series"
- Default assumption: per-game (most common on Underdog)

---

## Performance Optimization

### Database Indexing
```sql
CREATE INDEX idx_player_games_player ON player_games(playername, date DESC);
CREATE INDEX idx_player_games_team ON player_games(teamname, date DESC);
CREATE INDEX idx_player_games_league ON player_games(league, date DESC);
CREATE INDEX idx_player_games_position ON player_games(position);
CREATE INDEX idx_team_games_team ON team_games(teamname, date DESC);
CREATE INDEX idx_games_league ON games(league, date DESC);
```

### Caching
- Cache projection results for a match until data is refreshed or parameters change
- Store computed league averages in a summary table, recalculate on refresh
- Player baseline calculations can be cached and invalidated on new data

### Response Times
- Target: <500ms for projection calculation on match selection
- Target: <100ms for edge calculation on line entry
- Target: <200ms for best picks aggregation

---

## Testing Strategy

### Unit Tests
- Projection engine stages (each stage independently testable with known inputs)
- Edge calculation with known distributions
- CSV parsing with sample data

### Integration Tests
- Full pipeline from CSV → database → projection → recommendation
- API endpoint responses with test database

### Validation Tests
- Backtest: Run projections on historical matches where we know the outcome
- Check that model probability calibration is reasonable before using real money
- Compare projections to actual results on a set of 100+ historical games

---

## Future Enhancements (Post-MVP)
1. **Automated schedule scraping** from Liquipedia
2. **Champion draft integration** — adjust projections based on champion picked (requires real-time draft data)
3. **Live line tracking** — if Underdog provides an API or the lines can be scraped
4. **Multi-game series modeling** — proper Bo3/Bo5 Monte Carlo simulations
5. **Bankroll management module** — Kelly criterion-based bet sizing
6. **Push notifications** — alert when a high-edge opportunity appears
7. **Meta shift detection** — automatically detect when a new patch significantly changes the landscape
8. **Player-champion stat profiles** — project differently based on which champion a player locks in
9. **Weather report** — daily summary of best available picks across all leagues
10. **Export to CSV** — export picks and results for external analysis
