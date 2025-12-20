"""
ABFI Intelligence Suite - Lending Sentiment API

Product 1: Lending Sentiment Dashboard
Provides lending sentiment index, fear components, and document analysis.

Now connected to real database with scraped and analyzed articles.
"""

import json
from datetime import date, datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Query, UploadFile, File, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from app.db import database as db
from app.services.llm_analyzer import analyze_article as llm_analyze
from app.services.data_pipeline import run_pipeline, refresh_sentiment_index


router = APIRouter()


# ============================================================================
# Response Models (aligned with dashboard wireframes)
# ============================================================================

class FearComponents(BaseModel):
    """Fear component breakdown (percentages)."""
    regulatory_risk: float = Field(default=0, ge=0, le=100)
    technology_risk: float = Field(default=0, ge=0, le=100)
    feedstock_risk: float = Field(default=0, ge=0, le=100)
    counterparty_risk: float = Field(default=0, ge=0, le=100)
    market_risk: float = Field(default=0, ge=0, le=100)
    esg_concerns: float = Field(default=0, ge=0, le=100)


class EntityAnnotation(BaseModel):
    """Entity mention in document."""
    text: str
    label: str  # LENDER, PROJECT, POLICY, COMPANY
    start: int
    end: int


class SentimentIndex(BaseModel):
    """Daily sentiment index values for dashboard KPIs."""
    date: date
    overall_index: float = Field(..., ge=-100, le=100, description="Net sentiment -100 to +100")
    bullish_count: int
    bearish_count: int
    neutral_count: int
    documents_analyzed: int
    fear_components: FearComponents
    daily_change: Optional[float] = None
    weekly_change: Optional[float] = None
    monthly_change: Optional[float] = None


class SentimentTrend(BaseModel):
    """Time series data point for sentiment chart."""
    date: date
    bullish: float
    bearish: float
    net_sentiment: float


class LenderScore(BaseModel):
    """Sentiment score for a specific lender."""
    lender: str
    sentiment: float = Field(..., ge=-100, le=100)
    change_30d: float
    documents: int
    trend: List[float]  # Sparkline data


class DocumentFeed(BaseModel):
    """Document entry for real-time feed."""
    id: str
    title: str
    source: str
    published_date: datetime
    sentiment: str  # BULLISH, BEARISH, NEUTRAL
    sentiment_score: float = Field(..., ge=-1, le=1)
    url: Optional[str] = None


class DocumentAnalysis(BaseModel):
    """Full document sentiment analysis result."""
    doc_id: str
    title: str
    source: str
    source_type: str
    published_date: Optional[datetime] = None
    url: Optional[str] = None

    # Primary classification
    sentiment: str  # BULLISH, BEARISH, NEUTRAL
    sentiment_score: float = Field(..., ge=-1, le=1)
    intensity: int = Field(..., ge=1, le=5)

    # Multi-dimensional analysis
    fear_components: List[str]  # Risk factors identified
    temporal: str  # SHORT_TERM, MEDIUM_TERM, LONG_TERM

    # Entities
    entities: List[EntityAnnotation]
    lenders_mentioned: List[str]
    projects_mentioned: List[str]
    policies_mentioned: List[str]

    # ML metadata
    confidence: float = Field(..., ge=0, le=1)
    attention_highlights: List[str]
    processed_at: datetime


class SentimentAlert(BaseModel):
    """Alert configuration for sentiment thresholds."""
    id: str
    name: str
    condition: str  # threshold expression
    threshold: float
    is_active: bool
    last_triggered: Optional[datetime] = None


# ============================================================================
# Helper Functions
# ============================================================================

def _get_mock_sentiment_index() -> SentimentIndex:
    """Return mock data when no real data exists."""
    return SentimentIndex(
        date=date.today(),
        overall_index=42,
        bullish_count=156,
        bearish_count=87,
        neutral_count=2604,
        documents_analyzed=2847,
        fear_components=FearComponents(
            regulatory_risk=34,
            technology_risk=21,
            feedstock_risk=18,
            counterparty_risk=14,
            market_risk=8,
            esg_concerns=5,
        ),
        daily_change=2.3,
        weekly_change=8.5,
        monthly_change=12.0,
    )


