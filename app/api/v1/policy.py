"""
ABFI Intelligence Suite - Policy Intelligence API
"""

from datetime import date, datetime
from typing import List, Optional
from enum import Enum
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field


router = APIRouter()


class Jurisdiction(str, Enum):
    """Australian jurisdictions."""
    FEDERAL = "federal"
    NSW = "nsw"
    VIC = "vic"
    QLD = "qld"
    WA = "wa"
    SA = "sa"
    TAS = "tas"
    NT = "nt"
    ACT = "act"


class PolicyType(str, Enum):
    """Types of policy documents."""
    LEGISLATION = "legislation"
    REGULATION = "regulation"
    CONSULTATION = "consultation"
    FUNDING_PROGRAM = "funding_program"
    MINISTERIAL_STATEMENT = "ministerial_statement"
    AGENCY_GUIDANCE = "agency_guidance"
    INDUSTRY_STRATEGY = "industry_strategy"


class BiofuelRelevance(str, Enum):
    """Relevance to biofuel industry."""
    DIRECT = "direct"       # Explicitly about biofuels
    ADJACENT = "adjacent"   # Energy transition, relevant
    CONTEXTUAL = "contextual"  # General policy, minor relevance
    NONE = "none"


class FuelType(str, Enum):
    """Biofuel types covered."""
    SAF = "saf"
    BIODIESEL = "biodiesel"
    RENEWABLE_DIESEL = "renewable_diesel"
    BIOGAS = "biogas"
    BIOMETHANE = "biomethane"
    BIOETHANOL = "bioethanol"
    HYDROGEN = "hydrogen"


# Response Models
class PolicyUpdate(BaseModel):
    """Policy document/update."""
    id: str
    title: str
    source: str
    source_url: str
    jurisdiction: List[Jurisdiction]
    policy_type: PolicyType
    biofuel_relevance: BiofuelRelevance
    fuel_types: List[FuelType]
    policy_mechanisms: List[str]
    summary: str
    effective_dates: List[dict]  # [{type: "effective", date: ...}]
    key_entities: List[str]
    impact_score: float = Field(..., ge=0, le=1)
    published_date: date
    processed_date: datetime


class MandateScenario(BaseModel):
    """SAF mandate probability scenario."""
    name: str  # accelerated, base_case, delayed, no_mandate
    mandate_year: Optional[int]
    initial_blend_pct: float
    trajectory: str  # aggressive, moderate, conservative, voluntary_only
    probability: float = Field(..., ge=0, le=1)
    demand_projections: dict  # {year: {demand_litres, demand_tonnes}}
    key_assumptions: List[str]
    trigger_events: List[str]


class MandateScenarios(BaseModel):
    """Complete mandate scenario analysis."""
    scenarios: List[MandateScenario]
    last_updated: datetime
    key_signposts: List[dict]  # Events that would shift probabilities
    update_triggers: List[str]
    methodology_notes: str


class PolicyAlert(BaseModel):
    """Policy alert for significant changes."""
    id: str
    alert_type: str  # new_policy, amendment, deadline, consultation_open
    severity: str  # high, medium, low
    title: str
    summary: str
    action_required: Optional[str]
    deadline: Optional[date]
    created_at: datetime


# Endpoints
@router.get("/tracker", response_model=List[PolicyUpdate])
async def get_policy_updates(
    jurisdiction: Optional[List[Jurisdiction]] = Query(None),
    policy_type: Optional[List[PolicyType]] = Query(None),
    fuel_type: Optional[List[FuelType]] = Query(None),
    relevance: Optional[BiofuelRelevance] = None,
    since: Optional[datetime] = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
):
    """
    Get policy updates with optional filters.

    Tracks federal and 8 state/territory jurisdictions for
    relevant policy changes, consultations, and announcements.
    """
    # TODO: Implement
    pass


@router.get("/mandate-scenarios", response_model=MandateScenarios)
async def get_mandate_scenarios():
    """
    Get SAF mandate probability scenarios.

    Returns probabilistic scenarios for Australian SAF mandate timing
    and structure based on policy signals and international precedents.

    Scenarios include:
    - **Accelerated**: Earlier mandate (2027), aggressive trajectory
    - **Base case**: Moderate timing (2029), measured growth
    - **Delayed**: Later mandate (2032), conservative start
    - **No mandate**: Voluntary uptake only
    """
    return MandateScenarios(
        scenarios=[
            MandateScenario(
                name="accelerated",
                mandate_year=2027,
                initial_blend_pct=2.0,
                trajectory="aggressive",
                probability=0.15,
                demand_projections={
                    "2027": {"demand_litres": 170_000_000, "demand_tonnes": 136_000},
                    "2030": {"demand_litres": 510_000_000, "demand_tonnes": 408_000},
                },
                key_assumptions=[
                    "Strong political commitment post-2025 election",
                    "EU border adjustment pressure",
                    "Airline voluntary commitments accelerate",
                ],
                trigger_events=[
                    "Government announces SAF roadmap",
                    "Major airline long-term offtake",
                ],
            ),
            MandateScenario(
                name="base_case",
                mandate_year=2029,
                initial_blend_pct=1.0,
                trajectory="moderate",
                probability=0.45,
                demand_projections={
                    "2029": {"demand_litres": 85_000_000, "demand_tonnes": 68_000},
                    "2030": {"demand_litres": 170_000_000, "demand_tonnes": 136_000},
                },
                key_assumptions=[
                    "Policy consultation in 2025-2026",
                    "Legislation passed by 2028",
                    "Gradual ramp-up trajectory",
                ],
                trigger_events=[
                    "Consultation paper released",
                    "Industry working group formed",
                ],
            ),
        ],
        last_updated=datetime.now(),
        key_signposts=[
            {"event": "SAF consultation paper", "probability_shift": "+15% accelerated"},
            {"event": "Election policy announcement", "probability_shift": "variable"},
        ],
        update_triggers=[
            "Major policy announcement",
            "International mandate change",
            "Significant industry investment",
        ],
        methodology_notes="Based on political signal analysis, international precedents, and industry engagement.",
    )


@router.get("/alerts", response_model=List[PolicyAlert])
async def get_policy_alerts(
    severity: Optional[str] = None,
    since: Optional[datetime] = None,
):
    """
    Get policy alerts for significant changes.

    Alerts are generated for new policies, amendments, approaching
    deadlines, and consultation openings.
    """
    # TODO: Implement
    pass


@router.get("/consultations")
async def get_open_consultations():
    """
    Get currently open policy consultations.

    Returns active consultations with deadlines and relevance scoring.
    """
    # TODO: Implement
    pass


@router.get("/calendar")
async def get_policy_calendar(
    months_ahead: int = Query(default=6, le=24),
):
    """
    Get policy event calendar.

    Returns upcoming policy milestones, review dates, and
    expected announcements.
    """
    # TODO: Implement
    pass
