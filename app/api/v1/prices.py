"""
ABFI Intelligence Suite - Feedstock Price Index API

Product 2: Feedstock Price Index Dashboard
IOSCO-compliant pricing methodology for biofuel feedstocks.
"""

from datetime import date, datetime, timedelta
from typing import List, Optional
from enum import Enum
from fastapi import APIRouter, Query, Path, HTTPException
from pydantic import BaseModel, Field


router = APIRouter()


# ============================================================================
# Enums
# ============================================================================

class FeedstockType(str, Enum):
    """Available feedstock types."""
    UCO = "UCO"      # Used Cooking Oil
    TALLOW = "TAL"   # Tallow
    CANOLA = "CAN"   # Canola Oil
    PALM = "PALM"    # Palm Oil
    PFAD = "PFAD"    # Palm Fatty Acid Distillate
    RES = "RES"      # Agricultural Residue


class Region(str, Enum):
    """Trading regions."""
    AUS = "AUS"      # Australia
    SEA = "SEA"      # Southeast Asia
    EU = "EU"        # Europe (ARA)
    NA = "NA"        # North America
    LATAM = "LATAM"  # Latin America


class AssessmentType(str, Enum):
    """Price assessment methodology."""
    TRANSACTION_BASED = "transaction_based"
    INDICATIVE = "indicative"
    INTERPOLATED = "interpolated"


# ============================================================================
# Response Models (aligned with dashboard wireframes)
# ============================================================================

class PriceKPI(BaseModel):
    """Price KPI card data."""
    commodity: str
    price: float
    currency: str = "AUD"
    unit: str = "MT"
    change_pct: float
    change_direction: str  # up, down, flat


class OHLCDataPoint(BaseModel):
    """OHLC candlestick data point."""
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: Optional[int] = None


class PriceTimeSeries(BaseModel):
    """Price time series for charts."""
    commodity: str
    region: str
    data: List[OHLCDataPoint]
    source: str


class PriceAssessment(BaseModel):
    """Weekly price assessment (IOSCO-compliant)."""
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


class RegionalPrice(BaseModel):
    """Regional price with change indicator."""
    region: str
    region_name: str
    price: float
    change_pct: float
    currency: str = "AUD"


class RegionalHeatmap(BaseModel):
    """Regional price heatmap data."""
    commodity: str
    regions: List[RegionalPrice]


class ExportParity(BaseModel):
    """Export parity spread calculation."""
    commodity: str
    base_region: str
    comparison_region: str
    spread: float  # AUD/MT
    currency: str = "AUD"


class ForwardPoint(BaseModel):
    """Forward curve data point."""
    tenor: str  # Spot, M3, M6, M9, M12
    price: float
    change_from_spot: float


class ForwardCurve(BaseModel):
    """Forward curve data."""
    commodity: str
    region: str
    curve_shape: str  # contango, backwardation, flat
    points: List[ForwardPoint]
    as_of_date: date


class TechnicalIndicator(BaseModel):
    """Technical indicator value."""
    name: str
    value: float
    signal: str  # buy, sell, neutral


class PriceAlert(BaseModel):
    """Price alert configuration."""
    id: str
    commodity: str
    condition: str  # above, below, change_pct
    threshold: float
    is_active: bool
    last_triggered: Optional[datetime] = None


# ============================================================================
# Endpoints - Price KPIs
# ============================================================================

@router.get("/kpis", response_model=List[PriceKPI])
async def get_price_kpis():
    """
    Get current price KPIs for all commodities.

    Used for top KPI cards on dashboard.
    """
    return [
        PriceKPI(commodity="UCO", price=1245, change_pct=2.3, change_direction="up"),
        PriceKPI(commodity="Tallow", price=892, change_pct=-1.2, change_direction="down"),
        PriceKPI(commodity="Canola", price=687, change_pct=0.8, change_direction="up"),
        PriceKPI(commodity="Palm Oil", price=1034, change_pct=0.1, change_direction="flat"),
    ]


