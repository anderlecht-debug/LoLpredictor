"""Downloads CSV data from Oracle's Elixir."""

import os
import requests
from config import CSV_CACHE_DIR

# Known Oracle's Elixir CSV download URLs
DOWNLOAD_URLS = {
    'player_data': 'https://oracleselixir.com/stats/players/byTournament/2025',
}


def download_csv(url, filename):
    """Download a CSV file and save to cache directory."""
    filepath = os.path.join(CSV_CACHE_DIR, filename)
    print(f"Downloading {url}...")
    try:
        resp = requests.get(url, timeout=120, stream=True)
        resp.raise_for_status()
        with open(filepath, 'wb') as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Saved to {filepath}")
        return filepath
    except requests.RequestException as e:
        print(f"Download failed: {e}")
        return None


def download_all():
    """Download all required CSV files."""
    results = {}
    for name, url in DOWNLOAD_URLS.items():
        filepath = download_csv(url, f"{name}.csv")
        results[name] = filepath
    return results


def get_cached_files():
    """List available cached CSV files."""
    files = []
    if os.path.exists(CSV_CACHE_DIR):
        for f in os.listdir(CSV_CACHE_DIR):
            if f.endswith('.csv'):
                files.append(os.path.join(CSV_CACHE_DIR, f))
    return files
