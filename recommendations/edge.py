"""Edge calculation for player props."""


def calculate_edge(model_probability):
    """Calculate edge given model probability.

    Underdog pick'ems are effectively 50/50 implied.
    """
    implied = 0.50
    return model_probability - implied


def classify_edge(edge):
    """Classify edge into a label."""
    if edge >= 0.10:
        return 'strong'
    elif edge >= 0.05:
        return 'moderate'
    elif edge >= 0.03:
        return 'marginal'
    elif edge >= 0:
        return 'none'
    else:
        return 'wrong_side'


def edge_color(edge):
    """Return color class for edge value."""
    cls = classify_edge(edge)
    return {
        'strong': 'edge-strong',
        'moderate': 'edge-moderate',
        'marginal': 'edge-marginal',
        'none': 'edge-none',
        'wrong_side': 'edge-wrong',
    }.get(cls, 'edge-none')
