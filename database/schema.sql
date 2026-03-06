-- LoL Props Lab Database Schema

CREATE TABLE IF NOT EXISTS players (
    player_id INTEGER PRIMARY KEY AUTOINCREMENT,
    playername TEXT NOT NULL,
    current_team TEXT,
    current_league TEXT,
    current_position TEXT,
    last_updated DATE,
    UNIQUE(playername)
);

CREATE TABLE IF NOT EXISTS teams (
    team_id INTEGER PRIMARY KEY AUTOINCREMENT,
    teamname TEXT NOT NULL,
    current_league TEXT,
    last_updated DATE,
    UNIQUE(teamname)
);

CREATE TABLE IF NOT EXISTS games (
    game_id TEXT PRIMARY KEY,
    date DATE NOT NULL,
    league TEXT NOT NULL,
    split TEXT,
    playoffs INTEGER DEFAULT 0,
    patch TEXT,
    gamelength INTEGER,
    blue_team TEXT NOT NULL,
    red_team TEXT NOT NULL,
    blue_result INTEGER,
    total_kills INTEGER,
    FOREIGN KEY (blue_team) REFERENCES teams(teamname),
    FOREIGN KEY (red_team) REFERENCES teams(teamname)
);

CREATE TABLE IF NOT EXISTS player_games (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id TEXT NOT NULL,
    playername TEXT NOT NULL,
    teamname TEXT NOT NULL,
    league TEXT NOT NULL,
    date DATE NOT NULL,
    patch TEXT,
    side TEXT,
    position TEXT NOT NULL,
    champion TEXT,
    result INTEGER,
    kills INTEGER,
    deaths INTEGER,
    assists INTEGER,
    total_cs INTEGER,
    gamelength INTEGER,
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

CREATE TABLE IF NOT EXISTS team_games (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id TEXT NOT NULL,
    teamname TEXT NOT NULL,
    league TEXT NOT NULL,
    date DATE NOT NULL,
    patch TEXT,
    side TEXT,
    result INTEGER,
    gamelength INTEGER,
    kills INTEGER,
    deaths INTEGER,
    towers INTEGER,
    dragons INTEGER,
    barons INTEGER,
    heralds INTEGER,
    team_kpm REAL,
    firsttower INTEGER,
    firstdragon INTEGER,
    firstbaron INTEGER,
    FOREIGN KEY (game_id) REFERENCES games(game_id)
);

CREATE TABLE IF NOT EXISTS upcoming_matches (
    match_id INTEGER PRIMARY KEY AUTOINCREMENT,
    league TEXT NOT NULL,
    team_a TEXT NOT NULL,
    team_b TEXT NOT NULL,
    match_date DATE,
    format TEXT DEFAULT 'Bo1',
    props_per_game INTEGER DEFAULT 1,
    status TEXT DEFAULT 'upcoming',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (team_a) REFERENCES teams(teamname),
    FOREIGN KEY (team_b) REFERENCES teams(teamname)
);

CREATE TABLE IF NOT EXISTS entered_lines (
    line_id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id INTEGER NOT NULL,
    playername TEXT NOT NULL,
    stat TEXT NOT NULL,
    line_value REAL NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (match_id) REFERENCES upcoming_matches(match_id)
);

CREATE TABLE IF NOT EXISTS picks (
    pick_id INTEGER PRIMARY KEY AUTOINCREMENT,
    date_entered DATE NOT NULL,
    match_date DATE,
    league TEXT,
    playername TEXT NOT NULL,
    stat TEXT NOT NULL,
    line REAL NOT NULL,
    direction TEXT NOT NULL,
    model_projection REAL NOT NULL,
    model_probability REAL NOT NULL,
    edge REAL NOT NULL,
    confidence TEXT NOT NULL,
    actual_result REAL,
    hit INTEGER,
    parlay_group_id INTEGER,
    notes TEXT,
    FOREIGN KEY (parlay_group_id) REFERENCES parlay_groups(parlay_id)
);

CREATE TABLE IF NOT EXISTS parlay_groups (
    parlay_id INTEGER PRIMARY KEY AUTOINCREMENT,
    date_entered DATE NOT NULL,
    entry_fee REAL,
    potential_payout REAL,
    actual_payout REAL,
    status TEXT DEFAULT 'pending',
    num_picks INTEGER,
    num_hits INTEGER
);

CREATE TABLE IF NOT EXISTS model_settings (
    key TEXT PRIMARY KEY,
    value REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS refresh_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    rows_processed INTEGER,
    status TEXT,
    message TEXT
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_player_games_player ON player_games(playername, date DESC);
CREATE INDEX IF NOT EXISTS idx_player_games_team ON player_games(teamname, date DESC);
CREATE INDEX IF NOT EXISTS idx_player_games_league ON player_games(league, date DESC);
CREATE INDEX IF NOT EXISTS idx_player_games_position ON player_games(position);
CREATE INDEX IF NOT EXISTS idx_player_games_game ON player_games(game_id);
CREATE INDEX IF NOT EXISTS idx_team_games_team ON team_games(teamname, date DESC);
CREATE INDEX IF NOT EXISTS idx_team_games_game ON team_games(game_id);
CREATE INDEX IF NOT EXISTS idx_games_league ON games(league, date DESC);
CREATE INDEX IF NOT EXISTS idx_picks_date ON picks(date_entered DESC);
