# Frontend Specification

## Overview
Single-page browser application served at `localhost:5000`. Dark-themed, clean, data-dense UI optimized for quick decision-making. No frameworks beyond vanilla JS or lightweight libraries — keep it simple and fast.

## Technology
- HTML5, CSS3, vanilla JavaScript (or lightweight Alpine.js/htmx if needed)
- Served by Flask via Jinja2 templates or static files
- All API calls to Flask backend via fetch/AJAX
- No build step required — open browser and go
- Responsive but optimized for desktop (1440px+ wide)

---

## Color Theme

### Dark Theme (Default)
```css
--bg-primary: #0d1117;       /* Main background */
--bg-secondary: #161b22;     /* Card/panel background */
--bg-tertiary: #21262d;      /* Hover/active states */
--border: #30363d;           /* Borders */
--text-primary: #e6edf3;     /* Primary text */
--text-secondary: #8b949e;   /* Secondary/muted text */
--text-tertiary: #6e7681;    /* Tertiary text */
--accent-blue: #58a6ff;      /* Links, active states */
--accent-green: #3fb950;     /* Positive/profit/strong edge */
--accent-yellow: #d29922;    /* Warnings/medium edge */
--accent-red: #f85149;       /* Negative/loss/wrong side */
--accent-purple: #bc8cff;    /* Highlights/special */
```

---

## Page Layout

### Navigation Bar (Top)
Persistent top bar with:
- App name/logo: "LoL Props Lab" (or similar)
- View tabs: **Dashboard** | **Best Picks** | **Results** | **Settings**
- Data freshness indicator: "Data updated: Mar 5, 2026" (green if <48h, yellow if 2-5 days, red if >5 days)
- Refresh button to trigger data pull

---

## View 1: Dashboard (Main View)

### Match Selector Panel (Left Sidebar or Top Section)
- Dropdown or card grid to select a match
- Grouped by league, then by date
- Shows: League badge, Team A vs Team B, date/time
- Upcoming matches listed first, then recent (for result entry)
- Search/filter by league, team, player name

### Projection Table (Center — Main Content)
Once a match is selected, display a table with 10 rows (5 players per team):

| Column | Description |
|--------|-------------|
| Side | Blue/Red team indicator (color-coded) |
| Player | Player name |
| Role | top/jng/mid/bot/sup (icon) |
| Champion | (blank for upcoming, filled for completed) |
| Stat | Stat being projected (one row per stat, or grouped) |
| Projection | Model's projected value |
| Std Dev | ± range |
| Underdog Line | **Editable input field** — user types the line here |
| Direction | Auto-calculated: OVER or UNDER |
| Model Prob | Probability of the recommended direction |
| Edge | Edge percentage (color-coded) |
| Confidence | High/Med/Low badge |
| Recommend | Checkmark icon if recommended |

**Layout option:** Rather than one row per stat, group by player with sub-rows for each stat:

```
┌─────────────────────────────────────────────────────────┐
│ BLUE SIDE — T1                                          │
├─────────────────────────────────────────────────────────┤
│ Zeus (TOP)                                              │
│   Kills   │ Proj: 3.2 │ Line: [___] │ → OVER  │ 57% │ 7% edge │ ✓  │
│   Deaths  │ Proj: 2.8 │ Line: [___] │ → UNDER │ 54% │ 4% edge │    │
│   Assists │ Proj: 5.1 │ Line: [___] │ → OVER  │ 61% │ 11% edge│ ✓  │
│   CS      │ Proj: 241 │ Line: [___] │ → OVER  │ 58% │ 8% edge │ ✓  │
├─────────────────────────────────────────────────────────┤
│ Oner (JNG)                                              │
│   ...                                                   │
```

### Player Detail Popover
Clicking a player name opens a detail panel showing:
- Last 15 game stats (mini table)
- Rolling average trend (sparkline chart)
- Opponent-specific historical matchup data
- Patch-segmented performance
- Win/loss stat splits

