"""Parses and normalizes Oracle's Elixir CSV data."""

import pandas as pd
import numpy as np


# Column name mapping to handle variations across seasons
COLUMN_MAPPING = {
    'gameid': 'gameid',
    'game_id': 'gameid',
    'league': 'league',
    'split': 'split',
    'playoffs': 'playoffs',
    'date': 'date',
    'patch': 'patch',
    'side': 'side',
    'position': 'position',
    'playername': 'playername',
    'player': 'playername',
    'teamname': 'teamname',
    'team': 'teamname',
    'champion': 'champion',
    'kills': 'kills',
    'deaths': 'deaths',
    'assists': 'assists',
    'total cs': 'total_cs',
    'totcs': 'total_cs',
    'total_cs': 'total_cs',
    'minionkills': 'minionkills',
    'monsterkills': 'monsterkills',
    'gamelength': 'gamelength',
    'result': 'result',
    'dpm': 'dpm',
    'damageshare': 'damageshare',
    'visionscore': 'visionscore',
    'vspm': 'vspm',
    'killparticipation': 'killparticipation',
    'goldat15': 'goldat15',
    'csat15': 'csat15',
    'golddiffat15': 'golddiffat15',
    'csdiffat15': 'csdiffat15',
    'xpdiffat15': 'xpdiffat15',
    'totalgold': 'totalgold',
    'team kpm': 'team_kpm',
    'teamkpm': 'team_kpm',
    'towers': 'towers',
    'dragons': 'dragons',
    'barons': 'barons',
    'heralds': 'heralds',
    'firsttower': 'firsttower',
    'firstdragon': 'firstdragon',
    'firstbaron': 'firstbaron',
    'firstblood': 'firstblood',
}


def normalize_columns(df):
    """Normalize column names to standard format."""
    df.columns = df.columns.str.lower().str.strip()
    rename_map = {}
    for col in df.columns:
        if col in COLUMN_MAPPING:
            rename_map[col] = COLUMN_MAPPING[col]
    df = df.rename(columns=rename_map)
    return df


def normalize_patch(patch_val):
    """Normalize patch to major.minor format."""
    if pd.isna(patch_val):
        return None
    patch_str = str(patch_val).strip()
    parts = patch_str.split('.')
    if len(parts) >= 2:
        return f"{parts[0]}.{parts[1]}"
    return patch_str


def normalize_gamelength(val):
    """Normalize game length to seconds."""
    if pd.isna(val):
        return None
    val = float(val)
    # If value is small, it's likely in minutes
    if val < 100:
        return int(val * 60)
    return int(val)


def parse_csv(filepath):
    """Parse an Oracle's Elixir CSV file and return normalized DataFrames."""
    print(f"Parsing {filepath}...")
    df = pd.read_csv(filepath, low_memory=False)

    # Validate this is actually a CSV with expected data (not HTML)
    if len(df.columns) < 5:
        raise ValueError(f"File appears invalid: only {len(df.columns)} columns found. "
                         "It may be HTML instead of CSV. Check the download URL.")

    df = normalize_columns(df)

    # Check for required position column
    if 'position' not in df.columns:
        # Print available columns for debugging
        print(f"  Available columns: {list(df.columns[:20])}...")
        raise ValueError(
            f"'position' column not found. Available columns: {list(df.columns)}"
        )

    # Normalize patch
    if 'patch' in df.columns:
        df['patch'] = df['patch'].apply(normalize_patch)

    # Normalize game length
    if 'gamelength' in df.columns:
        df['gamelength'] = df['gamelength'].apply(normalize_gamelength)

    # Normalize date
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], errors='coerce').dt.strftime('%Y-%m-%d')

    # Normalize position
    if 'position' in df.columns:
        df['position'] = df['position'].str.lower().str.strip()

    # Calculate total_cs if not present
    if 'total_cs' not in df.columns:
        if 'minionkills' in df.columns and 'monsterkills' in df.columns:
            df['total_cs'] = df['minionkills'].fillna(0) + df['monsterkills'].fillna(0)

    # Ensure numeric columns
    numeric_cols = ['kills', 'deaths', 'assists', 'total_cs', 'gamelength',
                    'result', 'dpm', 'damageshare', 'visionscore', 'vspm',
                    'killparticipation', 'goldat15', 'csat15', 'golddiffat15',
                    'csdiffat15', 'xpdiffat15', 'playoffs']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Split into player rows and team rows
    player_df = df[df['position'].isin(['top', 'jng', 'mid', 'bot', 'sup'])].copy()
    team_df = df[df['position'] == 'team'].copy()

    print(f"Parsed {len(player_df)} player rows and {len(team_df)} team rows")
    return player_df, team_df
