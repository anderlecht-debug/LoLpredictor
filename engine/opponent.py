"""Stage 2: Opponent adjustments."""

import numpy as np
from database.queries import get_opponent_position_stats, get_league_position_averages


def calculate_opponent_factor(opponent_team, position, league, settings):
    """Calculate how the opponent affects stats for a given position.

    Returns dict of adjustment factors per stat.
    """
    lookback = int(settings.get('LOOKBACK_WINDOW', 15))
    decay = settings.get('DECAY_FACTOR', 0.85)
    min_games = int(settings.get('MIN_GAMES_OPPONENT', 5))

    # Get stats the opponent allows to this position
    opp_games = get_opponent_position_stats(opponent_team, position, limit=lookback)

    # Get league averages for this position
    league_avgs = get_league_position_averages(league, position)

    if not league_avgs or league_avgs.get('game_count', 0) == 0:
        return {'kills': 1.0, 'deaths': 1.0, 'assists': 1.0, 'cs': 1.0}

    if not opp_games or len(opp_games) < min_games:
        # Not enough opponent data, shrink toward league average (factor = 1.0)
        shrinkage = len(opp_games) / min_games if opp_games else 0
        factors = {}
        for stat in ['kills', 'deaths', 'assists']:
            if opp_games:
                opp_avg = np.mean([g[stat] for g in opp_games if g[stat] is not None])
                league_avg = league_avgs.get(f'avg_{stat}', opp_avg)
                if league_avg and league_avg > 0:
                    raw_factor = opp_avg / league_avg
                    factors[stat] = 1.0 + shrinkage * (raw_factor - 1.0)
                else:
                    factors[stat] = 1.0
            else:
                factors[stat] = 1.0
        factors['cs'] = 1.0
        return factors

    # Calculate decay-weighted opponent stats
    weights = np.array([decay ** i for i in range(len(opp_games))])
    w_sum = weights.sum()

    factors = {}
    for stat in ['kills', 'deaths', 'assists']:
        values = np.array([g[stat] for g in opp_games if g[stat] is not None], dtype=float)
        if len(values) == 0:
            factors[stat] = 1.0
            continue

        w = weights[:len(values)]
        opp_avg = np.sum(w * values) / w.sum()
        league_avg = league_avgs.get(f'avg_{stat}')

        if league_avg and league_avg > 0:
            factors[stat] = float(opp_avg / league_avg)
        else:
            factors[stat] = 1.0

    # CS opponent factor (based on CSPM allowed)
    cs_values = []
    for g in opp_games:
        if g['total_cs'] is not None and g['gamelength'] and g['gamelength'] > 0:
            cs_values.append(g['total_cs'] / (g['gamelength'] / 60.0))
    if cs_values:
        w = weights[:len(cs_values)]
        opp_cspm = np.sum(w * np.array(cs_values)) / w.sum()
        league_cspm = league_avgs.get('avg_cspm')
        factors['cs'] = float(opp_cspm / league_cspm) if league_cspm and league_cspm > 0 else 1.0
    else:
        factors['cs'] = 1.0

    return factors
