# Projection Engine

## Overview
The projection engine generates per-player, per-game stat projections for kills, deaths, assists, and CS. Each projection includes a point estimate (expected value) and a standard deviation estimate, which together allow us to calculate the probability of going over or under any given line.

## Projection Pipeline

For each player in an upcoming match, the engine runs through these stages in order:

### Stage 1: Player Baseline (Exponentially Weighted Rolling Average)

**What:** Calculate the player's recent average for each stat, with more recent games weighted more heavily.

**Method:** Exponential decay weighting over the last N games (default N=15).

```
Weight for game i (where i=0 is most recent):
    w_i = alpha^i, where alpha = 0.85

Weighted average:
    baseline = sum(w_i * stat_i) / sum(w_i)

Weighted standard deviation:
    std = sqrt(sum(w_i * (stat_i - baseline)^2) / sum(w_i))
```

**Parameters:**
- `LOOKBACK_WINDOW = 15` games
- `DECAY_FACTOR = 0.85` (most recent game ~3x weight of game 15)
- If player has fewer than 5 games, flag as "low confidence" and widen the standard deviation by 1.5x

**Rate stats vs counting stats:**
- Kills, deaths, assists are counting stats — use raw per-game values
- CS should be modeled as CS per minute × expected game length (see Stage 4)
- This avoids conflating game length variance with CS skill variance

---

### Stage 2: Opponent Adjustment

**What:** Adjust the player baseline based on how the opposing team performs against that position.

**Method:** Calculate how many kills/deaths/assists/CS per minute the opposing team allows to the specific position (top, jng, mid, bot, sup) relative to the league average.

```
opponent_position_avg = avg stat allowed by opponent to this position (last 15 games, decay-weighted)
league_position_avg = avg stat for this position across the league (last 30 days)

opponent_factor = opponent_position_avg / league_position_avg
```

**Application:**
```
adjusted_projection = player_baseline * opponent_factor
```

**Example:**
- A mid laner averages 4.5 kills/game (baseline)
- The opposing team allows 5.8 kills/game to enemy mid laners
- League average for mid laners is 4.2 kills/game
- Opponent factor = 5.8 / 4.2 = 1.38
- Adjusted projection = 4.5 * 1.38 = 6.21 kills

**Edge cases:**
- If opponent has <5 games of data for that position, blend toward league average (shrinkage)
- Weight recent opponent data more heavily (same decay factor)
- Use data from the current split/season only for opponent adjustments to avoid stale meta data

---

### Stage 3: Pace Adjustment

**What:** Account for expected game pace (fast/bloody games inflate stats, slow/controlled games suppress them).

**Method:** Calculate the expected combined kills per minute (KPM) for the matchup and compare to the league average.

```
team_a_kpm = team A's average kills per minute (last 15 games, decay-weighted)
team_b_kpm = team B's average kills per minute (last 15 games, decay-weighted)
expected_combined_kpm = (team_a_kpm + team_b_kpm) / 2

league_avg_combined_kpm = average combined KPM across the league

pace_factor = expected_combined_kpm / league_avg_combined_kpm
```

**Application to different stats:**
```
kills_adjusted *= pace_factor
deaths_adjusted *= pace_factor
assists_adjusted *= pace_factor^0.8  # assists scale slightly less than kills
cs_adjusted *= 1.0  # CS is less pace-dependent (handled by game length instead)
```

**Why this matters:** Two teams that average 1.2 combined KPM meeting each other will produce far more kills than a matchup between two teams averaging 0.6 KPM. This is one of the biggest sources of mispricing on Underdog.

---

### Stage 4: Game Length Adjustment

**What:** Adjust counting stats based on expected game duration.

**Method:**
```
team_a_avg_gamelength = team A's average game length in minutes (decay-weighted)
team_b_avg_gamelength = team B's average game length in minutes (decay-weighted)
expected_gamelength = (team_a_avg_gamelength + team_b_avg_gamelength) / 2

league_avg_gamelength = league average game length

gamelength_factor = expected_gamelength / league_avg_gamelength
```

**Application:**
```
# CS scales nearly linearly with game length
cs_adjusted *= gamelength_factor

# Kills/deaths/assists scale somewhat with game length but not linearly
# (many kills happen in mid-game fights, not evenly distributed)
kills_adjusted *= gamelength_factor^0.5
deaths_adjusted *= gamelength_factor^0.5
assists_adjusted *= gamelength_factor^0.5
```

---

### Stage 5: Win Probability Modifier

**What:** Players on the winning team systematically have higher kills, assists, and CS, and lower deaths. Adjusting for expected win probability improves projections.

**Method:** Calculate a simple win probability for each team using recent performance.

```
# Simple ELO-style rating based on recent results
# Or use win rate differential as a quick proxy:
team_a_winrate = team A's win rate (last 15 games, decay-weighted)
team_b_winrate = team B's win rate (last 15 games, decay-weighted)

# Normalize to probabilities
team_a_winprob = team_a_winrate / (team_a_winrate + team_b_winrate)
```

