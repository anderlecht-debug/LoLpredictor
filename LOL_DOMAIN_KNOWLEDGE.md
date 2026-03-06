# LoL Esports Domain Knowledge

## Critical Context for Accurate Projections

This document captures domain-specific knowledge that must be understood when building and using the projection system. Misunderstanding any of these factors will lead to systematic projection errors.

---

## Role-Specific Stat Profiles

Player stats vary dramatically by role. The model must never compare a support's kills to a mid laner's kills. All baselines, opponent adjustments, and league averages must be segmented by position.

### Typical Stat Ranges by Role (Per Game, Approximate)

| Role | Kills | Deaths | Assists | CS |
|------|-------|--------|---------|-----|
| Top | 2-5 | 2-4 | 4-8 | 220-290 |
| Jungle | 2-5 | 2-5 | 6-10 | 160-220 |
| Mid | 3-6 | 2-4 | 5-9 | 230-290 |
| Bot (ADC) | 3-7 | 2-4 | 5-8 | 260-330 |
| Support | 0-2 | 3-5 | 8-14 | 25-50 |

### Modeling Implications
- **Support kills** are extremely low and Poisson-distributed with a very low mean — even small changes in projection dramatically shift over/under probabilities
- **Support CS** is very low and mostly irrelevant for props (Underdog rarely offers it)
- **ADC CS** has the highest mean and lowest relative variance — most predictable
- **Jungle CS** includes monster kills and is more volatile than lane CS
- **Assists** for supports are much higher and more variable than for carries

---

## Patch Impact

League of Legends patches change the game meta every 2-4 weeks. Some patches are minor (number tweaks), others fundamentally reshape which champions and strategies are viable.

### How Patches Affect Projections
- **Champion viability shifts** — a player who dominated on a now-nerfed champion may see stat drops
- **Game pace changes** — some patches favor early aggression (more kills, shorter games), others favor scaling (fewer early kills, longer games)
- **Role priority shifts** — some metas are "bot lane focused" (ADCs get more resources and kills), others are "top lane carry" metas

### Handling in the Model
- Segment data by patch when calculating league averages for pace and game length
- When a player's data spans a major patch boundary, weight post-patch games 2x
- Flag projections where >50% of lookback data is from a different patch
- Major patch indicators: champion rework, item system changes, dragon/baron objective changes, map changes

### Patch Version Format
- Format: `SEASON.PATCH` (e.g., `14.10` = Season 14, Patch 10)
- Minor hotfixes sometimes shown as `14.10.1` — treat as same patch
- New season patches (e.g., `15.1`) are always major meta shifts

---

## League Quality and Data Reliability

Not all leagues are equal in skill level or data quality.

### Tier Classification
| Tier | Leagues | Notes |
|------|---------|-------|
| S | LCK, LPL | Highest skill, most data, most reliable projections |
| A | LEC, LCS | High skill, good data |
| B | PCS, VCS, CBLOL | Moderate skill, decent data, more variance |
| C | LLA, LJL, LCO | Lower sample sizes, higher variance, more volatile |
| Special | MSI, Worlds | Cross-region — requires careful handling |

### Implications for Modeling
- **Tier C leagues** often have softer Underdog lines (less market attention) — this is where edges tend to be largest
- **Cross-region events** (MSI, Worlds) create matchups with no head-to-head history — rely more on league-level opponent adjustments
- **Opponent adjustments** should be calculated within the same league (an LCK team's defensive stats shouldn't be compared to LLA averages)
- When a league has fewer teams/games, the "league average" baseline is noisier — use wider confidence intervals

---

## Roster Changes and Substitutions

LoL esports teams frequently swap players, especially in:
- LPL (China) — liberal use of 6-10 man rosters with frequent substitutions
- Academy/trainee callups mid-split
- Emergency substitutions (illness, visa issues)

### Handling
- If a player has no data in the current split/season, flag as "new roster" and mark low confidence
- If a team is fielding a substitute, the opponent adjustment for "what this team allows" may be misleading (team plays differently with subs)
- When a player moves to a new team, their historical data is still useful for individual baseline but the team-dependent factors (pace, win probability) must use the new team's data
- The system should allow the user to manually note "Player X is subbing in" to trigger appropriate adjustments

---

## Blue/Red Side Asymmetry