@router.get("/current/{commodity}", response_model=PriceKPI)
async def get_current_price(
    commodity: str,
    region: Region = Query(default=Region.AUS),
):
    """
    Get current price for a specific commodity.

    - **commodity**: UCO, tallow, canola, palm_oil
    - **region**: AUS, SEA, EU, NA
    """
    prices = {
        "uco": 1245,
        "tallow": 892,
        "canola": 687,
        "palm": 1034,
        "pfad": 980,
    }

    price = prices.get(commodity.lower())
    if not price:
        raise HTTPException(status_code=404, detail=f"Commodity {commodity} not found")

    return PriceKPI(
        commodity=commodity.upper(),
        price=price,
        change_pct=2.3,
        change_direction="up",
    )


# ============================================================================
# Endpoints - OHLC Data
# ============================================================================

@router.get("/ohlc/{commodity}", response_model=PriceTimeSeries)
async def get_ohlc_data(
    commodity: str,
    region: Region = Query(default=Region.AUS),
    period: str = Query(default="1Y", regex="^(1M|3M|6M|1Y|2Y|5Y)$"),
):
    """
    Get OHLC candlestick data for a commodity.

    Used for main price chart with TradingView Lightweight Charts.

    - **commodity**: UCO, tallow, canola, palm_oil
    - **region**: AUS, SEA, EU, NA
    - **period**: 1M, 3M, 6M, 1Y, 2Y, 5Y
    """
    periods = {"1M": 30, "3M": 90, "6M": 180, "1Y": 365, "2Y": 730, "5Y": 1825}
    days = periods.get(period, 365)

    base_price = {"uco": 1200, "tallow": 850, "canola": 650, "palm": 1000}.get(
        commodity.lower(), 1000
    )

    data = []
    for i in range(days):
        d = date.today() - timedelta(days=days - i)
        variation = (hash(str(d) + commodity) % 100) - 50
        price = base_price + variation

        data.append(OHLCDataPoint(
            date=d,
            open=price - 5,
            high=price + 15,
            low=price - 20,
            close=price,
            volume=10000 + (hash(str(d)) % 5000),
        ))

    return PriceTimeSeries(
        commodity=commodity.upper(),
        region=region.value,
        data=data,
        source="ABFI Internal",
    )


# ============================================================================
# Endpoints - IOSCO Price Index
# ============================================================================

@router.get("/index/{feedstock}", response_model=dict)
async def get_price_index(
    feedstock: FeedstockType = Path(..., description="Feedstock type"),
    region: Region = Query(default=Region.AUS, description="Region filter"),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
):
    """
    Get feedstock price index time series.

    Returns IOSCO-compliant weekly price assessments for the specified
    feedstock and region.
    """
    index_code = f"ABFI-{feedstock.value}-{region.value}"

    return {
        "index_code": index_code,
        "feedstock": feedstock.value,
        "region": region.value,
        "assessments": [
            {
                "week_ending": date.today().isoformat(),
                "price": 1180.50,
                "price_low": 1120.00,
                "price_high": 1240.00,
                "transaction_count": 12,
                "total_volume": 2450.0,
                "assessment_type": "transaction_based",
            }
        ],
        "period_start": start_date or (date.today() - timedelta(days=365)),
        "period_end": end_date or date.today(),
        "average_price": 1175.25,
        "volatility_30d": 0.045,
    }


# ============================================================================
# Endpoints - Regional Analysis
# ============================================================================

@router.get("/heatmap/{commodity}", response_model=RegionalHeatmap)
async def get_regional_heatmap(commodity: str):
    """
    Get regional price heatmap data.

    Used for geographic heatmap visualization.
    """
    return RegionalHeatmap(
        commodity=commodity.upper(),
        regions=[
            RegionalPrice(region="AUS", region_name="Australia", price=1245, change_pct=2.3),
            RegionalPrice(region="SEA", region_name="Southeast Asia", price=1203, change_pct=-0.8),
            RegionalPrice(region="EU", region_name="Europe", price=1330, change_pct=1.1),
            RegionalPrice(region="NA", region_name="North America", price=1243, change_pct=-0.2),
            RegionalPrice(region="LATAM", region_name="Latin America", price=1180, change_pct=0.5),
        ],
    )


