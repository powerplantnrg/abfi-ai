"""
ABFI Intelligence Suite - Database Client
SQLite-based storage compatible with Vercel serverless.

For production, use Turso (LibSQL) for edge-compatible SQLite.
For development, uses local SQLite file.
"""

import sqlite3
import json
import hashlib
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
from pathlib import Path
import logging
import os

from app.core.config import settings

logger = logging.getLogger(__name__)

# Database path for local SQLite
DB_PATH = Path(__file__).parent.parent.parent / "abfi_intelligence.db"

# Check if we should use Turso (production) or local SQLite (development)
USE_TURSO = bool(settings.turso_database_url and settings.turso_auth_token)

# Turso/LibSQL connection (lazy loaded)
_turso_client = None


def _get_turso_client():
    """Get or create Turso client connection."""
    global _turso_client
    if _turso_client is None:
        try:
            import libsql_experimental as libsql
            _turso_client = libsql.connect(
                settings.turso_database_url,
                auth_token=settings.turso_auth_token
            )
            logger.info("Connected to Turso database")
        except ImportError:
            logger.warning("libsql_experimental not installed, falling back to SQLite")
            return None
        except Exception as e:
            logger.error(f"Failed to connect to Turso: {e}")
            return None
    return _turso_client


def get_connection():
    """Get database connection - Turso for production, SQLite for dev."""
    if USE_TURSO:
        client = _get_turso_client()
        if client:
            return client

    # Fallback to local SQLite
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_db():
    """Context manager for database connections."""
    conn = get_connection()
    is_turso = USE_TURSO and _turso_client is not None

    try:
        yield conn
        if not is_turso:
            conn.commit()
    except Exception as e:
        if not is_turso:
            conn.rollback()
        raise e
    finally:
        if not is_turso:
            conn.close()