# ============================================================================
# Endpoints - Dashboard Data
# ============================================================================

@router.get("/index", response_model=SentimentIndex)
async def get_current_sentiment_index():
    """
    Get the current lending sentiment index.

    Returns overall index, document counts, and fear component breakdown.
    Used for KPI cards on dashboard.
    """
    # Try to get real data from database
    latest = db.get_latest_sentiment_index()

    if latest:
        fear = latest.get("fear_breakdown", {})
        return SentimentIndex(
            date=date.fromisoformat(latest["index_date"]),
            overall_index=latest["overall_index"],
            bullish_count=latest["bullish_count"],
            bearish_count=latest["bearish_count"],
            neutral_count=latest["neutral_count"],
            documents_analyzed=latest["documents_analyzed"],
            fear_components=FearComponents(
                regulatory_risk=fear.get("regulatory_risk", 0),
                technology_risk=fear.get("technology_risk", 0),
                feedstock_risk=fear.get("feedstock_risk", 0),
                counterparty_risk=fear.get("counterparty_risk", 0),
                market_risk=fear.get("market_risk", 0),
                esg_concerns=fear.get("esg_concerns", 0),
            ),
            daily_change=latest.get("daily_change"),
            weekly_change=latest.get("weekly_change"),
            monthly_change=latest.get("monthly_change"),
        )

    # Fallback to mock data if no real data
    return _get_mock_sentiment_index()


@router.get("/index/history", response_model=List[SentimentIndex])
async def get_sentiment_history(
    lookback_days: int = Query(default=365, ge=1, le=730),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
):
    """
    Get historical sentiment index time series.

    Used for main sentiment trend chart on dashboard.
    """
    history_data = db.get_sentiment_history(days=lookback_days)

    if history_data:
        results = []
        for item in history_data:
            fear = item.get("fear_breakdown", {})
            results.append(SentimentIndex(
                date=date.fromisoformat(item["index_date"]),
                overall_index=item["overall_index"],
                bullish_count=item["bullish_count"],
                bearish_count=item["bearish_count"],
                neutral_count=item["neutral_count"],
                documents_analyzed=item["documents_analyzed"],
                fear_components=FearComponents(
                    regulatory_risk=fear.get("regulatory_risk", 0),
                    technology_risk=fear.get("technology_risk", 0),
                    feedstock_risk=fear.get("feedstock_risk", 0),
                    counterparty_risk=fear.get("counterparty_risk", 0),
                    market_risk=fear.get("market_risk", 0),
                    esg_concerns=fear.get("esg_concerns", 0),
                ),
                daily_change=item.get("daily_change"),
                weekly_change=item.get("weekly_change"),
                monthly_change=item.get("monthly_change"),
            ))
        return results

    # Generate mock historical data as fallback
    end = end_date or date.today()
    start = start_date or (end - timedelta(days=lookback_days))

    history = []
    current = start
    while current <= end:
        history.append(SentimentIndex(
            date=current,
            overall_index=42 + (hash(str(current)) % 40) - 20,
            bullish_count=150 + (hash(str(current)) % 20),
            bearish_count=80 + (hash(str(current)) % 15),
            neutral_count=2500 + (hash(str(current)) % 200),
            documents_analyzed=2800 + (hash(str(current)) % 100),
            fear_components=FearComponents(
                regulatory_risk=34,
                technology_risk=21,
                feedstock_risk=18,
                counterparty_risk=14,
                market_risk=8,
                esg_concerns=5,
            ),
        ))
        current += timedelta(days=1)

    return history


