"""Stage 5: Win probability modifier."""

import numpy as np
from database.queries import get_team_recent_games
from config import WIN_MODIFIER, LOSS_MODIFIER


def calculate_win_probability(team_a, team_b, settings):
    """Calculate win probability for each team.

    Uses win rate differential as a proxy.
    """
    lookback = int(settings.get('LOOKBACK_WINDOW', 15))
    decay = settings.get('DECAY_FACTOR', 0.85)

    def weighted_winrate(teamname):
        games = get_team_recent_games(teamname, limit=lookback)
        if not games:
            return 0.5
        results = [g['result'] for g in games if g['result'] is not None]
        if not results:
            return 0.5
        arr = np.array(results, dtype=float)
        w = np.array([decay ** i for i in range(len(arr))])
        return float(np.sum(w * arr) / w.sum())

    wr_a = weighted_winrate(team_a)
    wr_b = weighted_winrate(team_b)

    # Normalize to probabilities
    total = wr_a + wr_b
    if total == 0:
        return {'team_a': 0.5, 'team_b': 0.5}

    wp_a = wr_a / total
    wp_b = wr_b / total

    return {'team_a': float(wp_a), 'team_b': float(wp_b)}


def apply_win_modifier(projection, win_prob, stat):
    """Apply win/loss blended modifier to a projection.

    Returns adjusted projection value.
    """
    win_mod = WIN_MODIFIER.get(stat, 1.0)
    loss_mod = LOSS_MODIFIER.get(stat, 1.0)

    adjusted = (win_prob * projection * win_mod) + ((1 - win_prob) * projection * loss_mod)
    return float(adjusted)
