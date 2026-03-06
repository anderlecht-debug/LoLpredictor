"""Downloads CSV data from Oracle's Elixir."""

import os
import requests
from config import CSV_CACHE_DIR

# Known Oracle's Elixir CSV download URLs
# Direct S3 links for match data CSVs
DOWNLOAD_URLS = {
    'player_data': 'https://oracleselixir-downloadable-match-data.s3-us-west-2.amazonaws.com/2025_LoL_esports_match_data_from_OraclesElixir.csv',
}


def download_csv(url, filename):
    """Download a CSV file and save to cache directory."""
    filepath = os.path.join(CSV_CACHE_DIR, filename)
    print(f"Downloading {url}...")
    try:
        resp = requests.get(url, timeout=120, stream=True)
        resp.raise_for_status()

        # Validate we got CSV, not HTML
        content_type = resp.headers.get('Content-Type', '')
        first_chunk = next(resp.iter_content(chunk_size=1024), b'')
        if first_chunk and first_chunk.strip().startswith(b'<'):
            print(f"Download returned HTML instead of CSV. URL may be wrong: {url}")
            return None

        with open(filepath, 'wb') as f:
            f.write(first_chunk)
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
