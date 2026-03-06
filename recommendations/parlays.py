"""Parlay suggestion logic."""

from recommendations.correlations import find_independent_picks, find_correlated_stacks


def suggest_parlays(ranked_picks):
    """Generate parlay suggestions from ranked picks.

    Returns dict with independent parlay and correlated stack suggestions.
    """
    recommended = [p for p in ranked_picks if p.get('recommended', False)]

    # Best independent parlay (3 picks from different games)
    independent = find_independent_picks(recommended, count=3)

    # Best correlated stack
    stacks = find_correlated_stacks(recommended)
    best_stack = stacks[0] if stacks else None

    # Calculate combined probability estimate for independent parlay
    if independent:
        combined_prob = 1.0
        for pick in independent:
            combined_prob *= pick.get('probability', 0.5)
        independent_prob = combined_prob
    else:
        independent_prob = None

    return {
        'independent_parlay': {
            'picks': independent,
            'combined_probability': round(independent_prob, 4) if independent_prob else None,
        },
        'correlated_stack': best_stack,
        'all_stacks': stacks,
    }
