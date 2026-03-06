"""Stage 4: Game length adjustment."""

import numpy as np
from database.queries import get_team_recent_games, get_league_averages


def calculate_gamelength_factor(team_a, team_b, league, settings):
    """Calculate game length adjustment factors.

    Returns dict with factors per stat and expected game length info.
    """
    lookback = int(settings.get('LOOKBACK_WINDOW', 15))
    decay = settings.get('DECAY_FACTOR', 0.85)

    team_a_games = get_team_recent_games(team_a, limit=lookback)
    team_b_games = get_team_recent_games(team_b, limit=lookback)
    league_avgs = get_league_averages(league)

    if not league_avgs or league_avgs.get('avg_gamelength', 0) == 0:
        return {
            'kills': 1.0, 'deaths': 1.0, 'assists': 1.0, 'cs': 1.0,
            'expected_minutes': 30, 'league_avg_minutes': 30,
        }

    league_avg_gl = league_avgs['avg_gamelength']  # in seconds

    def weighted_gamelength(games):
        if not games:
            return league_avg_gl
        gl_vals = [g['gamelength'] for g in games if g['gamelength'] is not None and g['gamelength'] > 0]
        if not gl_vals:
            return league_avg_gl
        arr = np.array(gl_vals, dtype=float)
        w = np.array([decay ** i for i in range(len(arr))])
        return float(np.sum(w * arr) / w.sum())

    team_a_gl = weighted_gamelength(team_a_games)
    team_b_gl = weighted_gamelength(team_b_games)
    expected_gl = (team_a_gl + team_b_gl) / 2.0

    gl_ratio = expected_gl / league_avg_gl if league_avg_gl > 0 else 1.0

    gl_exp_cs = settings.get('GAMELENGTH_EXPONENT_CS', 1.0)
    gl_exp_kda = settings.get('GAMELENGTH_EXPONENT_KDA', 0.5)

    return {
        'kills': float(gl_ratio ** gl_exp_kda),
        'deaths': float(gl_ratio ** gl_exp_kda),
        'assists': float(gl_ratio ** gl_exp_kda),
        'cs': float(gl_ratio ** gl_exp_cs),
        'expected_minutes': float(expected_gl / 60.0),
        'league_avg_minutes': float(league_avg_gl / 60.0),
    }
