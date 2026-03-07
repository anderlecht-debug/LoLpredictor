"""Configuration and model parameters for LoL Props Lab."""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
CSV_CACHE_DIR = os.path.join(DATA_DIR, 'csv_cache')
DB_PATH = os.environ.get('LOL_PROPS_DB_PATH', os.path.join(DATA_DIR, 'lol_props.db'))

# Ensure directories exist (skip if read-only filesystem like Vercel)
try:
    os.makedirs(CSV_CACHE_DIR, exist_ok=True)
except OSError:
    pass

# Oracle's Elixir data URL
ORACLE_ELIXIR_URL = 'https://oracleselixir.com/stats/players/byTournament'

# Model parameters (defaults)
DEFAULT_PARAMS = {
    'LOOKBACK_WINDOW': 15,
    'DECAY_FACTOR': 0.85,
    'MIN_GAMES_PLAYER': 5,
    'MIN_GAMES_OPPONENT': 5,
    'PACE_EXPONENT_KILLS': 1.0,
    'PACE_EXPONENT_ASSISTS': 0.8,
    'GAMELENGTH_EXPONENT_CS': 1.0,
    'GAMELENGTH_EXPONENT_KDA': 0.5,
    'LOW_CONF_STD_MULTIPLIER': 1.5,
    'EDGE_THRESHOLD_RECOMMEND': 0.05,
    'EDGE_THRESHOLD_HIGH_CONF': 0.10,
}

# Win/loss stat modifiers (starting points, can be recalibrated from data)
WIN_MODIFIER = {
    'kills': 1.35,
    'deaths': 0.65,
    'assists': 1.30,
    'cs': 1.08,
}

LOSS_MODIFIER = {
    'kills': 0.70,
    'deaths': 1.30,
    'assists': 0.75,
    'cs': 0.93,
}

# Confidence multipliers for ranking
CONFIDENCE_MULTIPLIER = {
    'high': 1.0,
    'medium': 0.75,
    'low': 0.5,
}

# League tiers
LEAGUE_TIERS = {
    'LCK': 'S', 'LPL': 'S',
    'LEC': 'A', 'LCS': 'A',
    'PCS': 'B', 'VCS': 'B', 'CBLOL': 'B',
    'LLA': 'C', 'LJL': 'C', 'LCO': 'C',
    'MSI': 'Special', 'Worlds': 'Special',
}

TIER_ORDER = {'S': 0, 'A': 1, 'B': 2, 'C': 3, 'Special': 1}

# Minimum game length in seconds to exclude remakes
MIN_GAME_LENGTH = 900
