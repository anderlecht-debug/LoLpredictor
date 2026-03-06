"""Flask application entry point for LoL Props Lab."""

import os
import sys

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template
from database.db import init_db
from api.routes import api

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)


@app.route('/')
def index():
    return render_template('index.html')


# Register API blueprint
app.register_blueprint(api)

# Initialize database on startup
with app.app_context():
    init_db()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
