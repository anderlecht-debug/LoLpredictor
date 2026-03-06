# Data Model & Schema

## Data Source: Oracle's Elixir

### Overview
Oracle's Elixir (oracleselixir.com) provides free, downloadable CSV files containing per-player, per-game statistics for every professional League of Legends match across all major and minor leagues globally. The data is maintained by Tim Sevenhuysen and is the standard source for LoL esports analytics.

### CSV Files to Ingest
Oracle's Elixir provides data exports typically at these URLs:
- `https://oracleselixir.com/stats/players/byTournament` (player stats by tournament)
- Direct CSV download links from the site's data pages

The primary dataset is the **player-level match data CSV**, which contains one row per player per game. A standard 5v5 game produces 10 rows (5 per team). The data includes:

### Key Fields From Oracle's Elixir CSVs

#### Identifiers
| Field | Description |
|-------|-------------|
| `gameid` | Unique identifier for each game |
| `league` | League code (LCK, LPL, LEC, LCS, PCS, VCS, CBLOL, LLA, LJL, etc.) |
| `split` | Season split (Spring, Summer, etc.) |
| `playoffs` | Whether the game was a playoff game (1/0) |
| `date` | Date of the match (YYYY-MM-DD) |
| `patch` | Game patch version (e.g., "14.10") |
| `side` | Blue or Red side |
| `position` | Player role: top, jng, mid, bot, sup |
| `playername` | Player's in-game name |
| `teamname` | Team name |
| `champion` | Champion played |

#### Core Stats (Per Game)
| Field | Description |
|-------|-------------|
| `kills` | Player kills |
| `deaths` | Player deaths |
| `assists` | Player assists |
| `totalgold` | Total gold earned |
| `total cs` | Total creep score (minions + monsters) |
| `minionkills` | Lane minions killed |
| `monsterkills` | Jungle monsters killed |
| `gamelength` | Game duration in seconds |
| `result` | Win (1) or Loss (0) |

#### Advanced Stats
| Field | Description |
|-------|-------------|
| `dpm` | Damage per minute |
| `damageshare` | % of team's total damage |
| `goldspend` | Total gold spent |
| `visionscore` | Vision score |
| `vspm` | Vision score per minute |
| `killsat15` | Kills at 15 minutes |
| `deathsat15` | Deaths at 15 minutes |
| `assistsat15` | Assists at 15 minutes |
| `csat15` | CS at 15 minutes |
| `goldat15` | Gold at 15 minutes |
| `csdiffat15` | CS difference vs opponent at 15 |
| `golddiffat15` | Gold difference vs opponent at 15 |
| `xpdiffat15` | XP difference vs opponent at 15 |
| `killparticipation` | Kill participation % |
| `firstblood` | First blood involvement (1/0) |

#### Team-Level Rows
Oracle's Elixir also includes team-level aggregate rows (position = "team") with fields like:
- `firsttower`, `firstdragon`, `firstbaron`, `firstherald`
- `towers`, `dragons`, `barons`, `heralds`
- `team kpm` (team kills per minute)

---

## SQLite Database Schema

### Table: `players`
Stores unique player identities.
```sql
CREATE TABLE players (
    player_id INTEGER PRIMARY KEY AUTOINCREMENT,
    playername TEXT NOT NULL,
    current_team TEXT,
    current_league TEXT,
    current_position TEXT,
    last_updated DATE,
    UNIQUE(playername)
);
```

### Table: `teams`
Stores unique team identities.
```sql
CREATE TABLE teams (
    team_id INTEGER PRIMARY KEY AUTOINCREMENT,
    teamname TEXT NOT NULL,
    current_league TEXT,
    last_updated DATE,
    UNIQUE(teamname)
);
```

### Table: `games`
One row per game.
```sql
CREATE TABLE games (
    game_id TEXT PRIMARY KEY, -- Oracle's Elixir gameid
    date DATE NOT NULL,
    league TEXT NOT NULL,
    split TEXT,
    playoffs INTEGER DEFAULT 0,
    patch TEXT,
    gamelength INTEGER, -- seconds
    blue_team TEXT NOT NULL,
    red_team TEXT NOT NULL,
    blue_result INTEGER, -- 1 = win, 0 = loss
    total_kills INTEGER, -- combined kills in the game
    FOREIGN KEY (blue_team) REFERENCES teams(teamname),
    FOREIGN KEY (red_team) REFERENCES teams(teamname)
);
```

