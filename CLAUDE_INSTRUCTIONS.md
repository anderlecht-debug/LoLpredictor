# Claude Project Instructions

## What This Project Is
You are building a locally-run LoL esports player prop projection system called "LoL Props Lab." The user bets on Underdog Fantasy player props (higher/lower on kills, deaths, assists, CS) and needs a statistically-driven tool to identify profitable picks.

## Context Documents
Read these documents to understand the full system before writing any code:

1. **PROJECT_OVERVIEW.md** — High-level purpose, workflow, tech stack, design principles
2. **DATA_MODEL.md** — Oracle's Elixir data source, SQLite schema, data refresh process
3. **PROJECTION_ENGINE.md** — The complete statistical model: 7-stage pipeline from player baseline through probability calculation
4. **RECOMMENDATION_ENGINE.md** — Edge calculation, pick ranking, correlation awareness, parlay suggestions, result tracking
5. **FRONTEND_SPEC.md** — UI views, layout, color theme, interaction patterns, component details
6. **IMPLEMENTATION_GUIDE.md** — File structure, dependencies, API endpoints, data flow, setup instructions
7. **LOL_DOMAIN_KNOWLEDGE.md** — Critical LoL esports context: role differences, patch impact, league tiers, data quirks

## How to Use These Documents

### When building backend/engine code:
Refer to DATA_MODEL.md for schema, PROJECTION_ENGINE.md for the exact algorithms, and LOL_DOMAIN_KNOWLEDGE.md for domain-specific edge cases.

### When building the frontend:
Refer to FRONTEND_SPEC.md for exact layout, color codes, and component behavior. Use RECOMMENDATION_ENGINE.md for understanding what data the UI needs to display.

### When building API routes:
Refer to IMPLEMENTATION_GUIDE.md for the endpoint spec and data flow diagrams.

### When debugging projection accuracy:
Refer to PROJECTION_ENGINE.md for the parameter defaults and tuning guidance, and LOL_DOMAIN_KNOWLEDGE.md for common data pitfalls.

## Key Design Decisions Already Made
- **Tech stack:** Python/Flask backend, SQLite database, vanilla HTML/CSS/JS frontend
- **Data source:** Oracle's Elixir (free CSVs)
- **No external API keys or paid services**
- **Runs locally at localhost:5000**
- **Single command to start:** `python app.py`
- **Upcoming matches are entered manually** (not scraped)
- **Underdog lines are entered manually** by the user
- **The system tracks picks and outcomes** for performance analysis

## Build Order (Suggested)
1. Database schema and data ingestion (refresh_data.py)
2. Projection engine (the 7-stage pipeline)
3. API routes (Flask backend)
4. Frontend (HTML/CSS/JS served by Flask)
5. Recommendation engine (edge calculation, ranking)
6. Result tracking and performance dashboard
7. Polish and testing

## Important Constraints
- Everything must work offline after the initial data download
- No npm, no webpack, no frontend build tools — keep it simple
- The user is not deeply technical — setup must be minimal
- All model parameters should be adjustable in the Settings view
- The system must handle missing or incomplete data gracefully (flag low confidence, don't crash)
