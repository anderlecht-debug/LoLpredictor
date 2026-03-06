"""Main projection pipeline - runs all 7 stages for a player in a match."""

from engine.baseline import calculate_baseline
from engine.opponent import calculate_opponent_factor
from engine.pace import calculate_pace_factor
from engine.gamelength import calculate_gamelength_factor
from engine.winprob import calculate_win_probability, apply_win_modifier
from engine.distributions import calculate_probability
from engine.confidence import assess_confidence
from database.db import get_settings
from database.queries import get_team_players, get_opponent_position_stats


def project_match(team_a, team_b, league, settings=None):
    """Run projections for all players in a match.

    Returns list of player projection dicts.
    """
    if settings is None:
        settings = get_settings()

    # Pre-calculate shared match factors
    pace_factors = calculate_pace_factor(team_a, team_b, league, settings)
    gl_factors = calculate_gamelength_factor(team_a, team_b, league, settings)
    win_probs = calculate_win_probability(team_a, team_b, settings)

    # Get players for each team
    team_a_players = get_team_players(team_a)
    team_b_players = get_team_players(team_b)

    results = []

    # Project each player
    for players, team, opp_team, win_prob in [
        (team_a_players, team_a, team_b, win_probs['team_a']),
        (team_b_players, team_b, team_a, win_probs['team_b']),
    ]:
        for player_info in players:
            projection = project_player(
                player_info['playername'],
                player_info['position'],
                team, opp_team, league,
                win_prob, pace_factors, gl_factors, settings
            )
            if projection:
                results.append(projection)

    return {
        'players': results,
        'match_context': {
            'pace': {
                'label': pace_factors.get('pace_label', 'MEDIUM'),
                'combined_kpm': pace_factors.get('combined_kpm'),
                'league_avg_kpm': pace_factors.get('league_avg_kpm'),
            },
            'game_length': {
                'expected_minutes': gl_factors.get('expected_minutes'),
                'league_avg_minutes': gl_factors.get('league_avg_minutes'),
            },
            'win_probability': win_probs,
        },
    }


def project_player(playername, position, team, opponent, league,
                    win_prob, pace_factors, gl_factors, settings):
    """Run the full 7-stage pipeline for a single player."""

    # Stage 1: Baseline
    baseline = calculate_baseline(playername, settings)
    if baseline is None:
        return None

    # Stage 2: Opponent adjustment
    opp_factors = calculate_opponent_factor(opponent, position, league, settings)

    # Count opponent games for confidence
    opp_games = get_opponent_position_stats(opponent, position)
    opp_game_count = len(opp_games) if opp_games else 0

    # Stage 3-5: Apply adjustments
    projections = {}
    for stat in ['kills', 'deaths', 'assists', 'cs']:
        if stat == 'cs':
            # Use CSPM baseline * expected game length
            cspm = baseline['stats'].get('cspm', {}).get('mean', 7.0)
            expected_minutes = gl_factors.get('expected_minutes', 30)

            # Stage 2: Opponent adjustment on CSPM
            cs_base = cspm * opp_factors.get('cs', 1.0)

            # Stage 3: Pace (CS not pace-dependent)
            # Stage 4: Convert CSPM to total CS using expected game length
            mean = cs_base * expected_minutes

            # Stage 5: Win probability modifier
            mean = apply_win_modifier(mean, win_prob, 'cs')

            # Standard deviation
            std = baseline['stats'].get('cs', {}).get('std', 30)
            std *= opp_factors.get('cs', 1.0)
            std *= gl_factors.get('cs', 1.0)
        else:
            # Stage 1: Get baseline
            mean = baseline['stats'].get(stat, {}).get('mean', 0)
            std = baseline['stats'].get(stat, {}).get('std', 1)

            # Stage 2: Opponent adjustment
            mean *= opp_factors.get(stat, 1.0)

            # Stage 3: Pace adjustment
            mean *= pace_factors.get(stat, 1.0)

            # Stage 4: Game length adjustment
            mean *= gl_factors.get(stat, 1.0)

            # Stage 5: Win probability modifier
            mean = apply_win_modifier(mean, win_prob, stat)

            # Adjust std by the same factors
            std *= abs(opp_factors.get(stat, 1.0))
            std *= abs(pace_factors.get(stat, 1.0))
            std *= abs(gl_factors.get(stat, 1.0))

        projections[stat] = {
            'mean': round(mean, 2),
            'std': round(std, 2),
        }

    # Confidence assessment
    confidence = assess_confidence(baseline['game_count'], opp_game_count, settings)

    return {
        'playername': playername,
        'position': baseline.get('position', position),
        'team': team,
        'opponent': opponent,
        'league': league,
        'projections': projections,
        'confidence': confidence,
        'game_count': baseline['game_count'],
    }


def calculate_edge_for_line(projection, stat, line_value):
    """Calculate edge for a specific line value.

    Returns edge calculation result dict.
    """
    proj = projection['projections'].get(stat)
    if not proj:
        return None

    probs = calculate_probability(proj['mean'], proj['std'], line_value, stat)

    if probs['p_over'] > probs['p_under']:
        direction = 'over'
        probability = probs['p_over']
    else:
        direction = 'under'
        probability = probs['p_under']

    edge = probability - 0.50

    return {
        'playername': projection['playername'],
        'team': projection['team'],
        'opponent': projection['opponent'],
        'league': projection['league'],
        'stat': stat,
        'line': line_value,
        'direction': direction,
        'projection': proj['mean'],
        'std': proj['std'],
        'probability': round(probability, 4),
        'edge': round(edge, 4),
        'confidence': projection['confidence'],
        'p_over': round(probs['p_over'], 4),
        'p_under': round(probs['p_under'], 4),
        'recommended': edge >= 0.05,
    }