### Table: `player_games`
One row per player per game. This is the primary analysis table.
```sql
CREATE TABLE player_games (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id TEXT NOT NULL,
    playername TEXT NOT NULL,
    teamname TEXT NOT NULL,
    league TEXT NOT NULL,
    date DATE NOT NULL,
    patch TEXT,
    side TEXT, -- Blue/Red
    position TEXT NOT NULL, -- top/jng/mid/bot/sup
    champion TEXT,
    result INTEGER, -- 1 = win, 0 = loss
    kills INTEGER,
    deaths INTEGER,
    assists INTEGER,
    total_cs INTEGER,
    gamelength INTEGER, -- seconds
    dpm REAL,
    damageshare REAL,
    visionscore REAL,
    vspm REAL,
    killparticipation REAL,
    goldat15 REAL,
    csat15 REAL,
    golddiffat15 REAL,
    csdiffat15 REAL,
    xpdiffat15 REAL,
    FOREIGN KEY (game_id) REFERENCES games(game_id),
    FOREIGN KEY (playername) REFERENCES players(playername)
);
```

### Table: `team_games`
One row per team per game. Used for pace and opponent adjustments.
```sql
CREATE TABLE team_games (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id TEXT NOT NULL,
    teamname TEXT NOT NULL,
    league TEXT NOT NULL,
    date DATE NOT NULL,
    patch TEXT,
    side TEXT,
    result INTEGER,
    gamelength INTEGER,
    kills INTEGER, -- team total kills
    deaths INTEGER, -- team total deaths (= opponent kills)
    towers INTEGER,
    dragons INTEGER,
    barons INTEGER,
    heralds INTEGER,
    team_kpm REAL, -- team kills per minute
    firsttower INTEGER,
    firstdragon INTEGER,
    firstbaron INTEGER,
    FOREIGN KEY (game_id) REFERENCES games(game_id)
);
```

### Table: `picks`
Tracks user's picks and outcomes for P/L tracking.
```sql
CREATE TABLE picks (
    pick_id INTEGER PRIMARY KEY AUTOINCREMENT,
    date_entered DATE NOT NULL,
    match_date DATE,
    league TEXT,
    playername TEXT NOT NULL,
    stat TEXT NOT NULL, -- 'kills', 'deaths', 'assists', 'cs'
    line REAL NOT NULL, -- Underdog's line (e.g., 4.5)
    direction TEXT NOT NULL, -- 'over' or 'under'
    model_projection REAL NOT NULL,
    model_probability REAL NOT NULL, -- probability of hitting
    edge REAL NOT NULL, -- model_prob - implied_prob
    confidence TEXT NOT NULL, -- 'high', 'medium', 'low'
    actual_result REAL, -- NULL until game is played, then actual stat
    hit INTEGER, -- NULL until resolved, then 1/0
    parlay_group_id INTEGER, -- optional grouping for multi-pick parlays
    notes TEXT
);
```

### Table: `parlay_groups`
Groups individual picks into parlays for P/L tracking.
```sql
CREATE TABLE parlay_groups (
    parlay_id INTEGER PRIMARY KEY AUTOINCREMENT,
    date_entered DATE NOT NULL,
    entry_fee REAL, -- dollar amount risked
    potential_payout REAL,
    actual_payout REAL, -- NULL until resolved
    status TEXT DEFAULT 'pending', -- 'pending', 'won', 'lost', 'partial'
    num_picks INTEGER,
    num_hits INTEGER -- NULL until resolved
);
```

---

## Data Refresh Process

### `refresh_data.py`
1. Downloads latest CSV files from Oracle's Elixir
2. Parses CSV rows, handling encoding and field variations
3. Upserts into SQLite tables (skip duplicates by gameid)
4. Updates `players` and `teams` tables with latest info
5. Logs refresh timestamp and row counts
6. Should be idempotent — safe to run multiple times

### Refresh Frequency
- Run before each betting session
- Oracle's Elixir typically updates within 24-48 hours of matches being played
- For smaller leagues, data may lag slightly longer

### Data Quality Notes
- Oracle's Elixir field names can vary slightly across seasons — the ingestion script must handle common variations
- Some fields may be null for older data or certain leagues
- `gamelength` is in seconds in some exports, minutes in others — normalize to seconds
- Patch format varies (e.g., "14.10" vs "14.10.1") — normalize to major.minor
- Player names are case-sensitive and may include unicode characters
- Same player name across different leagues could theoretically be different people — use team + league as disambiguation when needed
