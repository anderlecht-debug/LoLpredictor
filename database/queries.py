"""Common SQL queries as functions."""

from database.db import get_connection


def get_player_recent_games(playername, limit=15):
    """Get a player's most recent games."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM player_games
        WHERE playername = ? AND gamelength >= 900
        ORDER BY date DESC
        LIMIT ?
    """, (playername, limit)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_player_games_by_team(playername, teamname, limit=15):
    """Get a player's recent games on a specific team."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM player_games
        WHERE playername = ? AND teamname = ? AND gamelength >= 900
        ORDER BY date DESC
        LIMIT ?
    """, (playername, teamname, limit)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_team_recent_games(teamname, limit=15):
    """Get a team's most recent games."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM team_games
        WHERE teamname = ? AND gamelength >= 900
        ORDER BY date DESC
        LIMIT ?
    """, (teamname, limit)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_opponent_position_stats(teamname, position, limit=15):
    """Get stats allowed by a team to a specific position."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT pg.* FROM player_games pg
        JOIN games g ON pg.game_id = g.game_id
        WHERE pg.position = ?
          AND pg.teamname != ?
          AND ((g.blue_team = ? OR g.red_team = ?))
          AND pg.gamelength >= 900
        ORDER BY pg.date DESC
        LIMIT ?
    """, (position, teamname, teamname, teamname, limit)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_league_position_averages(league, position, days=30):
    """Get league average stats for a position over recent days."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT
            AVG(kills) as avg_kills,
            AVG(deaths) as avg_deaths,
            AVG(assists) as avg_assists,
            AVG(CAST(total_cs AS REAL) / (gamelength / 60.0)) as avg_cspm,
            AVG(total_cs) as avg_cs,
            COUNT(*) as game_count
        FROM player_games
        WHERE league = ? AND position = ? AND gamelength >= 900
          AND date >= date('now', '-' || ? || ' days')
    """, (league, position, days)).fetchone()
    conn.close()
    return dict(rows) if rows else None


def get_league_averages(league, days=30):
    """Get league-wide averages for pace calculations."""
    conn = get_connection()
    row = conn.execute("""
        SELECT
            AVG(team_kpm) as avg_kpm,
            AVG(gamelength) as avg_gamelength,
            COUNT(*) as game_count
        FROM team_games
        WHERE league = ? AND gamelength >= 900
          AND date >= date('now', '-' || ? || ' days')
    """, (league, days)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_leagues():
    """Get all leagues with game counts."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT league, COUNT(*) as game_count,
               MIN(date) as earliest, MAX(date) as latest
        FROM games
        GROUP BY league
        ORDER BY game_count DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_team_players(teamname):
    """Get current players on a team."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT DISTINCT playername, position
        FROM player_games
        WHERE teamname = ?
        ORDER BY date DESC
    """, (teamname,)).fetchall()
    conn.close()
    # Deduplicate: keep first occurrence (most recent) per position
    seen_positions = {}
    players = []
    for r in rows:
        pos = r['position']
        if pos not in seen_positions:
            seen_positions[pos] = True
            players.append(dict(r))
        if len(players) >= 5:
            break
    return players


def get_upcoming_matches():
    """Get all upcoming matches."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM upcoming_matches
        WHERE status = 'upcoming'
        ORDER BY match_date ASC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_match_by_id(match_id):
    """Get a specific match."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM upcoming_matches WHERE match_id = ?", (match_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def create_match(league, team_a, team_b, match_date, fmt='Bo1'):
    """Create an upcoming match."""
    conn = get_connection()
    cursor = conn.execute("""
        INSERT INTO upcoming_matches (league, team_a, team_b, match_date, format)
        VALUES (?, ?, ?, ?, ?)
    """, (league, team_a, team_b, match_date, fmt))
    match_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return match_id


def delete_match(match_id):
    """Delete a match and its entered lines."""
    conn = get_connection()
    conn.execute("DELETE FROM entered_lines WHERE match_id = ?", (match_id,))
    conn.execute("DELETE FROM upcoming_matches WHERE match_id = ?", (match_id,))
    conn.commit()
    conn.close()


def save_line(match_id, playername, stat, line_value):
    """Save or update an entered line."""
    conn = get_connection()
    conn.execute("""
        INSERT INTO entered_lines (match_id, playername, stat, line_value)
        VALUES (?, ?, ?, ?)
        ON CONFLICT DO NOTHING
    """, (match_id, playername, stat, line_value))
    # Use upsert pattern
    conn.execute("""
        UPDATE entered_lines SET line_value = ?
        WHERE match_id = ? AND playername = ? AND stat = ?
    """, (line_value, match_id, playername, stat))
    conn.commit()
    conn.close()


def get_lines_for_match(match_id):
    """Get all entered lines for a match."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM entered_lines WHERE match_id = ?
    """, (match_id,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def save_pick(pick_data):
    """Save a pick."""
    conn = get_connection()
    cursor = conn.execute("""
        INSERT INTO picks (date_entered, match_date, league, playername, stat,
                          line, direction, model_projection, model_probability,
                          edge, confidence, notes)
        VALUES (date('now'), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        pick_data.get('match_date'),
        pick_data.get('league'),
        pick_data['playername'],
        pick_data['stat'],
        pick_data['line'],
        pick_data['direction'],
        pick_data['model_projection'],
        pick_data['model_probability'],
        pick_data['edge'],
        pick_data['confidence'],
        pick_data.get('notes'),
    ))
    pick_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return pick_id