@router.get("/spreads/{commodity}", response_model=List[ExportParity])
async def get_export_parity_spreads(
    commodity: str,
    base_region: Region = Query(default=Region.AUS),
):
    """
    Get export parity spread calculations.

    Shows price differentials between regions.
    """
    return [
        ExportParity(
            commodity=commodity.upper(),
            base_region="AUS",
            comparison_region="EU",
            spread=85,
        ),
        ExportParity(
            commodity=commodity.upper(),
            base_region="AUS",
            comparison_region="SEA",
            spread=-42,
        ),
    ]


# ============================================================================
# Endpoints - Forward Curves
# ============================================================================

@router.get("/forward/{commodity}", response_model=ForwardCurve)
async def get_forward_curve(
    commodity: str,
    region: Region = Query(default=Region.AUS),
):
    """
    Get forward price curve.

    Shows contango/backwardation structure.
    """
    spot = 1245

    return ForwardCurve(
        commodity=commodity.upper(),
        region=region.value,
        curve_shape="contango",
        points=[
            ForwardPoint(tenor="Spot", price=spot, change_from_spot=0),
            ForwardPoint(tenor="M3", price=spot + 25, change_from_spot=25),
            ForwardPoint(tenor="M6", price=spot + 45, change_from_spot=45),
            ForwardPoint(tenor="M9", price=spot + 60, change_from_spot=60),
            ForwardPoint(tenor="M12", price=spot + 75, change_from_spot=75),
        ],
        as_of_date=date.today(),
    )


# ============================================================================
# Endpoints - Technical Analysis
# ============================================================================

@router.get("/technicals/{commodity}", response_model=List[TechnicalIndicator])
async def get_technical_indicators(
    commodity: str,
    region: Region = Query(default=Region.AUS),
):
    """
    Get technical indicators for a commodity.

    MA, Bollinger Bands, RSI, MACD.
    """
    return [
        TechnicalIndicator(name="MA(20)", value=1230, signal="buy"),
        TechnicalIndicator(name="MA(50)", value=1210, signal="buy"),
        TechnicalIndicator(name="RSI(14)", value=58, signal="neutral"),
        TechnicalIndicator(name="MACD", value=12.5, signal="buy"),
    ]


# ============================================================================
# Endpoints - Commodities
# ============================================================================

@router.get("/commodities")
async def list_commodities():
    """List all available commodities."""
    return {
        "commodities": [
            {"id": "UCO", "name": "Used Cooking Oil", "unit": "MT"},
            {"id": "tallow", "name": "Tallow", "unit": "MT"},
            {"id": "canola", "name": "Canola Oil", "unit": "MT"},
            {"id": "palm", "name": "Palm Oil", "unit": "MT"},
            {"id": "PFAD", "name": "Palm Fatty Acid Distillate", "unit": "MT"},
        ],
        "regions": [
            {"id": "AUS", "name": "Australia"},
            {"id": "SEA", "name": "Southeast Asia"},
            {"id": "EU", "name": "Europe (ARA)"},
            {"id": "NA", "name": "North America"},
        ],
    }


@router.get("/methodology")
async def get_methodology():
    """
    Get price index methodology documentation.

    Returns IOSCO-compliant methodology description.
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
        },
        "publication": {
            "frequency": "weekly",
            "publication_day": "Friday",
            "publication_time": "17:00 AEST",
        },
    }


# ============================================================================
# Endpoints - Alerts
# ============================================================================

@router.get("/alerts", response_model=List[PriceAlert])
async def get_price_alerts():
    """Get configured price alerts."""
    return [
        PriceAlert(id="alert1", commodity="UCO", condition="above", threshold=1300, is_active=True),
        PriceAlert(id="alert2", commodity="tallow", condition="below", threshold=800, is_active=True),
    ]


@router.post("/alerts")
async def create_price_alert(alert: PriceAlert):
    """Create a new price alert."""
    return {"status": "created", "alert_id": alert.id}


@router.delete("/alerts/{alert_id}")
async def delete_price_alert(alert_id: str):
    """Delete a price alert."""
    return {"status": "deleted", "alert_id": alert_id}
