"""Downloads CSV data from Oracle's Elixir."""

import os
import re
from datetime import datetime, timedelta
import requests
from config import CSV_CACHE_DIR


# Oracle's Elixir hosts data on Google Drive. The links may change over time.
# Update DEFAULT_GDRIVE_URL below if the link stops working, or pass a new
# one via: python refresh_data.py --url "https://drive.google.com/..."
# Get updated URLs from: https://oracleselixir.com/tools/downloads

# Default Google Drive file ID for 2025 match data
DEFAULT_GDRIVE_URL = 'https://drive.google.com/file/d/1v6LRphp2kYciU4SXp0PCjEMuev1bDejc/view'

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


def _get_gdrive_file_id(url):
    """Extract Google Drive file ID from URL."""
    match = re.search(r'/d/([a-zA-Z0-9_-]+)', url)
    if match:
        return match.group(1)
    match = re.search(r'[?&]id=([a-zA-Z0-9_-]+)', url)
    if match:
        return match.group(1)
    return None


def _download_from_gdrive(file_id, filepath):
    """Download a file from Google Drive, handling large-file confirmation."""
    session = requests.Session()
    base_url = "https://drive.google.com/uc?export=download"
    resp = session.get(base_url, params={'id': file_id}, stream=True, timeout=120)
    resp.raise_for_status()

    # Google Drive shows a confirmation page for large files.
    # Check for the confirm token in cookies or response.
    confirm_token = None
    for key, value in resp.cookies.items():
        if key.startswith('download_warning'):
            confirm_token = value
            break

    if confirm_token:
        print("  Large file detected, confirming download...")
        resp = session.get(base_url, params={'id': file_id, 'confirm': confirm_token},
                           stream=True, timeout=300)
        resp.raise_for_status()

    # Validate we got CSV, not HTML
    first_chunk = next(resp.iter_content(chunk_size=4096), b'')
    if first_chunk and first_chunk.strip().startswith(b'<'):
        # One more attempt: try with confirm=t (newer Google Drive behavior)
        resp = session.get(base_url, params={'id': file_id, 'confirm': 't'},
                           stream=True, timeout=300)
        resp.raise_for_status()
        first_chunk = next(resp.iter_content(chunk_size=4096), b'')
        if first_chunk and first_chunk.strip().startswith(b'<'):
            print(f"  Download returned HTML. The Google Drive link may require manual download.")
            return None

    with open(filepath, 'wb') as f:
        f.write(first_chunk)
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)
    return filepath


def download_csv(url, filename):
    """Download a CSV file and save to cache directory."""
    filepath = os.path.join(CSV_CACHE_DIR, filename)
    print(f"Downloading from {url}...")

    try:
        # Use specialized Google Drive downloader
        file_id = _get_gdrive_file_id(url)
        if file_id:
            result = _download_from_gdrive(file_id, filepath)
            if result:
                print(f"Saved to {filepath}")
                return result
            return None

        # Generic download for non-Google-Drive URLs
        resp = requests.get(url, timeout=120, stream=True, allow_redirects=True)
        resp.raise_for_status()
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

    url = custom_url or DEFAULT_GDRIVE_URL
    filepath = download_csv(url, 'player_data.csv')
    results['player_data'] = filepath

    return results


def get_cached_files():
    """List available cached CSV files."""
    files = []
    if os.path.exists(CSV_CACHE_DIR):
        for f in os.listdir(CSV_CACHE_DIR):
            if f.endswith('.csv'):
                files.append(os.path.join(CSV_CACHE_DIR, f))
    return files
