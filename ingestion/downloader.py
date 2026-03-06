"""Downloads CSV data from Oracle's Elixir."""

import os
import re
from datetime import datetime, timedelta
import requests
from config import CSV_CACHE_DIR


# Oracle's Elixir hosts data on Google Drive. The download links change,
# so we provide a manual download fallback. Users can also place CSV files
# directly in data/csv_cache/.
#
# To get the latest download URL:
#   1. Visit https://oracleselixir.com/tools/downloads
#   2. Right-click the year's download link and copy the URL
#   3. Pass it via: python refresh_data.py --url "https://drive.google.com/..."

# Google Drive direct download conversion
def gdrive_direct_url(url):
    """Convert a Google Drive sharing URL to a direct download URL."""
    # Handle formats like:
    #   https://drive.google.com/file/d/FILE_ID/view?usp=sharing
    #   https://drive.google.com/uc?id=FILE_ID
    match = re.search(r'/d/([a-zA-Z0-9_-]+)', url)
    if match:
        file_id = match.group(1)
        return f"https://drive.google.com/uc?export=download&id={file_id}"
    match = re.search(r'[?&]id=([a-zA-Z0-9_-]+)', url)
    if match:
        file_id = match.group(1)
        return f"https://drive.google.com/uc?export=download&id={file_id}"
    return url


def download_csv(url, filename):
    """Download a CSV file and save to cache directory."""
    filepath = os.path.join(CSV_CACHE_DIR, filename)
    print(f"Downloading {url}...")

    # Convert Google Drive URLs to direct download format
    if 'drive.google.com' in url:
        url = gdrive_direct_url(url)
        print(f"  Converted to direct URL: {url}")

    try:
        resp = requests.get(url, timeout=120, stream=True, allow_redirects=True)
        resp.raise_for_status()

        # Validate we got CSV, not HTML
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


def download_all(custom_url=None):
    """Download all required CSV files.

    Args:
        custom_url: Optional URL to download data from (e.g., Google Drive link
                    from Oracle's Elixir downloads page).
    """
    results = {}

    if custom_url:
        filepath = download_csv(custom_url, 'player_data.csv')
        results['player_data'] = filepath
    else:
        print("No download URL configured.")
        print("Please provide one using: python refresh_data.py --url <URL>")
        print("Or manually place CSV files in data/csv_cache/")
        print("")
        print("Get the URL from: https://oracleselixir.com/tools/downloads")
        results['player_data'] = None

    return results


def get_cached_files():
    """List available cached CSV files."""
    files = []
    if os.path.exists(CSV_CACHE_DIR):
        for f in os.listdir(CSV_CACHE_DIR):
            if f.endswith('.csv'):
                files.append(os.path.join(CSV_CACHE_DIR, f))
    return files