def get_pending_picks():
    """Get all pending (unresolved) picks."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM picks WHERE hit IS NULL
        ORDER BY date_entered DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_pick_result(pick_id, actual_result):
    """Update a pick with actual result."""
    conn = get_connection()
    pick = conn.execute(
        "SELECT * FROM picks WHERE pick_id = ?", (pick_id,)
    ).fetchone()
    if pick:
        line = pick['line']
        direction = pick['direction']
        if direction == 'over':
            hit = 1 if actual_result > line else 0
        else:
            hit = 1 if actual_result < line else 0
        conn.execute("""
            UPDATE picks SET actual_result = ?, hit = ? WHERE pick_id = ?
        """, (actual_result, hit, pick_id))
    conn.commit()
    conn.close()


def get_performance_summary():
    """Get overall performance metrics."""
    conn = get_connection()
    row = conn.execute("""
        SELECT
            COUNT(*) as total_picks,
            SUM(CASE WHEN hit = 1 THEN 1 ELSE 0 END) as hits,
            SUM(CASE WHEN hit = 0 THEN 1 ELSE 0 END) as misses,
            AVG(CASE WHEN hit IS NOT NULL THEN CAST(hit AS REAL) END) as hit_rate
        FROM picks
    """).fetchone()
    conn.close()
    return dict(row) if row else None


def get_performance_by_stat():
    """Get hit rate by stat type."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT stat,
               COUNT(*) as total,
               SUM(CASE WHEN hit = 1 THEN 1 ELSE 0 END) as hits,
               AVG(CASE WHEN hit IS NOT NULL THEN CAST(hit AS REAL) END) as hit_rate
        FROM picks WHERE hit IS NOT NULL
        GROUP BY stat
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_performance_by_league():
    """Get hit rate by league."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT league,
               COUNT(*) as total,
               SUM(CASE WHEN hit = 1 THEN 1 ELSE 0 END) as hits,
               AVG(CASE WHEN hit IS NOT NULL THEN CAST(hit AS REAL) END) as hit_rate
        FROM picks WHERE hit IS NOT NULL AND league IS NOT NULL
        GROUP BY league
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_calibration_data():
    """Get calibration buckets: predicted vs actual."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT
            CASE
                WHEN model_probability >= 0.70 THEN '70%+'
                WHEN model_probability >= 0.65 THEN '65-70%'
                WHEN model_probability >= 0.60 THEN '60-65%'
                WHEN model_probability >= 0.55 THEN '55-60%'
                ELSE '50-55%'
            END as bucket,
            COUNT(*) as total,
            AVG(CAST(hit AS REAL)) as actual_rate,
            AVG(model_probability) as avg_predicted
        FROM picks WHERE hit IS NOT NULL
        GROUP BY bucket
        ORDER BY avg_predicted
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_pick_history(limit=100, offset=0):
    """Get full pick history."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM picks
        ORDER BY date_entered DESC, pick_id DESC
        LIMIT ? OFFSET ?
    """, (limit, offset)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_team_names():
    """Get all team names for autocomplete."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT teamname FROM teams ORDER BY teamname"
    ).fetchall()
    conn.close()
    return [r['teamname'] for r in rows]


def get_data_status():
    """Get database statistics and freshness."""
    conn = get_connection()
    stats = {}
    for table in ['games', 'player_games', 'team_games', 'players', 'teams']:
        row = conn.execute(f"SELECT COUNT(*) as cnt FROM {table}").fetchone()
        stats[table] = row['cnt']

    date_row = conn.execute(
        "SELECT MAX(date) as latest, MIN(date) as earliest FROM games"
    ).fetchone()
    stats['latest_date'] = date_row['latest']
    stats['earliest_date'] = date_row['earliest']

    refresh_row = conn.execute("""
        SELECT timestamp, status FROM refresh_log
        ORDER BY id DESC LIMIT 1
    """).fetchone()
    stats['last_refresh'] = dict(refresh_row) if refresh_row else None

    conn.close()
    return stats