@router.get("/trend", response_model=List[SentimentTrend])
async def get_sentiment_trend(
    period: str = Query(default="12m", regex="^(1m|3m|6m|12m|24m)$"),
):
    """
    Get sentiment trend data for area chart.

    Returns bullish, bearish, and net sentiment time series.
    """
    periods = {"1m": 30, "3m": 90, "6m": 180, "12m": 365, "24m": 730}
    days = periods.get(period, 365)

    history_data = db.get_sentiment_history(days=days)

    if history_data:
        return [
            SentimentTrend(
                date=date.fromisoformat(item["index_date"]),
                bullish=item["bullish_count"],
                bearish=item["bearish_count"],
                net_sentiment=item["overall_index"],
            )
            for item in history_data
        ]

    # Mock data fallback
    trends = []
    for i in range(days):
        d = date.today() - timedelta(days=days - i)
        trends.append(SentimentTrend(
            date=d,
            bullish=50 + (hash(str(d)) % 30),
            bearish=30 + (hash(str(d)) % 20),
            net_sentiment=20 + (hash(str(d)) % 40) - 20,
        ))

    return trends


@router.get("/lenders", response_model=List[LenderScore])
async def get_lender_scores(
    limit: int = Query(default=10, le=50),
):
    """
    Get sentiment scores by lender.

    Used for lender comparison matrix on dashboard.
    """
    lender_data = db.get_lender_sentiment_scores(limit=limit)

    if lender_data:
        return [
            LenderScore(
                lender=item["lender"],
                sentiment=item["sentiment"],
                change_30d=0,  # TODO: calculate from historical data
                documents=item["documents"],
                trend=item.get("trend", []),
            )
            for item in lender_data
        ]

    # Mock data fallback
    lenders = [
        ("CEFC", 68, 12, 45),
        ("NAB", 34, 5, 28),
        ("CBA", 22, -8, 31),
        ("ANZ", 15, 0, 19),
        ("Westpac", -12, -15, 22),
        ("Macquarie", 45, 8, 15),
        ("ARENA", 55, 10, 12),
        ("ADB", 28, 3, 8),
    ]

    return [
        LenderScore(
            lender=name,
            sentiment=score,
            change_30d=change,
            documents=docs,
            trend=[score + i for i in range(-5, 5)],
        )
        for name, score, change, docs in lenders[:limit]
    ]


@router.get("/documents/feed", response_model=List[DocumentFeed])
async def get_document_feed(
    limit: int = Query(default=20, le=100),
    sentiment: Optional[str] = Query(default=None, regex="^(BULLISH|BEARISH|NEUTRAL)$"),
):
    """
    Get real-time document feed with sentiment labels.

    Used for latest documents panel on dashboard.
    """
    articles = db.get_recent_articles(limit=limit, sentiment=sentiment)

    if articles:
        results = []
        for article in articles:
            pub_date = article.get("published_date") or article.get("processed_at")
            if isinstance(pub_date, str):
                try:
                    pub_date = datetime.fromisoformat(pub_date.replace("Z", "+00:00"))
                except:
                    pub_date = datetime.now()

            results.append(DocumentFeed(
                id=article["id"],
                title=article["title"],
                source=article.get("source", "Unknown"),
                published_date=pub_date if isinstance(pub_date, datetime) else datetime.now(),
                sentiment=article.get("sentiment", "NEUTRAL"),
                sentiment_score=article.get("sentiment_score", 0),
                url=article.get("url"),
            ))
        return results

    # Mock documents fallback
    docs = [
        DocumentFeed(
            id="doc1",
            title="CEFC announces $150M bioenergy investment fund",
            source="RenewEconomy",
            published_date=datetime.now() - timedelta(hours=2),
            sentiment="BULLISH",
            sentiment_score=0.82,
            url="https://reneweconomy.com.au/example",
        ),
        DocumentFeed(
            id="doc2",
            title="Banks tighten lending criteria for new projects",
            source="AFR",
            published_date=datetime.now() - timedelta(hours=5),
            sentiment="BEARISH",
            sentiment_score=-0.65,
            url="https://afr.com/example",
        ),
        DocumentFeed(
            id="doc3",
            title="Policy consultation opens for SAF mandate",
            source="DCCEEW",
            published_date=datetime.now() - timedelta(hours=8),
            sentiment="NEUTRAL",
            sentiment_score=0.12,
            url="https://dcceew.gov.au/example",
        ),
    ]

    if sentiment:
        docs = [d for d in docs if d.sentiment == sentiment]

    return docs[:limit]


