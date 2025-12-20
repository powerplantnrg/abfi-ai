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

# Vercel expects 'app' for ASGI applications
