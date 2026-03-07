"""Data download and ingestion script for LoL Props Lab."""

import sys
import os

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db import init_db, get_connection
from ingestion.downloader import download_all, get_cached_files
from ingestion.parser import parse_csv
from ingestion.loader import load_players_and_teams, load_games, load_player_games, load_team_data


def refresh(download=True, url=None):
    """Run the full data refresh pipeline."""
    print("=== LoL Props Lab Data Refresh ===")

    # Initialize database
    print("\n1. Initializing database...")
    init_db()

    # Download CSVs
    if download:
        print("\n2. Downloading data from Oracle's Elixir...")
        results = download_all(custom_url=url)
        csv_files = [v for v in results.values() if v is not None]
    else:
        print("\n2. Using cached CSV files...")
        csv_files = get_cached_files()

    if not csv_files:
        print("No CSV files available. Please check your internet connection or place CSV files in data/csv_cache/")
        log_refresh(0, 'error', 'No CSV files available')
        return

    # Parse and load each file
    total_rows = 0
    for filepath in csv_files:
        print(f"\n3. Processing {os.path.basename(filepath)}...")
        try:
            player_df, team_df = parse_csv(filepath)

            print("   Phase 1: Loading players and teams...")
            player_count = load_players_and_teams(player_df)

            print("   Phase 2: Loading games...")
            games_count = load_games(player_df, team_df)

            print("   Phase 3: Loading player games...")
            pg_count = load_player_games(player_df)

            print("   Phase 4: Loading team games...")
            tg_count = load_team_data(team_df)

            total_rows += player_count + games_count + pg_count + tg_count
        except Exception as e:
            print(f"   Error processing {filepath}: {e}")
            continue

    print(f"\n=== Refresh complete: {total_rows} new rows loaded ===")
    log_refresh(total_rows, 'success', f'{total_rows} rows loaded')


def log_refresh(rows, status, message):
    """Log the refresh to the database."""
    try:
        conn = get_connection()
        conn.execute("""
            INSERT INTO refresh_log (rows_processed, status, message)
            VALUES (?, ?, ?)
        """, (rows, status, message))
        conn.commit()
        conn.close()
    except Exception:
        pass


if __name__ == '__main__':
    skip_download = '--no-download' in sys.argv or '--cached' in sys.argv

    # Parse --url argument
    custom_url = None
    for i, arg in enumerate(sys.argv):
        if arg == '--url' and i + 1 < len(sys.argv):
            custom_url = sys.argv[i + 1]

    if skip_download:
        refresh(download=False)
    else:
        refresh(download=True, url=custom_url)