# ============================================================================
# Endpoints - Analysis
# ============================================================================

@router.post("/analyze", response_model=DocumentAnalysis)
async def analyze_document(
    file: Optional[UploadFile] = File(None),
    url: Optional[str] = None,
    text: Optional[str] = None,
):
    """
    Analyze a document for lending sentiment.

    Provide one of: file upload, URL, or raw text.
    Returns detailed sentiment breakdown with entity annotations.
    """
    if not file and not url and not text:
        raise HTTPException(
            status_code=400,
            detail="Provide file, url, or text for analysis"
        )

    # Get content
    content = text or ""
    title = "Analyzed Document"
    source = "Text Input"

    if file:
        content = (await file.read()).decode("utf-8", errors="ignore")
        title = file.filename or "Uploaded Document"
        source = "User Upload"
    elif url:
        source = "URL"
        title = url

    # Analyze using LLM
    analysis = await llm_analyze(title=title, content=content, source=source)

    if analysis:
        return DocumentAnalysis(
            doc_id="analysis_" + datetime.now().strftime("%Y%m%d%H%M%S"),
            title=title,
            source=source,
            source_type="upload" if file else ("url" if url else "text"),
            published_date=datetime.now(),
            sentiment=analysis.sentiment,
            sentiment_score=analysis.sentiment_score,
            intensity=analysis.intensity,
            fear_components=analysis.fear_components,
            temporal="MEDIUM_TERM",
            entities=[],
            lenders_mentioned=analysis.lenders_mentioned,
            projects_mentioned=[],
            policies_mentioned=[],
            confidence=analysis.confidence,
            attention_highlights=[analysis.summary],
            processed_at=datetime.now(),
        )

    # Fallback mock result
    return DocumentAnalysis(
        doc_id="analysis_" + datetime.now().strftime("%Y%m%d%H%M%S"),
        title=title,
        source=source,
        source_type="upload" if file else ("url" if url else "text"),
        published_date=datetime.now(),
        sentiment="NEUTRAL",
        sentiment_score=0.0,
        intensity=3,
        fear_components=[],
        temporal="MEDIUM_TERM",
        entities=[],
        lenders_mentioned=[],
        projects_mentioned=[],
        policies_mentioned=[],
        confidence=0.5,
        attention_highlights=["Analysis pending"],
        processed_at=datetime.now(),
    )


@router.get("/documents", response_model=List[DocumentAnalysis])
async def list_analyzed_documents(
    source: Optional[str] = None,
    sentiment: Optional[str] = Query(default=None, regex="^(BULLISH|BEARISH|NEUTRAL)$"),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
):
    """
    List analyzed documents with their sentiment scores.

    Filter by source, sentiment, date range with pagination.
    """
    articles = db.get_recent_articles(limit=limit, sentiment=sentiment, source=source)

    results = []
    for article in articles:
        pub_date = article.get("published_date") or article.get("processed_at")
        if isinstance(pub_date, str):
            try:
                pub_date = datetime.fromisoformat(pub_date.replace("Z", "+00:00"))
            except:
                pub_date = datetime.now()

        fear_comps = article.get("fear_components", "[]")
        if isinstance(fear_comps, str):
            fear_comps = json.loads(fear_comps)

        lenders = article.get("lenders_mentioned", "[]")
        if isinstance(lenders, str):
            lenders = json.loads(lenders)

        results.append(DocumentAnalysis(
            doc_id=article["id"],
            title=article["title"],
            source=article.get("source", "Unknown"),
            source_type="scraped",
            published_date=pub_date if isinstance(pub_date, datetime) else datetime.now(),
            url=article.get("url"),
            sentiment=article.get("sentiment", "NEUTRAL"),
            sentiment_score=article.get("sentiment_score", 0),
            intensity=article.get("intensity", 3),
            fear_components=fear_comps,
            temporal="MEDIUM_TERM",
            entities=[],
            lenders_mentioned=lenders,
            projects_mentioned=[],
            policies_mentioned=[],
            confidence=article.get("confidence", 0.5),
            attention_highlights=[article.get("summary", "")],
            processed_at=datetime.fromisoformat(article["processed_at"]) if article.get("processed_at") else datetime.now(),
        ))

    return results


