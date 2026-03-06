# Recommendation Engine

## Overview
The recommendation engine compares the projection engine's output (projected stat distributions) against user-entered Underdog Fantasy lines to identify profitable picks. It calculates edge, ranks picks, and suggests optimal parlay construction.

## Edge Calculation

### Core Formula
```
model_probability = P(over) or P(under) from projection engine
implied_probability = 0.50  (Underdog pick'ems are effectively 50/50 implied)
edge = model_probability - implied_probability
```

**Why 0.50 implied:** Underdog Fantasy pick'ems are structured as higher/lower choices. While Underdog builds margin into the lines themselves (by setting the line slightly in their favor), each pick is fundamentally priced at even odds. The edge comes from finding lines where the true probability significantly deviates from 50%.

### Edge Classification

| Edge | Label | Color | Action |
|------|-------|-------|--------|
| 10%+ | **Strong Edge** | Green | Highly recommended |
| 5-10% | **Moderate Edge** | Yellow-Green | Recommended |
| 3-5% | **Marginal Edge** | Yellow | Optional — consider for parlays if correlated with other strong picks |
| 0-3% | **No Edge** | Gray | Skip |
| Negative | **Wrong Side** | Red | The OTHER direction may have edge — check |

### Directional Recommendation
For each player/stat combination, the engine calculates both P(over) and P(under). It recommends whichever direction has the higher probability, but ONLY if that probability exceeds the edge threshold.

```python
p_over = calculate_over_probability(projection, line)
p_under = 1 - p_over

if p_over > p_under:
    direction = "OVER"
    edge = p_over - 0.50
else:
    direction = "UNDER"
    edge = p_under - 0.50

if edge >= EDGE_THRESHOLD_RECOMMEND:
    recommend = True
```

---

## Pick Ranking

Picks are ranked by **expected value**, not just raw edge. This accounts for the confidence level of the projection.

### Ranking Score
```
ranking_score = edge * confidence_multiplier

where confidence_multiplier:
    High confidence:   1.0
    Medium confidence:  0.75
    Low confidence:    0.5
```

This means a 7% edge high-confidence pick (score: 0.07) ranks above a 10% edge low-confidence pick (score: 0.05).

### Tiebreakers
When ranking scores are equal:
1. Prefer picks from higher-tier leagues (more reliable data)
2. Prefer picks with more games in the lookback window
3. Prefer picks on stats with lower variance (CS > kills > assists > deaths)

---

## Correlation Awareness

### Why It Matters
Underdog parlays require multiple picks. Correlated picks (e.g., two players from the same game going OVER on kills in what's projected to be a bloodbath) are not independent. This matters for bankroll management, though Underdog allows correlated parlays.

### Correlation Flags
The system flags when recommended picks are correlated:

**Positive correlations:**
- Multiple players from the same game — all kills/assists overs (or all unders) are correlated
- Players on the same team — kills and assists are directly linked
- Kill overs correlate with death overs for opposing players

**Negative correlations:**
- Kill over for Player A may correlate with death over for the same player's lane opponent

### Parlay Construction Guidance
The system should display:
- **Independent picks:** Picks from different games (true independent events)
- **Correlated stacks:** Groups of picks from the same game that all benefit from the same game environment (e.g., "high-kill game stack")
- **Suggested parlays:** Combine 2-3 highest-edge independent picks, or suggest a correlated stack if the game environment strongly favors it

---

## Best Picks Feed

### Aggregation
The "Best Picks" view collects all recommended picks across every match the user has entered lines for and presents them in a single ranked list.

### Display Fields
For each recommended pick:
| Field | Description |
|-------|-------------|
| Player | Player name |
| Team | Team abbreviation |
| Opponent | Opposing team |
| League | League code |
| Stat | kills/deaths/assists/cs |
| Line | Underdog's line (user-entered) |
| Direction | OVER or UNDER |
| Projection | Model's point estimate |
| Model Prob | Probability of hitting |
| Edge | Edge percentage |
| Confidence | High/Medium/Low |
| Rank Score | Combined ranking score |

### Filtering & Sorting
Users can filter by:
- League
- Stat type
- Minimum edge threshold
- Confidence level
- Game/match

Default sort: by ranking score (descending)

---

## Result Tracking

### Entering Results
After games are played, the user enters actual stat lines. The system:
1. Compares actual stats to the line
2. Marks each pick as hit (1) or miss (0)
3. Updates parlay group status
4. Calculates running P/L

### Metrics Tracked

**Overall Performance:**
- Total picks made
- Hit rate (% of picks that hit)
- Hit rate by confidence level
- Hit rate by stat type
- Hit rate by league
- Total entries, total payouts, net P/L
- ROI % (net P/L / total entries)

**Model Calibration:**
- Predicted probability vs actual hit rate (binned)
- Are 60% predictions hitting ~60%?
- Calibration curve visualization

**Edge Verification:**
- Do higher-edge picks actually hit more often?
- Hit rate bucketed by edge: 5-7%, 7-10%, 10%+

**Trend Analysis:**
- Rolling 7-day and 30-day hit rate
- P/L trend line
- Identifies if model is degrading (needs recalibration or data refresh)

### Alerts
The system should flag:
- If hit rate drops below 48% over last 50 picks (model may be miscalibrated)
- If a specific stat type is consistently underperforming (e.g., kill projections are off)
- If a specific league's projections are poor (data quality issue)
- When data hasn't been refreshed in 3+ days

---

## Bankroll Management Display

While not a full bankroll management system, the dashboard should display:
- Current session P/L
- Running total P/L
- Largest win / largest loss
- Current streak (wins/losses in a row)
- Suggested max parlays per day based on edge quality available

---

## Anti-Tilt Safeguards

The system includes subtle nudges:
- If user has entered 10+ picks in one session with average edge below 5%, display: "Consider being more selective — your average edge this session is only X%."
- If user is on a 5+ loss streak, display their overall track record to provide perspective
- Never recommend a pick solely because "it feels due" — all recommendations are purely mathematical
