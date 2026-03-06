"""Stage 3: Pace adjustment based on expected combined kills per minute."""

import numpy as np
from database.queries import get_team_recent_games, get_league_averages


def calculate_pace_factor(team_a, team_b, league, settings):
    """Calculate pace adjustment factor for the matchup.

    Returns dict with pace factors for each stat type and raw pace info.
    """
    lookback = int(settings.get('LOOKBACK_WINDOW', 15))
    decay = settings.get('DECAY_FACTOR', 0.85)

    team_a_games = get_team_recent_games(team_a, limit=lookback)
    team_b_games = get_team_recent_games(team_b, limit=lookback)
    league_avgs = get_league_averages(league)

    if not league_avgs or league_avgs.get('avg_kpm', 0) == 0:
        return {
            'kills': 1.0, 'deaths': 1.0, 'assists': 1.0, 'cs': 1.0,
            'combined_kpm': None, 'league_avg_kpm': None,
        }

    league_avg_kpm = league_avgs['avg_kpm']

    def weighted_kpm(games):
        if not games:
            return league_avg_kpm
        kpm_vals = [g['team_kpm'] for g in games if g['team_kpm'] is not None]
        if not kpm_vals:
            return league_avg_kpm
        arr = np.array(kpm_vals, dtype=float)
        w = np.array([decay ** i for i in range(len(arr))])
        return float(np.sum(w * arr) / w.sum())

    team_a_kpm = weighted_kpm(team_a_games)
    team_b_kpm = weighted_kpm(team_b_games)
    combined_kpm = (team_a_kpm + team_b_kpm) / 2.0

    pace_raw = combined_kpm / league_avg_kpm if league_avg_kpm > 0 else 1.0

    pace_exp_kills = settings.get('PACE_EXPONENT_KILLS', 1.0)
    pace_exp_assists = settings.get('PACE_EXPONENT_ASSISTS', 0.8)

    return {
        'kills': float(pace_raw ** pace_exp_kills),
        'deaths': float(pace_raw ** pace_exp_kills),
        'assists': float(pace_raw ** pace_exp_assists),
        'cs': 1.0,  # CS not pace-dependent
        'combined_kpm': float(combined_kpm),
        'league_avg_kpm': float(league_avg_kpm),
        'pace_label': 'HIGH' if pace_raw > 1.1 else ('LOW' if pace_raw < 0.9 else 'MEDIUM'),
    }