@router.get("/fear-components/history")
async def get_fear_component_history(
    component: Optional[str] = Query(
        default=None,
        description="Specific component or 'all'"
    ),
    lookback_days: int = Query(default=90, le=365),
):
    """
    Get historical values for fear components.

    Used for fear breakdown chart on dashboard.
    """
    history_data = db.get_sentiment_history(days=lookback_days)

    if history_data:
        components = [
            "regulatory_risk", "technology_risk", "feedstock_risk",
            "counterparty_risk", "market_risk", "esg_concerns"
        ]

        history = {}
        for comp in components:
            if component and component != "all" and comp != component:
                continue
            history[comp] = []
            for item in history_data:
                fear = item.get("fear_breakdown", {})
                history[comp].append({
                    "date": item["index_date"],
                    "value": fear.get(comp, 0)
                })

        return history

    # Mock data fallback
    components = [
        "regulatory_risk", "technology_risk", "feedstock_risk",
        "counterparty_risk", "market_risk", "esg_concerns"
    ]

    history = {}
    for comp in components:
        if component and component != "all" and comp != component:
            continue
        history[comp] = [
            {"date": (date.today() - timedelta(days=i)).isoformat(), "value": 20 + (hash(comp + str(i)) % 30)}
            for i in range(lookback_days, 0, -1)
        ]

    return history


# ============================================================================
# Endpoints - Pipeline Control
# ============================================================================

@router.post("/pipeline/run")
async def trigger_pipeline(background_tasks: BackgroundTasks):
    """
    Trigger the data pipeline to scrape and analyze new articles.

    Runs in the background and returns immediately.
    """
    background_tasks.add_task(run_pipeline)
    return {
        "status": "started",
        "message": "Pipeline started in background. Check /documents/feed for new articles."
    }


@router.post("/pipeline/refresh-index")
async def trigger_refresh_index():
    """
    Refresh the sentiment index from existing data.

    Use this to recalculate the index without scraping new articles.
    """
    result = await refresh_sentiment_index()
    return {
        "status": "completed",
        "result": result,
    }


# ============================================================================
# Endpoints - Alerts
# ============================================================================

@router.get("/alerts", response_model=List[SentimentAlert])
async def get_sentiment_alerts():
    """Get configured sentiment alerts."""
    return [
        SentimentAlert(
            id="alert1",
            name="Bullish Spike",
            condition="overall_index > 60",
            threshold=60,
            is_active=True,
            last_triggered=None,
        ),
        SentimentAlert(
            id="alert2",
            name="Bearish Warning",
            condition="overall_index < -30",
            threshold=-30,
            is_active=True,
            last_triggered=datetime.now() - timedelta(days=15),
        ),
    ]


@router.post("/alerts")
async def create_sentiment_alert(alert: SentimentAlert):
    """Create a new sentiment alert."""
    return {"status": "created", "alert_id": alert.id}


@router.delete("/alerts/{alert_id}")
async def delete_sentiment_alert(alert_id: str):
    """Delete a sentiment alert."""
    return {"status": "deleted", "alert_id": alert_id}
