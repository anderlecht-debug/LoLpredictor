"""Stage 1: Player baseline calculation using exponentially weighted rolling averages."""

import numpy as np
from database.queries import get_player_recent_games


def calculate_baseline(playername, settings):
    """Calculate exponentially weighted baseline stats for a player.

    Returns dict with mean and std for each stat, plus game count and confidence info.
    """
    lookback = int(settings.get('LOOKBACK_WINDOW', 15))
    decay = settings.get('DECAY_FACTOR', 0.85)
    min_games = int(settings.get('MIN_GAMES_PLAYER', 5))

    games = get_player_recent_games(playername, limit=lookback)

    if not games:
        return None

    game_count = len(games)
    low_confidence = game_count < min_games

    # Calculate weights (most recent game = index 0 = highest weight)
    weights = np.array([decay ** i for i in range(game_count)])

    stats = {}
    for stat in ['kills', 'deaths', 'assists']:
        values = np.array([g[stat] for g in games if g[stat] is not None], dtype=float)
        if len(values) == 0:
            stats[stat] = {'mean': 0, 'std': 1, 'values': []}
            continue

        w = weights[:len(values)]
        w_sum = w.sum()

        mean = np.sum(w * values) / w_sum
        variance = np.sum(w * (values - mean) ** 2) / w_sum
        std = np.sqrt(variance) if variance > 0 else 0.5

        if low_confidence:
            std *= settings.get('LOW_CONF_STD_MULTIPLIER', 1.5)

        stats[stat] = {'mean': float(mean), 'std': float(std), 'values': values.tolist()}

    # CS: model as CS per minute to decouple from game length
    cs_values = []
    for g in games:
        if g['total_cs'] is not None and g['gamelength'] and g['gamelength'] > 0:
            cspm = g['total_cs'] / (g['gamelength'] / 60.0)
            cs_values.append(cspm)

    if cs_values:
        cs_arr = np.array(cs_values, dtype=float)
        w = weights[:len(cs_arr)]
        w_sum = w.sum()
        cs_mean = np.sum(w * cs_arr) / w_sum
        cs_var = np.sum(w * (cs_arr - cs_mean) ** 2) / w_sum
        cs_std = np.sqrt(cs_var) if cs_var > 0 else 0.5

        if low_confidence:
            cs_std *= settings.get('LOW_CONF_STD_MULTIPLIER', 1.5)

        stats['cspm'] = {'mean': float(cs_mean), 'std': float(cs_std)}

        # Also store raw CS stats for reference
        raw_cs = np.array([g['total_cs'] for g in games if g['total_cs'] is not None], dtype=float)
        w_cs = weights[:len(raw_cs)]
        stats['cs'] = {
            'mean': float(np.sum(w_cs * raw_cs) / w_cs.sum()),
            'std': float(np.sqrt(np.sum(w_cs * (raw_cs - np.sum(w_cs * raw_cs) / w_cs.sum()) ** 2) / w_cs.sum())) or 10.0,
        }
        if low_confidence:
            stats['cs']['std'] *= settings.get('LOW_CONF_STD_MULTIPLIER', 1.5)
    else:
        stats['cspm'] = {'mean': 7.0, 'std': 1.0}
        stats['cs'] = {'mean': 200, 'std': 30}

    return {
        'stats': stats,
        'game_count': game_count,
        'low_confidence': low_confidence,
        'position': games[0]['position'] if games else None,
        'team': games[0]['teamname'] if games else None,
        'league': games[0]['league'] if games else None,
    }