def init_database():
    """Initialize database with schema."""
    with get_db() as conn:
        cursor = conn.cursor()

        # Sources table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                base_url TEXT NOT NULL,
                scraper_type TEXT NOT NULL,
                priority INTEGER DEFAULT 5,
                is_active INTEGER DEFAULT 1,
                last_scraped TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Raw documents table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS raw_documents (
                id TEXT PRIMARY KEY,
                source_id INTEGER REFERENCES sources(id),
                url TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                raw_content TEXT NOT NULL,
                metadata TEXT DEFAULT '{}',
                scraped_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(url, content_hash)
            )
        """)

        # Processed articles table with sentiment analysis
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS processed_articles (
                id TEXT PRIMARY KEY,
                raw_document_id TEXT REFERENCES raw_documents(id),
                title TEXT NOT NULL,
                published_date TEXT,
                author TEXT,
                content_text TEXT NOT NULL,
                summary TEXT,
                url TEXT,
                source TEXT,

                -- Sentiment analysis results
                sentiment TEXT CHECK(sentiment IN ('BULLISH', 'BEARISH', 'NEUTRAL')),
                sentiment_score REAL,
                intensity INTEGER CHECK(intensity >= 1 AND intensity <= 5),
                confidence REAL,

                -- Fear components (JSON)
                fear_components TEXT DEFAULT '[]',

                -- Entities (JSON)
                entities TEXT DEFAULT '{}',
                lenders_mentioned TEXT DEFAULT '[]',

                -- Classification
                is_bioenergy_relevant INTEGER DEFAULT 1,
                relevance_score REAL DEFAULT 0.0,

                processed_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Daily sentiment index table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_sentiment_index (
                id TEXT PRIMARY KEY,
                index_date TEXT UNIQUE NOT NULL,
                overall_index REAL NOT NULL,
                bullish_count INTEGER NOT NULL,
                bearish_count INTEGER NOT NULL,
                neutral_count INTEGER NOT NULL,
                documents_analyzed INTEGER NOT NULL,
                fear_breakdown TEXT NOT NULL,
                lender_scores TEXT DEFAULT '{}',
                daily_change REAL,
                weekly_change REAL,
                monthly_change REAL,
                calculated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Feedstock prices table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedstock_prices (
                id TEXT PRIMARY KEY,
                commodity TEXT NOT NULL,
                region TEXT NOT NULL,
                price REAL NOT NULL,
                currency TEXT DEFAULT 'AUD',
                unit TEXT DEFAULT 'MT',
                open_price REAL,
                high_price REAL,
                low_price REAL,
                close_price REAL,
                volume INTEGER,
                source TEXT NOT NULL,
                price_date TEXT NOT NULL,
                recorded_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(commodity, region, source, price_date)
            )
        """)

        # Policy tracker table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS policy_tracker (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                jurisdiction TEXT NOT NULL,
                policy_type TEXT NOT NULL,
                status TEXT NOT NULL,
                summary TEXT NOT NULL,
                introduced_date TEXT,
                expected_decision TEXT,
                effective_date TEXT,
                source_url TEXT,
                market_impact TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_sentiment ON processed_articles(sentiment)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_date ON processed_articles(published_date DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_source ON processed_articles(source)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sentiment_date ON daily_sentiment_index(index_date DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_prices_commodity ON feedstock_prices(commodity, region)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_prices_date ON feedstock_prices(price_date DESC)")

        # Seed sources
        sources = [
            ("RenewEconomy", "https://reneweconomy.com.au", "reneweconomy", 1),
            ("CEFC", "https://www.cefc.com.au", "cefc", 2),
            ("ARENA", "https://arena.gov.au", "arena", 2),
            ("CER", "https://www.cleanenergyregulator.gov.au", "cer", 1),
            ("AEMO", "https://aemo.com.au", "aemo", 1),
        ]

        for name, base_url, scraper_type, priority in sources:
            cursor.execute("""
                INSERT OR IGNORE INTO sources (name, base_url, scraper_type, priority)
                VALUES (?, ?, ?, ?)
            """, (name, base_url, scraper_type, priority))

        logger.info("Database initialized successfully")


# ============================================================================
# Article Operations
# ============================================================================

def insert_article(
    title: str,
    content: str,
    url: str,
    source: str,
    published_date: Optional[datetime] = None,
    author: Optional[str] = None,
) -> Optional[str]:
    """Insert a raw article if it doesn't exist."""
    import uuid

    content_hash = hashlib.sha256(content.encode()).hexdigest()[:32]
    doc_id = str(uuid.uuid4())

    with get_db() as conn:
        cursor = conn.cursor()

        # Check if article already exists
        cursor.execute(
            "SELECT id FROM raw_documents WHERE url = ? AND content_hash = ?",
            (url, content_hash)
        )
        if cursor.fetchone():
            return None  # Already exists

        # Get source ID
        cursor.execute("SELECT id FROM sources WHERE name = ?", (source,))
        source_row = cursor.fetchone()
        source_id = source_row["id"] if source_row else None

        # Insert raw document
        cursor.execute("""
            INSERT INTO raw_documents (id, source_id, url, content_hash, raw_content, metadata)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            doc_id,
            source_id,
            url,
            content_hash,
            content,
            json.dumps({"title": title, "author": author})
        ))

        return doc_id


def insert_processed_article(
    raw_document_id: str,
    title: str,
    content_text: str,
    url: str,
    source: str,
    sentiment: str,
    sentiment_score: float,
    intensity: int = 3,
    confidence: float = 0.8,
    fear_components: List[str] = None,
    lenders_mentioned: List[str] = None,
    published_date: Optional[datetime] = None,
    summary: Optional[str] = None,
) -> str:
    """Insert a processed article with sentiment analysis."""
    import uuid

    article_id = str(uuid.uuid4())

    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO processed_articles (
                id, raw_document_id, title, content_text, url, source,
                sentiment, sentiment_score, intensity, confidence,
                fear_components, lenders_mentioned, published_date, summary
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            article_id,
            raw_document_id,
            title,
            content_text,
            url,
            source,
            sentiment,
            sentiment_score,
            intensity,
            confidence,
            json.dumps(fear_components or []),
            json.dumps(lenders_mentioned or []),
            published_date.isoformat() if published_date else None,
            summary,
        ))

        return article_id


def get_recent_articles(
    limit: int = 50,
    sentiment: Optional[str] = None,
    source: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Get recent processed articles."""
    with get_db() as conn:
        cursor = conn.cursor()

        query = """
            SELECT * FROM processed_articles
            WHERE 1=1
        """
        params = []

        if sentiment:
            query += " AND sentiment = ?"
            params.append(sentiment)

        if source:
            query += " AND source = ?"
            params.append(source)

        query += " ORDER BY processed_at DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()

        return [dict(row) for row in rows]


def get_article_counts_by_sentiment(days: int = 30) -> Dict[str, int]:
    """Get article counts grouped by sentiment for the last N days."""
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT sentiment, COUNT(*) as count
            FROM processed_articles
            WHERE date(processed_at) >= date('now', ?)
            GROUP BY sentiment
        """, (f"-{days} days",))

        result = {"BULLISH": 0, "BEARISH": 0, "NEUTRAL": 0}
        for row in cursor.fetchall():
            if row["sentiment"]:
                result[row["sentiment"]] = row["count"]

        return result


# ============================================================================
# Sentiment Index Operations
# ============================================================================

def save_daily_sentiment_index(
    index_date: date,
    overall_index: float,
    bullish_count: int,
    bearish_count: int,
    neutral_count: int,
    documents_analyzed: int,
    fear_breakdown: Dict[str, float],
    lender_scores: Dict[str, float] = None,
) -> str:
    """Save daily sentiment index."""
    import uuid

    index_id = str(uuid.uuid4())

    with get_db() as conn:
        cursor = conn.cursor()

        # Calculate changes
        cursor.execute("""
            SELECT overall_index FROM daily_sentiment_index
            WHERE index_date = date(?, '-1 day')
        """, (index_date.isoformat(),))
        prev_day = cursor.fetchone()
        daily_change = overall_index - prev_day["overall_index"] if prev_day else None

        cursor.execute("""
            SELECT overall_index FROM daily_sentiment_index
            WHERE index_date = date(?, '-7 days')
        """, (index_date.isoformat(),))
        prev_week = cursor.fetchone()
        weekly_change = overall_index - prev_week["overall_index"] if prev_week else None

        cursor.execute("""
            SELECT overall_index FROM daily_sentiment_index
            WHERE index_date = date(?, '-30 days')
        """, (index_date.isoformat(),))
        prev_month = cursor.fetchone()
        monthly_change = overall_index - prev_month["overall_index"] if prev_month else None

        # Insert or replace
        cursor.execute("""
            INSERT OR REPLACE INTO daily_sentiment_index (
                id, index_date, overall_index, bullish_count, bearish_count,
                neutral_count, documents_analyzed, fear_breakdown, lender_scores,
                daily_change, weekly_change, monthly_change
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            index_id,
            index_date.isoformat(),
            overall_index,
            bullish_count,
            bearish_count,
            neutral_count,
            documents_analyzed,
            json.dumps(fear_breakdown),
            json.dumps(lender_scores or {}),
            daily_change,
            weekly_change,
            monthly_change,
        ))

        return index_id


def get_latest_sentiment_index() -> Optional[Dict[str, Any]]:
    """Get the most recent sentiment index."""
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM daily_sentiment_index
            ORDER BY index_date DESC
            LIMIT 1
        """)

        row = cursor.fetchone()
        if row:
            result = dict(row)
            result["fear_breakdown"] = json.loads(result["fear_breakdown"])
            result["lender_scores"] = json.loads(result["lender_scores"])
            return result

        return None


def get_sentiment_history(days: int = 365) -> List[Dict[str, Any]]:
    """Get sentiment index history."""
    with get_db() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM daily_sentiment_index
            WHERE index_date >= date('now', ?)
            ORDER BY index_date ASC
        """, (f"-{days} days",))

        results = []
        for row in cursor.fetchall():
            result = dict(row)
            result["fear_breakdown"] = json.loads(result["fear_breakdown"])
            result["lender_scores"] = json.loads(result["lender_scores"])
            results.append(result)

        return results


# ============================================================================
# Lender Operations
# ============================================================================

def get_lender_sentiment_scores(limit: int = 10) -> List[Dict[str, Any]]:
    """Calculate sentiment scores by lender mentioned in articles."""
    with get_db() as conn:
        cursor = conn.cursor()

        # Get all articles with lenders mentioned
        cursor.execute("""
            SELECT lenders_mentioned, sentiment, sentiment_score
            FROM processed_articles
            WHERE lenders_mentioned != '[]'
            AND date(processed_at) >= date('now', '-90 days')
        """)

        lender_data = {}
        for row in cursor.fetchall():
            lenders = json.loads(row["lenders_mentioned"])
            for lender in lenders:
                if lender not in lender_data:
                    lender_data[lender] = {"scores": [], "docs": 0}
                lender_data[lender]["scores"].append(row["sentiment_score"] * 100)
                lender_data[lender]["docs"] += 1

        # Calculate averages
        results = []
        for lender, data in lender_data.items():
            if data["docs"] >= 3:  # Minimum 3 documents
                avg_score = sum(data["scores"]) / len(data["scores"])
                results.append({
                    "lender": lender,
                    "sentiment": round(avg_score, 1),
                    "documents": data["docs"],
                    "trend": data["scores"][-10:],  # Last 10 scores for sparkline
                })

        # Sort by number of documents
        results.sort(key=lambda x: x["documents"], reverse=True)
        return results[:limit]


# Initialize database on import
init_database()
