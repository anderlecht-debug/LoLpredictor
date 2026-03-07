"""Loads parsed data into SQLite database."""

from database.db import get_connection


def load_players_and_teams(player_df):
    """First pass: upsert players and teams only (no FK dependencies)."""
    conn = get_connection()
    players_seen = set()
    teams_seen = set()

    for _, row in player_df.iterrows():
        playername = row.get('playername')
        if not playername or playername in players_seen:
            continue
        players_seen.add(playername)

        conn.execute("""
            INSERT INTO players (playername, current_team, current_league, current_position, last_updated)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(playername) DO UPDATE SET
                current_team = excluded.current_team,
                current_league = excluded.current_league,
                current_position = excluded.current_position,
                last_updated = excluded.last_updated
        """, (
            playername,
            row.get('teamname'),
            row.get('league'),
            row.get('position'),
            row.get('date'),
        ))

        teamname = row.get('teamname')
        if teamname and teamname not in teams_seen:
            teams_seen.add(teamname)
            conn.execute("""
                INSERT INTO teams (teamname, current_league, last_updated)
                VALUES (?, ?, ?)
                ON CONFLICT(teamname) DO UPDATE SET
                    current_league = excluded.current_league,
                    last_updated = excluded.last_updated
            """, (teamname, row.get('league'), row.get('date')))

    conn.commit()
    conn.close()
    print(f"  Players: {len(players_seen)}, Teams: {len(teams_seen)}")
    return len(players_seen)


def load_player_games(player_df):
    """Second pass: insert player_games (requires games to exist)."""
    conn = get_connection()
    inserted = 0
    skipped = 0

    for _, row in player_df.iterrows():
        gameid = row.get('gameid')
        playername = row.get('playername')
        if not gameid or not playername:
            skipped += 1
            continue

        exists = conn.execute(
            "SELECT 1 FROM player_games WHERE game_id = ? AND playername = ?",
            (gameid, playername)
        ).fetchone()

        if exists:
            skipped += 1
            continue

        conn.execute("""
            INSERT INTO player_games (
                game_id, playername, teamname, league, date, patch, side,
                position, champion, result, kills, deaths, assists, total_cs,
                gamelength, dpm, damageshare, visionscore, vspm,
                killparticipation, goldat15, csat15, golddiffat15,
                csdiffat15, xpdiffat15
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            gameid, playername, row.get('teamname'), row.get('league'),
            row.get('date'), row.get('patch'), row.get('side'),
            row.get('position'), row.get('champion'),
            _safe_int(row.get('result')),
            _safe_int(row.get('kills')), _safe_int(row.get('deaths')),
            _safe_int(row.get('assists')), _safe_int(row.get('total_cs')),
            _safe_int(row.get('gamelength')),
            _safe_float(row.get('dpm')), _safe_float(row.get('damageshare')),
            _safe_float(row.get('visionscore')), _safe_float(row.get('vspm')),
            _safe_float(row.get('killparticipation')),
            _safe_float(row.get('goldat15')), _safe_float(row.get('csat15')),
            _safe_float(row.get('golddiffat15')),
            _safe_float(row.get('csdiffat15')),
            _safe_float(row.get('xpdiffat15')),
        ))
        inserted += 1

    conn.commit()
    conn.close()
    print(f"Player games: {inserted} inserted, {skipped} skipped")
    return inserted


def load_team_data(team_df):
    """Load team game data into the database."""
    conn = get_connection()
    inserted = 0
    skipped = 0

    for _, row in team_df.iterrows():
        gameid = row.get('gameid')
        teamname = row.get('teamname')
        if not gameid or not teamname:
            skipped += 1
            continue

        # Check if team_game already exists
        exists = conn.execute(
            "SELECT 1 FROM team_games WHERE game_id = ? AND teamname = ?",
            (gameid, teamname)
        ).fetchone()

        if exists:
            skipped += 1
            continue

        # Calculate team_kpm if not present
        team_kpm = _safe_float(row.get('team_kpm'))
        if team_kpm is None:
            kills = _safe_int(row.get('kills'))
            gamelength = _safe_int(row.get('gamelength'))
            if kills is not None and gamelength and gamelength > 0:
                team_kpm = kills / (gamelength / 60.0)

        conn.execute("""
            INSERT INTO team_games (
                game_id, teamname, league, date, patch, side, result,
                gamelength, kills, deaths, towers, dragons, barons,
                heralds, team_kpm, firsttower, firstdragon, firstbaron
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            gameid, teamname, row.get('league'), row.get('date'),
            row.get('patch'), row.get('side'),
            _safe_int(row.get('result')),
            _safe_int(row.get('gamelength')),
            _safe_int(row.get('kills')), _safe_int(row.get('deaths')),
            _safe_int(row.get('towers')), _safe_int(row.get('dragons')),
            _safe_int(row.get('barons')), _safe_int(row.get('heralds')),
            team_kpm,
            _safe_int(row.get('firsttower')),
            _safe_int(row.get('firstdragon')),
            _safe_int(row.get('firstbaron')),
        ))
        inserted += 1

    conn.commit()
    conn.close()
    print(f"Team data: {inserted} inserted, {skipped} skipped")
    return inserted


def load_games(player_df, team_df):
    """Load game-level data from player and team DataFrames."""
    conn = get_connection()
    inserted = 0

    # Group by game_id
    if 'gameid' not in player_df.columns:
        return 0

    game_ids = player_df['gameid'].unique()

    for gid in game_ids:
        exists = conn.execute(
            "SELECT 1 FROM games WHERE game_id = ?", (str(gid),)
        ).fetchone()
        if exists:
            continue

        game_rows = player_df[player_df['gameid'] == gid]
        if game_rows.empty:
            continue

        first_row = game_rows.iloc[0]

        # Identify blue/red teams
        blue_rows = game_rows[game_rows['side'].str.lower() == 'blue'] if 'side' in game_rows.columns else game_rows.head(5)
        red_rows = game_rows[game_rows['side'].str.lower() == 'red'] if 'side' in game_rows.columns else game_rows.tail(5)

        blue_team = blue_rows['teamname'].iloc[0] if len(blue_rows) > 0 else 'Unknown'
        red_team = red_rows['teamname'].iloc[0] if len(red_rows) > 0 else 'Unknown'

        blue_result = None
        if len(blue_rows) > 0 and 'result' in blue_rows.columns:
            blue_result = _safe_int(blue_rows['result'].iloc[0])

        total_kills = None
        if 'kills' in game_rows.columns:
            kills_sum = game_rows['kills'].sum()
            total_kills = _safe_int(kills_sum) if not _is_nan(kills_sum) else None

        conn.execute("""
            INSERT OR IGNORE INTO games (
                game_id, date, league, split, playoffs, patch,
                gamelength, blue_team, red_team, blue_result, total_kills
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(gid), first_row.get('date'), first_row.get('league'),
            first_row.get('split'), _safe_int(first_row.get('playoffs')),
            first_row.get('patch'), _safe_int(first_row.get('gamelength')),
            blue_team, red_team, blue_result, total_kills,
        ))
        inserted += 1

    conn.commit()
    conn.close()
    print(f"Games: {inserted} inserted")
    return inserted


def _safe_int(val):
    """Safely convert to int, returning None for NaN/None."""
    if val is None or _is_nan(val):
        return None
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return None


def _safe_float(val):
    """Safely convert to float, returning None for NaN/None."""
    if val is None or _is_nan(val):
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def _is_nan(val):
    """Check if a value is NaN."""
    try:
        import math
        return math.isnan(float(val))
    except (ValueError, TypeError):
        return False