### Game Environment Panel (Right Sidebar or Below)
Shows the meta-factors driving projections:
- Expected game pace: "HIGH / MEDIUM / LOW" with combined KPM
- Expected game length: "XX minutes"
- Win probability: "Team A: 58% | Team B: 42%"
- Pace comparison visual (bar chart or gauge)

---

## View 2: Best Picks

### Aggregated Recommendations
Single table showing all recommended picks across all matches where lines have been entered.

| Rank | Player | Team vs Opp | League | Stat | Line | Dir | Proj | Prob | Edge | Conf |
|------|--------|-------------|--------|------|------|-----|------|------|------|------|
| 1    | Chovy  | GEN vs T1   | LCK    | Ast  | 5.5  | OVR | 7.1  | 64%  | 14%  | HIGH |
| 2    | Ruler  | JDG vs WBG  | LPL    | Kills| 3.5  | OVR | 4.8  | 61%  | 11%  | HIGH |
| ...  | ...    | ...         | ...    | ...  | ...  | ... | ...  | ...  | ...  | ...  |

### Parlay Suggestions Section
Below the table, display:
- **Best Independent Parlay (3-pick):** Top 3 picks from different games
- **Best Correlated Stack:** Top picks from a single game that share a game-environment edge
- **Custom Parlay Builder:** Checkboxes to select picks and see combined probability estimate

### Filters
- League filter (multi-select)
- Stat type filter
- Minimum edge slider
- Confidence filter
- Show/hide marginal picks

---

## View 3: Results

### Result Entry
- Select a completed match
- Auto-populate player names and the picks that were made
- Input fields for actual stat values
- "Submit Results" button calculates hits/misses and updates P/L

### Performance Dashboard
Displayed after results are tracked:

**Summary Cards (Top Row):**
- Total Picks | Hit Rate | Net P/L | ROI %

**Charts:**
- P/L over time (line chart)
- Hit rate by stat type (bar chart)
- Hit rate by confidence level (bar chart)
- Hit rate by league (bar chart)
- Calibration curve: predicted probability (x-axis) vs actual hit rate (y-axis) — should be a diagonal line
- Rolling 30-day hit rate trend

**Pick History Table:**
Sortable, filterable table of all historical picks with:
- Date, player, stat, line, direction, projection, probability, edge, actual, hit/miss, parlay group

---

## View 4: Settings

### Model Parameters
Adjustable parameters (with defaults shown):
- Lookback window: 15 games
- Decay factor: 0.85
- Min games for projection: 5
- Edge threshold for recommendation: 5%
- High confidence edge threshold: 10%

### Data Management
- Manual refresh button with progress indicator
- Last refresh timestamp
- Database stats: total games, total players, date range
- Export data (CSV of all picks/results)
- Reset database option

### Display Preferences
- Lines per page in tables
- Default league filter
- Show/hide advanced stats

---

## Interaction Patterns

### Line Entry Workflow
1. User selects a match
2. Projections auto-load
3. User types Underdog lines into input fields
4. As each line is entered, edge and recommendation instantly calculate (no submit button needed — reactive)
5. Recommended picks highlight with green glow/border
6. User reviews Best Picks tab for cross-match comparison

### Keyboard Navigation
- Tab through line input fields
- Enter to confirm and move to next
- Up/Down arrows to adjust line by 0.5 increments
- Keyboard shortcut to switch views (1/2/3/4)

### Auto-Save
All entered lines and picks persist in SQLite — if the user refreshes the browser, their work is preserved.

---

## Responsive Behavior
- Primary target: desktop (1440px+)
- Tablet (768-1440px): Stack sidebar below, reduce column count
- Mobile (< 768px): Simplified card view, one player at a time

---

## Loading States
- Skeleton screens for tables while data loads
- Spinner on data refresh with progress percentage
- Instant feedback on line entry (no perceptible delay)

---

## Error States
- "No data available" message with refresh prompt if database is empty
- "Insufficient data" warning on individual player projections with <5 games
- "Data is stale" banner if last refresh was >3 days ago
- Clear error messages if data download fails (network issues, URL changes)
