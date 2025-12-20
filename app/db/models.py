"""
Database models for ABFI Intelligence Suite.

PostgreSQL with JSONB columns for flexible schema evolution.
Implements storage for:
- Data sources and raw documents
- Processed articles with NLP analysis
- Labelling infrastructure
- Price data and counterparty ratings
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


# ============================================================================
# Data Source Models
# ============================================================================

class Source(BaseModel):
    """Data source configuration."""
    id: int = Field(default=None)
    name: str = Field(..., max_length=100)
    base_url: str
    scraper_type: str  # aemo, cer, reneweconomy, ckan, arena, cefc
    scraper_config: dict = {}  # JSONB - scraper-specific configuration
    priority: int = Field(default=5, ge=1, le=10)
    is_active: bool = True
    rate_limit_seconds: float = 1.0
    last_scraped: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        from_attributes = True


class RawDocument(BaseModel):
    """Raw document from data sources."""
    id: UUID = Field(default_factory=uuid4)
    source_id: int
    url: str
    content_hash: str = Field(..., max_length=64)  # SHA-256
    raw_content: str
    metadata: dict = {}  # JSONB - source-specific metadata
    http_status: int = 200
    scraped_at: datetime = Field(default_factory=datetime.now)

    class Config:
        from_attributes = True


class ProcessedArticle(BaseModel):
    """Processed and analyzed article."""
    id: UUID = Field(default_factory=uuid4)
    raw_document_id: UUID
    title: str
    published_date: Optional[datetime] = None
    author: Optional[str] = None
    content_text: str  # Cleaned text content
    summary: Optional[str] = None

    # NLP analysis results (JSONB)
    entities: dict = {}  # Extracted entities
    sentiment_scores: dict = {}  # Model predictions
    keywords: list[str] = []
    topics: list[str] = []

    # Classification
    is_bioenergy_relevant: bool = True
    relevance_score: float = 0.0

    processed_at: datetime = Field(default_factory=datetime.now)

    class Config:
        from_attributes = True


# ============================================================================
# Labelling Infrastructure Models
# ============================================================================

class LabellingProject(BaseModel):
    """Label Studio project configuration."""
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    label_config: dict  # Label Studio XML as JSON
    expert_instruction: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        from_attributes = True


class LabellingTask(BaseModel):
    """Labelling task for annotation."""
    id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    document_id: Optional[UUID] = None  # Links to ProcessedArticle
    data: dict  # {"text": "...", "source": "...", "metadata": {...}}
    priority_score: float = 0.0  # Uncertainty score for active learning
    is_honeypot: bool = False
    honeypot_labels: Optional[dict] = None  # Gold standard for honeypots
    status: str = "pending"  # pending, assigned, completed, adjudication
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        from_attributes = True


class Annotation(BaseModel):
    """
    Annotation result from labeller.

    Example result:
    {
        "sentiment": "BULLISH",
        "intensity": 4,
        "fear_components": ["REGULATORY_RISK", "FEEDSTOCK_RISK"],
        "temporal": "MEDIUM_TERM",
        "entities": [
            {"start": 45, "end": 49, "label": "LENDER", "text": "CEFC"},
            {"start": 120, "end": 145, "label": "PROJECT", "text": "Opal Bio Energy"}
        ]
    }
    """
    id: UUID = Field(default_factory=uuid4)
    task_id: UUID
    annotator_id: str
    result: dict  # Full annotation result
    lead_time_seconds: Optional[int] = None
    honeypot_correct: Optional[bool] = None
    is_consensus: bool = False  # Final consensus label
    completed_at: datetime = Field(default_factory=datetime.now)

    class Config:
        from_attributes = True


class AgreementMetric(BaseModel):
    """Inter-annotator agreement metrics."""
    id: int = Field(default=None)
    project_id: UUID
    metric_type: str  # kappa, krippendorff_alpha, fleiss_kappa
    label_name: str   # sentiment, intensity, fear_components_*
    score: float
    sample_size: int
    annotator_ids: list[str] = []
    calculated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        from_attributes = True


# ============================================================================
# Feedstock Price Models
# ============================================================================

class FeedstockPrice(BaseModel):
    """Feedstock price data point."""
    id: UUID = Field(default_factory=uuid4)
    commodity: str  # UCO, tallow, canola, palm_oil
    region: str  # AUS, SEA, EU, NA
    price: float  # USD or AUD per MT
    currency: str = "AUD"
    unit: str = "MT"  # Metric tonnes

    # OHLC for candlestick charts
    open_price: Optional[float] = None
    high_price: Optional[float] = None
    low_price: Optional[float] = None
    close_price: Optional[float] = None
    volume: Optional[int] = None

    source: str  # platts, argus, internal
    price_date: datetime
    recorded_at: datetime = Field(default_factory=datetime.now)

    class Config:
        from_attributes = True


class ForwardCurve(BaseModel):
    """Forward price curve data."""
    id: UUID = Field(default_factory=uuid4)
    commodity: str
    region: str
    spot_price: float
    forward_prices: dict  # {"M3": 1250, "M6": 1280, "M9": 1300, "M12": 1320}
    curve_shape: str  # contango, backwardation, flat
    as_of_date: datetime
    source: str

    class Config:
        from_attributes = True


# ============================================================================
# Counterparty Risk Models
# ============================================================================

class CounterpartyRating(BaseModel):
    """Counterparty risk rating (BeZero-style)."""
    id: UUID = Field(default_factory=uuid4)
    counterparty_name: str
    counterparty_type: str  # supplier, offtaker, developer

    # Risk ratings
    overall_risk: str  # Low, Medium, High
    risk_score: float = Field(..., ge=0, le=100)

    # Component scores
    financial_health: float = Field(..., ge=0, le=100)
    operational_reliability: float = Field(..., ge=0, le=100)
    contract_compliance: float = Field(..., ge=0, le=100)
    esg_score: Optional[float] = None

    # Track record
    volume_mt: Optional[float] = None  # Historical volume
    reliability_pct: Optional[float] = None  # Delivery reliability %
    price_tier: Optional[str] = None  # Spot + premium/discount

    # Metadata
    assessment_date: datetime
    assessor: Optional[str] = None
    notes: Optional[str] = None
    supporting_docs: list[str] = []

    class Config:
        from_attributes = True


# ============================================================================
# Policy Tracker Models
# ============================================================================

class PolicyTracker(BaseModel):
    """Policy and regulatory tracking."""
    id: UUID = Field(default_factory=uuid4)
    title: str
    jurisdiction: str  # Federal, QLD, NSW, VIC, SA, WA
    policy_type: str  # mandate, incentive, regulation, consultation

    # Status tracking
    status: str  # proposed, review, enacted, expired
    current_stage: Optional[str] = None

    # Timeline
    introduced_date: Optional[datetime] = None
    consultation_start: Optional[datetime] = None
    consultation_end: Optional[datetime] = None
    expected_decision: Optional[datetime] = None
    enacted_date: Optional[datetime] = None
    effective_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None

    # Content
    summary: str
    full_text_url: Optional[str] = None
    key_provisions: list[str] = []
    affected_sectors: list[str] = []

    # Impact assessment
    impact_score: Optional[float] = None
    market_impact: Optional[str] = None  # bullish, bearish, neutral

    # Metadata
    source_url: Optional[str] = None
    last_updated: datetime = Field(default_factory=datetime.now)
    created_at: datetime = Field(default_factory=datetime.now)

    class Config:
        from_attributes = True


class CarbonRevenue(BaseModel):
    """Carbon revenue calculation results."""
    id: UUID = Field(default_factory=uuid4)
    scenario_name: str
    project_type: str  # bioenergy_plant, waste_to_energy, biogas

    # Inputs
    annual_output_tonnes: float
    emission_factor: float  # tCO2 per tonne
    baseline_year: int
    carbon_price: float  # AUD per tCO2

    # Calculated revenues
    accu_credits: int
    accu_revenue: float
    safeguard_benefit: float
    total_annual_revenue: float

    # Sensitivity
    sensitivity_low: float  # -20% carbon price
    sensitivity_high: float  # +20% carbon price

    calculated_at: datetime = Field(default_factory=datetime.now)

    class Config:
        from_attributes = True
