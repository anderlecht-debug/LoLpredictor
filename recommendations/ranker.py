"""Pick ranking and sorting."""

from config import CONFIDENCE_MULTIPLIER, LEAGUE_TIERS, TIER_ORDER


def rank_picks(picks):
    """Rank a list of picks by expected value.

    Each pick should have: edge, confidence, league, game_count, stat.
    Returns sorted list with ranking_score added.
    """
    for pick in picks:
        conf_mult = CONFIDENCE_MULTIPLIER.get(pick.get('confidence', 'low'), 0.5)
        pick['ranking_score'] = round(pick.get('edge', 0) * conf_mult, 4)

    # Sort by ranking_score descending, with tiebreakers
    picks.sort(key=lambda p: (
        -p.get('ranking_score', 0),
        TIER_ORDER.get(LEAGUE_TIERS.get(p.get('league', ''), 'C'), 3),
        -p.get('game_count', 0),
        _stat_variance_order(p.get('stat', '')),
    ))

    return picks


def _stat_variance_order(stat):
    """Lower number = lower variance = preferred in tiebreak."""
    return {'cs': 0, 'kills': 1, 'assists': 2, 'deaths': 3}.get(stat, 4)