**Stat modifiers by win/loss (derived from historical averages):**
These multipliers represent how much a stat changes in wins vs losses:
```
WIN_MODIFIER = {
    'kills': 1.35,    # winners get ~35% more kills
    'deaths': 0.65,   # winners die ~35% less
    'assists': 1.30,  # winners get ~30% more assists
    'cs': 1.08        # winners get ~8% more CS (less affected)
}

LOSS_MODIFIER = {
    'kills': 0.70,
    'deaths': 1.30,
    'assists': 0.75,
    'cs': 0.93
}
```

**Application:**
```
# Blend win and loss expected stats by win probability
final_projection = (win_prob * adjusted_projection * WIN_MODIFIER[stat]) +
                   ((1 - win_prob) * adjusted_projection * LOSS_MODIFIER[stat])
```

**Important:** The win/loss modifiers should be calibrated from the actual data in the database, not hardcoded. The values above are reasonable starting points. The system should recalculate these from the database on each refresh.

---

### Stage 6: Standard Deviation & Distribution Modeling

**What:** Estimate the spread of outcomes around the projection to calculate over/under probabilities.

**Kills & Deaths Distribution:**
- Model as **Poisson-like** (discrete, non-negative, integer-valued)
- Use the weighted standard deviation from Stage 1, adjusted by the same factors
- For Poisson, variance ≈ mean, but in practice LoL stats are slightly overdispersed
- Use a **Negative Binomial distribution** which allows variance > mean:
  ```
  mean = final_projection
  variance = weighted_std^2 (from player's historical data, adjusted)
  ```

**CS Distribution:**
- Model as **Normal distribution** (CS counts are high enough for normality)
- Mean = final_projection
- Std = adjusted weighted standard deviation

**Assists Distribution:**
- Model as **Negative Binomial** (similar to kills, but higher mean for supports)

---

### Stage 7: Over/Under Probability Calculation

**What:** Given a projection (mean, std) and a line (e.g., 4.5 kills), calculate P(over) and P(under).

```python
# For Poisson/Negative Binomial stats (kills, deaths, assists):
from scipy.stats import nbinom

# Convert mean and variance to Negative Binomial parameters
r = mean^2 / (variance - mean)  # if variance > mean
p = mean / variance

P_over = 1 - nbinom.cdf(floor(line), r, p)
P_under = nbinom.cdf(floor(line), r, p)

# For CS (Normal distribution):
from scipy.stats import norm
P_over = 1 - norm.cdf(line, loc=mean, std=std)
P_under = norm.cdf(line, loc=mean, std=std)
```

**Handling the line value:**
- Underdog typically uses X.5 lines (e.g., 4.5 kills)
- For X.5 lines: P(over) = P(stat >= 5) for a 4.5 line
- If line is a whole number, handle push rules per Underdog's terms

---

## Projection Confidence Levels

Each projection gets a confidence rating based on data quality:

| Confidence | Criteria |
|-----------|----------|
| **High** | Player has 15+ recent games, opponent has 10+ games, same patch meta |
| **Medium** | Player has 8-14 games, or opponent data is thin (5-9 games) |
| **Low** | Player has <8 games, or new roster, or cross-patch with major changes |

Low confidence projections have their standard deviations widened by 1.5x, which naturally reduces the calculated edge and makes the system less likely to recommend those picks.

---

## Model Calibration

The system should track predicted probabilities vs actual outcomes to check calibration:
- If the model says "60% chance of over 4.5 kills," that should hit ~60% of the time
- Track calibration buckets: 50-55%, 55-60%, 60-65%, 65-70%, 70%+
- Display calibration chart in the results tracking section of the UI
- If calibration is off, the adjustment factors (especially the win modifier and pace factor exponents) should be tuned

---

## Parameter Summary

| Parameter | Default | Description |
|-----------|---------|-------------|
| `LOOKBACK_WINDOW` | 15 | Number of recent games for player baseline |
| `DECAY_FACTOR` | 0.85 | Exponential decay rate (higher = slower decay) |
| `MIN_GAMES_PLAYER` | 5 | Minimum games for a player projection |
| `MIN_GAMES_OPPONENT` | 5 | Minimum opponent games before shrinking to league avg |
| `PACE_EXPONENT_KILLS` | 1.0 | How much kills scale with pace |
| `PACE_EXPONENT_ASSISTS` | 0.8 | How much assists scale with pace |
| `GAMELENGTH_EXPONENT_CS` | 1.0 | How CS scales with game length |
| `GAMELENGTH_EXPONENT_KDA` | 0.5 | How K/D/A scales with game length |
| `LOW_CONF_STD_MULTIPLIER` | 1.5 | Std dev inflation for low-confidence projections |
| `EDGE_THRESHOLD_RECOMMEND` | 0.05 | Minimum edge (5%) to recommend a pick |
| `EDGE_THRESHOLD_HIGH_CONF` | 0.10 | Edge threshold for "high confidence" label |
