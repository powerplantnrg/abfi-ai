"""
ABFI Intelligence Suite - Lending Sentiment API

Product 1: Lending Sentiment Dashboard
Provides lending sentiment index, fear components, and document analysis.
"""

from datetime import date, datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Query, UploadFile, File, HTTPException
from pydantic import BaseModel, Field


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
# Endpoints - Dashboard Data
# ============================================================================

@router.get("/index", response_model=SentimentIndex)
async def get_current_sentiment_index():
    """
    Get the current lending sentiment index.

    Returns overall index, document counts, and fear component breakdown.
    Used for KPI cards on dashboard.
    """
    # Mock data matching dashboard wireframe
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


@router.get("/index/history", response_model=List[SentimentIndex])
async def get_sentiment_history(
    lookback_days: int = Query(default=365, ge=1, le=730),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
):
    """
    Get historical sentiment index time series.

    Used for main sentiment trend chart on dashboard.

    - **lookback_days**: Number of days to retrieve (default 365)
    - **start_date**: Optional start date filter
    - **end_date**: Optional end date filter
    """
    # Generate mock historical data
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

    - **period**: Time period (1m, 3m, 6m, 12m, 24m)
    """
    periods = {"1m": 30, "3m": 90, "6m": 180, "12m": 365, "24m": 730}
    days = periods.get(period, 365)

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
            trend=[score + i for i in range(-5, 5)],  # Mock sparkline
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
    # Mock documents
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

    # Mock analysis result
    return DocumentAnalysis(
        doc_id="analysis_" + datetime.now().strftime("%Y%m%d%H%M%S"),
        title="Analyzed Document",
        source="User Upload" if file else ("URL" if url else "Text Input"),
        source_type="upload",
        published_date=datetime.now(),
        sentiment="BULLISH",
        sentiment_score=0.75,
        intensity=4,
        fear_components=["REGULATORY_RISK", "TECHNOLOGY_RISK"],
        temporal="MEDIUM_TERM",
        entities=[
            EntityAnnotation(text="CEFC", label="LENDER", start=45, end=49),
            EntityAnnotation(text="bioenergy project", label="PROJECT", start=100, end=117),
        ],
        lenders_mentioned=["CEFC"],
        projects_mentioned=["bioenergy project"],
        policies_mentioned=[],
        confidence=0.89,
        attention_highlights=["strong lending appetite", "favorable terms"],
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
    # Would query database
    return []


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
    # Would save to database
    return {"status": "created", "alert_id": alert.id}


@router.delete("/alerts/{alert_id}")
async def delete_sentiment_alert(alert_id: str):
    """Delete a sentiment alert."""
    return {"status": "deleted", "alert_id": alert_id}