The game is not symmetric between blue and red side:
- **Blue side** historically has a slight win rate advantage (typically 51-53%) due to champion draft order
- Some teams have significant blue/red side splits (e.g., a team might be 80% win rate on blue, 45% on red)
- Individual player stats can vary by side due to different draft priorities and lane matchup dynamics

### In the Model
- Win probability calculation should include a side adjustment if side is known
- For individual player baselines, a blue/red split can be included as a secondary factor but sample sizes are often too small to be reliable — treat with caution
- Don't over-index on this — it's a minor factor compared to pace and opponent quality

---

## Game Length Distributions

Game lengths are NOT normally distributed — they have a slight right skew (some games go very long, few end extremely early due to the comeback mechanics in LoL).

### Typical Ranges
- Fast games: 22-28 minutes
- Average games: 28-35 minutes
- Long games: 35-45 minutes
- Extreme: 45+ minutes (rare, maybe 2-3% of games)

### Impact on Stats
- CS scales approximately linearly with game time
- Kills scale sub-linearly (many kills happen in mid-game teamfights, not evenly across time)
- Deaths and assists follow similar patterns to kills
- Very short games (<25 min) often indicate a stomp — the winning team has inflated kills and the losing team has depressed everything

---

## Common Underdog Line Traps

### Stat Inflation in High-Kill Games
Underdog may set lines based on recent averages without fully accounting for upcoming pace. If a player's recent games were against slow teams and they're now facing a fast team, the line may be too low.

### Support Death Lines
Support deaths are highly variable and heavily game-script dependent. Supports die more in losses and in long games. Lines on support deaths are some of the hardest to project accurately — approach with wider margins.

### ADC CS in Short Games
If a game ends at 25 minutes, even a dominant ADC might only hit 250 CS. If Underdog's line is set at 260, the under might be correct simply because the game environment won't support 260 CS. Always check expected game length.

### "Pillow Fight" Games
Some matchups between two passive, slow teams produce games with very few kills. Both teams might average 0.6 KPM. In these games, EVERY kill and death line should be approached with under bias, and CS lines should be approached with over bias (long games, few fights = lots of farming).

---

## Data Quirks in Oracle's Elixir

### Known Issues
- Some early-season games may have incomplete data (nulls in advanced stats)
- Remade games (due to bugs) may appear in the data — check for suspiciously short game lengths (<10 minutes)
- Player names may change (rebrand, roster swap with name change) — the parser should handle this
- Some fields have inconsistent naming across seasons (e.g., `total cs` vs `totcs` vs `minions + monsters`)
- Team names may change mid-season (org rebrand)

### Filtering Recommendations
- Exclude games with `gamelength < 900` seconds (15 minutes) — likely remakes
- Exclude games with null kill/death/assist data
- For CS, exclude games where CS is null or 0 (data error, not actual 0 CS)
- When player appears on multiple teams in same season, segment their data by team

---

## Season and Split Structure

### Typical Calendar
- **Spring Split:** January–April
- **MSI:** May
- **Summer Split:** June–September
- **Worlds:** October–November
- **Off-season:** December (roster changes, no competitive data)

### Implications
- Cross-split data (using Spring data for Summer projections) is less reliable due to meta changes, roster changes, and form resets
- Within a split, recency-weighted data is appropriate
- At split start, all players have thin data — the model should automatically widen confidence intervals early in a split
- Playoff data may differ from regular season (teams play differently under pressure, Bo5 format means more data points per matchup but in a different context)

---

## Glossary of Key Terms

| Term | Definition |
|------|------------|
| KPM | Kills per minute (team or player) |
| CS | Creep Score — minions and monsters killed |
| DPM | Damage per minute |
| GD@15 | Gold difference at 15 minutes |
| CSD@15 | Creep score difference at 15 minutes |
| XPD@15 | Experience difference at 15 minutes |
| KP% | Kill participation — (kills + assists) / team total kills |
| VSPM | Vision score per minute |
| Bo1/Bo3/Bo5 | Best of 1/3/5 games in a series |
| Meta | The current dominant strategies and champion picks |
| Draft | Champion selection phase before the game |
| Prop | Proposition bet — a bet on an individual stat line |
| Parlay | Multiple picks combined — all must hit to win |
| EV | Expected value |
| Edge | Difference between model probability and implied probability |
| Line | The stat threshold set by the sportsbook (e.g., 4.5 kills) |
