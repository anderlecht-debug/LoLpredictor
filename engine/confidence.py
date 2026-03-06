"""Confidence level assessment for projections."""


def assess_confidence(player_game_count, opponent_game_count=None, settings=None):
    """Assess confidence level of a projection.

    Returns 'high', 'medium', or 'low'.
    """
    if player_game_count >= 15 and (opponent_game_count is None or opponent_game_count >= 10):
        return 'high'
    elif player_game_count >= 8 and (opponent_game_count is None or opponent_game_count >= 5):
        return 'medium'
    else:
        return 'low'
