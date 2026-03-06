"""Correlation detection between picks."""


def detect_correlations(picks):
    """Detect correlated picks and add correlation flags.

    Picks from the same game that share direction tendencies are correlated.
    """
    # Group picks by match (team vs opponent)
    match_groups = {}
    for pick in picks:
        match_key = tuple(sorted([pick.get('team', ''), pick.get('opponent', '')]))
        if match_key not in match_groups:
            match_groups[match_key] = []
        match_groups[match_key].append(pick)

    # Flag correlations
    for pick in picks:
        match_key = tuple(sorted([pick.get('team', ''), pick.get('opponent', '')]))
        group = match_groups.get(match_key, [])

        correlated_with = []
        for other in group:
            if other is pick:
                continue

            # Same team, same direction on kills/assists = positively correlated
            if (other.get('team') == pick.get('team') and
                other.get('direction') == pick.get('direction') and
                pick.get('stat') in ('kills', 'assists') and
                other.get('stat') in ('kills', 'assists')):
                correlated_with.append({
                    'player': other['playername'],
                    'stat': other['stat'],
                    'type': 'positive',
                })

            # Kill over for one player correlates with death over for opponent
            if (other.get('team') != pick.get('team') and
                pick.get('stat') == 'kills' and pick.get('direction') == 'over' and
                other.get('stat') == 'deaths' and other.get('direction') == 'over'):
                correlated_with.append({
                    'player': other['playername'],
                    'stat': other['stat'],
                    'type': 'positive',
                })

        pick['correlations'] = correlated_with
        pick['is_independent'] = len(correlated_with) == 0

    return picks


def find_independent_picks(picks, count=3):
    """Find the top N independent picks (from different games)."""
    seen_matches = set()
    independent = []

    for pick in picks:
        match_key = tuple(sorted([pick.get('team', ''), pick.get('opponent', '')]))
        if match_key not in seen_matches:
            independent.append(pick)
            seen_matches.add(match_key)
        if len(independent) >= count:
            break

    return independent


def find_correlated_stacks(picks):
    """Find groups of correlated picks from the same game."""
    match_groups = {}
    for pick in picks:
        match_key = tuple(sorted([pick.get('team', ''), pick.get('opponent', '')]))
        if match_key not in match_groups:
            match_groups[match_key] = []
        match_groups[match_key].append(pick)

    stacks = []
    for match_key, group in match_groups.items():
        if len(group) >= 2:
            stacks.append({
                'match': f"{match_key[0]} vs {match_key[1]}",
                'picks': group,
                'avg_edge': sum(p.get('edge', 0) for p in group) / len(group),
            })

    stacks.sort(key=lambda s: -s['avg_edge'])
    return stacks
