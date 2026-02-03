"""
Vercel Serverless Entry Point for ABFI Intelligence Suite API

This file serves as the entry point for Vercel's Python serverless functions.
It imports and exposes the FastAPI application.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app
from app.db import database as db

# Initialize database on cold start
try:
    db.init_database()
    print("Database initialized successfully")
except Exception as e:
    print(f"Database initialization error: {e}")

# Vercel expects 'app' for ASGI applications
