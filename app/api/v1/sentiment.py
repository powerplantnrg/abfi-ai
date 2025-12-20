"""
ABFI Intelligence Suite - Lending Sentiment API
"""

from datetime import date, datetime
from typing import List, Optional
from fastapi import APIRouter, Query, UploadFile, File, HTTPException
from pydantic import BaseModel, Field


router = APIRouter()


# Response Models
class FearComponents(BaseModel):
    """Fear component breakdown."""
    policy_reversal: float = Field(..., ge=0, le=1)
    technology_risk: float = Field(..., ge=0, le=1)
    offtake_uncertainty: float = Field(..., ge=0, le=1)
    feedstock_security: float = Field(..., ge=0, le=1)
    carbon_volatility: float = Field(..., ge=0, le=1)
    stranded_asset: float = Field(..., ge=0, le=1)


class SentimentIndex(BaseModel):
    """Daily sentiment index values."""
    date: date
    lending_appetite_index: float = Field(..., ge=-3, le=3)
    risk_perception_index: float = Field(..., ge=-3, le=3)
    fear_index: float = Field(..., ge=0, le=1)
    fear_components: FearComponents
    momentum_7d: float
    documents_processed: int
    confidence_interval: tuple[float, float]


class DocumentAnalysis(BaseModel):
    """Single document sentiment analysis result."""
    doc_id: str
    source: str
    source_type: str
    lending_appetite: float = Field(..., ge=-3, le=3)
    risk_perception: float = Field(..., ge=-3, le=3)
    fear_components: FearComponents
    entities: List[str]
    horizon: str  # short_term, medium_term, long_term
    attention_highlights: List[str]
    confidence: float
    processed_at: datetime


# Endpoints
@router.get("/index", response_model=List[SentimentIndex])
async def get_sentiment_index(
    lookback_days: int = Query(default=30, ge=1, le=365),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
):
    """
    Get the lending sentiment index time series.

    The index aggregates document-level sentiment predictions weighted by
    source authority, recency, and biofuel relevance.

    - **lookback_days**: Number of days to retrieve (default 30)
    - **start_date**: Optional start date filter
    - **end_date**: Optional end date filter
    """
    # TODO: Implement database query
    return [
        SentimentIndex(
            date=date.today(),
            lending_appetite_index=1.2,
            risk_perception_index=-0.5,
            fear_index=0.35,
            fear_components=FearComponents(
                policy_reversal=0.42,
                technology_risk=0.18,
                offtake_uncertainty=0.55,
                feedstock_security=0.31,
                carbon_volatility=0.28,
                stranded_asset=0.15,
            ),
            momentum_7d=0.15,
            documents_processed=127,
            confidence_interval=(1.0, 1.4),
        )
    ]


@router.get("/index/latest", response_model=SentimentIndex)
async def get_latest_sentiment():
    """Get the most recent sentiment index values."""
    # TODO: Implement
    pass


@router.post("/analyze", response_model=DocumentAnalysis)
async def analyze_document(
    file: Optional[UploadFile] = File(None),
    url: Optional[str] = None,
):
    """
    Analyze a document for lending sentiment.

    Upload a PDF/document or provide a URL to analyze.
    Returns detailed sentiment breakdown with attention highlights.
    """
    if not file and not url:
        raise HTTPException(
            status_code=400,
            detail="Either file or url must be provided"
        )

    # TODO: Implement document processing and inference
    pass


@router.get("/documents", response_model=List[DocumentAnalysis])
async def list_analyzed_documents(
    source_type: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
):
    """
    List analyzed documents with their sentiment scores.

    Filter by source type, date range, with pagination support.
    """
    # TODO: Implement
    pass


@router.get("/fear-components/history")
async def get_fear_component_history(
    component: str = Query(..., description="Fear component name"),
    lookback_days: int = Query(default=90, le=365),
):
    """
    Get historical values for a specific fear component.

    Useful for tracking how specific risk factors evolve over time.
    """
    # TODO: Implement
    pass
