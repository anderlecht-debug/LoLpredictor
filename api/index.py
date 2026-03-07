"""Vercel serverless entry point for LoL Props Lab Flask API."""

import os
import sys
import shutil

# Ensure project root is on path (for database, engine, etc.)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Set up DB in /tmp for serverless (writable directory)
SERVERLESS_DB = '/tmp/lol_props.db'
SOURCE_DB = os.path.join(PROJECT_ROOT, 'data', 'lol_props.db')

# Copy bundled DB to /tmp on cold start if available
if os.path.exists(SOURCE_DB) and not os.path.exists(SERVERLESS_DB):
    shutil.copy2(SOURCE_DB, SERVERLESS_DB)

# Override DB_PATH before importing app modules
os.environ['LOL_PROPS_DB_PATH'] = SERVERLESS_DB

from flask import Flask
from database.db import init_db
from api.routes import api as api_blueprint

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'vercel-lol-props-lab')

# Register API blueprint
app.register_blueprint(api_blueprint)

# Initialize database on cold start
with app.app_context():
    init_db()
