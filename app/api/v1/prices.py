"""
ABFI Intelligence Suite - Feedstock Price Index API
"""

from datetime import date
from typing import List, Optional
from enum import Enum
from fastapi import APIRouter, Query, Path
from pydantic import BaseModel, Field


router = APIRouter()


class FeedstockType(str, Enum):
    """Available feedstock types."""
    UCO = "UCO"  # Used Cooking Oil
    TAL = "TAL"  # Tallow
    CAN = "CAN"  # Canola Oil
    RES = "RES"  # Agricultural Residue
    BAM = "BAM"  # Bamboo Biomass


class Region(str, Enum):
    """Australian regions."""
    NAT = "NAT"  # National
    VIC = "VIC"
    QLD = "QLD"
    NSW = "NSW"
    WA = "WA"
    SA = "SA"


class AssessmentType(str, Enum):
    """Price assessment methodology."""
    TRANSACTION_BASED = "transaction_based"
    INDICATIVE = "indicative"
    INTERPOLATED = "interpolated"


# Response Models
class PriceAssessment(BaseModel):
    """Weekly price assessment."""
    index_code: str
    week_ending: date
    price: float = Field(..., description="AUD per tonne")
    price_low: float
    price_high: float
    currency: str = "AUD"
    unit: str = "per_tonne"
    basis: str = "delivered"
    transaction_count: int
    total_volume: float
    assessment_type: AssessmentType
    methodology_version: str = "1.0"


class PriceIndexSeries(BaseModel):
    """Time series of price assessments."""
    index_code: str
    feedstock: FeedstockType
    region: Region
    assessments: List[PriceAssessment]
    period_start: date
    period_end: date
    average_price: float
    volatility_30d: Optional[float]


class ForwardCurve(BaseModel):
    """Forward price curve."""
    index_code: str
    as_of_date: date
    tenors: List[dict]  # [{tenor: "1M", price: 1250.00}, ...]
    methodology: str


# Endpoints
@router.get("/index/{feedstock}", response_model=PriceIndexSeries)
async def get_price_index(
    feedstock: FeedstockType = Path(..., description="Feedstock type"),
    region: Region = Query(default=Region.NAT, description="Region filter"),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
):
    """
    Get feedstock price index time series.

    Returns IOSCO-compliant weekly price assessments for the specified
    feedstock and region.

    - **feedstock**: UCO, TAL, CAN, RES, or BAM
    - **region**: NAT (national), VIC, QLD, NSW, WA, SA
    """
    index_code = f"ABFI-{feedstock.value}-{region.value}"

    # TODO: Implement database query
    return PriceIndexSeries(
        index_code=index_code,
        feedstock=feedstock,
        region=region,
        assessments=[
            PriceAssessment(
                index_code=index_code,
                week_ending=date.today(),
                price=1180.50,
                price_low=1120.00,
                price_high=1240.00,
                transaction_count=12,
                total_volume=2450.0,
                assessment_type=AssessmentType.TRANSACTION_BASED,
            )
        ],
        period_start=date(2024, 1, 1),
        period_end=date.today(),
        average_price=1175.25,
        volatility_30d=0.045,
    )


@router.get("/index/{feedstock}/latest", response_model=PriceAssessment)
async def get_latest_price(
    feedstock: FeedstockType,
    region: Region = Query(default=Region.NAT),
):
    """Get the most recent price assessment for a feedstock."""
    # TODO: Implement
    pass


@router.get("/forward-curve/{feedstock}", response_model=ForwardCurve)
async def get_forward_curve(
    feedstock: FeedstockType,
    region: Region = Query(default=Region.NAT),
):
    """
    Get forward price curve for feedstock.

    Returns implied forward prices based on contract analysis
    and seasonal adjustments.
    """
    # TODO: Implement
    pass


@router.get("/summary")
async def get_price_summary():
    """
    Get summary of all price indices.

    Returns latest prices for all feedstock/region combinations
    with week-over-week changes.
    """
    # TODO: Implement
    pass


@router.get("/methodology")
async def get_methodology():
    """
    Get price index methodology documentation.

    Returns IOSCO-compliant methodology description including
    data sources, calculation methods, and governance.
    """
    return {
        "version": "1.0",
        "effective_date": "2024-01-01",
        "governance": {
            "oversight_committee": "ABFI Price Index Committee",
            "review_frequency": "quarterly",
        },
        "data_sources": [
            "ABFI.io verified transactions",
            "Renderer market intelligence",
            "Export parity calculations",
        ],
        "calculation": {
            "method": "volume_weighted_average",
            "outlier_treatment": "2.5_std_exclusion",
            "minimum_transactions": 3,
            "quality_normalization": True,
        },
        "publication": {
            "frequency": "weekly",
            "publication_day": "Friday",
            "publication_time": "17:00 AEST",
        },
    }
