"""SQLite database connection and initialization."""

import sqlite3
import os
from config import DB_PATH, DEFAULT_PARAMS

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), 'schema.sql')


def get_connection():
    """Get a SQLite connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    """Initialize the database with schema and default settings."""
    conn = get_connection()
    with open(SCHEMA_PATH, 'r') as f:
        conn.executescript(f.read())

    # Insert default model settings if not present
    for key, value in DEFAULT_PARAMS.items():
        conn.execute(
            "INSERT OR IGNORE INTO model_settings (key, value) VALUES (?, ?)",
            (key, value)
        )
    conn.commit()
    conn.close()


def get_settings():
    """Load model settings from database."""
    conn = get_connection()
    rows = conn.execute("SELECT key, value FROM model_settings").fetchall()
    conn.close()
    return {row['key']: row['value'] for row in rows}


def update_settings(settings_dict):
    """Update model settings."""
    conn = get_connection()
    for key, value in settings_dict.items():
        conn.execute(
            "INSERT OR REPLACE INTO model_settings (key, value) VALUES (?, ?)",
            (key, float(value))
        )
    conn.commit()
    conn.close()
