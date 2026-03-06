"""Stage 6-7: Distribution modeling and over/under probability calculation."""

import math
import numpy as np
from scipy.stats import nbinom, norm


def calculate_probability(mean, std, line, stat):
    """Calculate P(over) and P(under) for a given line.

    Uses Negative Binomial for kills/deaths/assists, Normal for CS.
    """
    if mean <= 0:
        mean = 0.1
    if std <= 0:
        std = 0.5

    variance = std ** 2

    if stat == 'cs':
        # Normal distribution for CS
        p_over = float(1 - norm.cdf(line, loc=mean, scale=std))
        p_under = float(norm.cdf(line, loc=mean, scale=std))
    else:
        # Negative Binomial for kills, deaths, assists
        if variance <= mean:
            # Variance must be > mean for NB; if not, inflate slightly
            variance = mean * 1.1

        # NB parameters
        r = (mean ** 2) / (variance - mean)
        p = mean / variance

        # Ensure valid parameters
        r = max(r, 0.1)
        p = max(min(p, 0.999), 0.001)

        # For X.5 lines: P(over 4.5) = P(X >= 5) = 1 - P(X <= 4)
        line_floor = int(math.floor(line))
        p_under = float(nbinom.cdf(line_floor, r, p))
        p_over = float(1 - p_under)

    return {
        'p_over': p_over,
        'p_under': p_under,
        'mean': float(mean),
        'std': float(std),
        'distribution': 'normal' if stat == 'cs' else 'negative_binomial',
    }
