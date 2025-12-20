"""
ABFI Intelligence Suite - Policy & Carbon Revenue API

Product 3: Policy & Carbon Revenue Dashboard
Policy tracking, mandate scenarios, and carbon revenue calculator.
"""

from datetime import date, datetime, timedelta
from typing import List, Optional
from enum import Enum
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field


router = APIRouter()


# ============================================================================
# Enums
# ============================================================================

class Jurisdiction(str, Enum):
    """Australian jurisdictions."""
    FEDERAL = "Federal"
    NSW = "NSW"
    VIC = "VIC"
    QLD = "QLD"
    WA = "WA"
    SA = "SA"
    TAS = "TAS"
    NT = "NT"
    ACT = "ACT"


class PolicyStatus(str, Enum):
    """Policy lifecycle status."""
    PROPOSED = "proposed"
    REVIEW = "review"
    ENACTED = "enacted"
    EXPIRED = "expired"


class PolicyType(str, Enum):
    """Types of policy documents."""
    MANDATE = "mandate"
    INCENTIVE = "incentive"
    REGULATION = "regulation"
    CONSULTATION = "consultation"
    FUNDING_PROGRAM = "funding_program"


# ============================================================================
# Response Models (aligned with dashboard wireframes)
# ============================================================================

class PolicyKPI(BaseModel):
    """Policy dashboard KPI card."""
    label: str
    value: int
    subtitle: str


class PolicyTimelineEvent(BaseModel):
    """Event on the policy timeline."""
    jurisdiction: str
    date: date
    event_type: str  # enacted, consultation_open, expected_decision
    title: str
    policy_id: Optional[str] = None


class PolicyKanbanItem(BaseModel):
    """Policy item for Kanban board."""
    id: str
    title: str
    jurisdiction: str
    policy_type: str
    status: str
    summary: Optional[str] = None


class Policy(BaseModel):
    """Full policy document."""
    id: str
    title: str
    jurisdiction: Jurisdiction
    policy_type: PolicyType
    status: PolicyStatus
    summary: str

    # Timeline
    introduced_date: Optional[date] = None
    consultation_start: Optional[date] = None
    consultation_end: Optional[date] = None
    expected_decision: Optional[date] = None
    enacted_date: Optional[date] = None
    effective_date: Optional[date] = None

    # Impact
    market_impact: Optional[str] = None  # bullish, bearish, neutral
    affected_sectors: List[str] = []
    key_provisions: List[str] = []

    source_url: Optional[str] = None
    last_updated: datetime


class MandateScenario(BaseModel):
    """Mandate scenario for comparison."""
    name: str
    mandate_level: str  # B20, B10, B5, No Mandate
    revenue_impact: float  # AUD


class CarbonCalculatorInput(BaseModel):
    """Carbon revenue calculator input."""
    project_type: str = "bioenergy_plant"
    annual_output_tonnes: float = 50000
    emission_factor: float = 0.85
    baseline_year: int = 2025
    carbon_price: float = 34.50


class CarbonCalculatorResult(BaseModel):
    """Carbon revenue calculation result."""
    accu_credits: int
    accu_revenue: float
    safeguard_benefit: float
    total_annual_revenue: float
    sensitivity_low: float
    sensitivity_high: float


class OfftakeAgreement(BaseModel):
    """Offtake market intelligence."""
    offtaker: str
    mandate: str
    volume: str
    term: str
    premium: str


class PolicyAlert(BaseModel):
    """Policy alert configuration."""
    id: str
    name: str
    condition: str
    is_active: bool
    last_triggered: Optional[datetime] = None


# ============================================================================
# Endpoints - Dashboard KPIs
# ============================================================================

@router.get("/kpis", response_model=List[PolicyKPI])
async def get_policy_kpis():
    """
    Get policy dashboard KPI cards.

    Returns counts for active policies, consultations, deadlines, ACCU price.
    """
    return [
        PolicyKPI(label="Active Policies", value=12, subtitle="2 new"),
        PolicyKPI(label="In Review Consults", value=5, subtitle="2 closing"),
        PolicyKPI(label="Upcoming Deadlines", value=3, subtitle="This week"),
        PolicyKPI(label="ACCU Price", value=35, subtitle="+$1.20"),
    ]


@router.get("/accu-price")
async def get_accu_price():
    """Get current ACCU price."""
    return {
        "price": 34.50,
        "currency": "AUD",
        "unit": "tCO2",
        "change": 1.20,
        "change_pct": 3.6,
        "source": "CER Quarterly Report",
        "as_of_date": date.today().isoformat(),
    }


# ============================================================================
# Endpoints - Policy Timeline
# ============================================================================

@router.get("/timeline", response_model=List[PolicyTimelineEvent])
async def get_policy_timeline(
    year: int = Query(default=2025),
    jurisdictions: Optional[List[str]] = Query(default=None),
):
    """
    Get policy timeline events for Gantt-style visualization.

    Used for policy timeline chart showing jurisdiction swimlanes.
    """
    events = [
        PolicyTimelineEvent(jurisdiction="Federal", date=date(2025, 2, 15), event_type="enacted", title="NGER Update"),
        PolicyTimelineEvent(jurisdiction="Federal", date=date(2025, 5, 1), event_type="consultation_open", title="RFS Update"),
        PolicyTimelineEvent(jurisdiction="Federal", date=date(2025, 8, 15), event_type="expected_decision", title="SAF Roadmap"),
        PolicyTimelineEvent(jurisdiction="QLD", date=date(2025, 3, 1), event_type="enacted", title="SAF Mandate"),
        PolicyTimelineEvent(jurisdiction="QLD", date=date(2025, 6, 15), event_type="consultation_open", title="B20 Review"),
        PolicyTimelineEvent(jurisdiction="NSW", date=date(2025, 4, 10), event_type="enacted", title="LCFS Phase 1"),
        PolicyTimelineEvent(jurisdiction="NSW", date=date(2025, 7, 20), event_type="consultation_open", title="B2 Expansion"),
        PolicyTimelineEvent(jurisdiction="VIC", date=date(2025, 2, 1), event_type="enacted", title="B20 Mandate"),
        PolicyTimelineEvent(jurisdiction="VIC", date=date(2025, 10, 1), event_type="expected_decision", title="ERF Expansion"),
        PolicyTimelineEvent(jurisdiction="SA", date=date(2025, 5, 15), event_type="enacted", title="Biofuel Incentive"),
        PolicyTimelineEvent(jurisdiction="SA", date=date(2025, 8, 1), event_type="consultation_open", title="RNG Target"),
        PolicyTimelineEvent(jurisdiction="WA", date=date(2025, 6, 1), event_type="enacted", title="Green Hydrogen"),
        PolicyTimelineEvent(jurisdiction="WA", date=date(2025, 11, 15), event_type="consultation_open", title="SAF Study"),
    ]

    if jurisdictions:
        events = [e for e in events if e.jurisdiction in jurisdictions]

    return events


# ============================================================================
# Endpoints - Policy Kanban
# ============================================================================

@router.get("/kanban", response_model=dict)
async def get_policy_kanban():
    """
    Get policy status Kanban board data.

    Returns policies grouped by status for drag-and-drop visualization.
    """
    return {
        "proposed": [
            PolicyKanbanItem(id="p1", title="SAF Mandate QLD", jurisdiction="QLD", policy_type="mandate", status="proposed"),
            PolicyKanbanItem(id="p2", title="LCFS NSW", jurisdiction="NSW", policy_type="regulation", status="proposed"),
        ],
        "review": [
            PolicyKanbanItem(id="p3", title="RFS Update Fed", jurisdiction="Federal", policy_type="regulation", status="review"),
            PolicyKanbanItem(id="p4", title="NGER Threshold", jurisdiction="Federal", policy_type="regulation", status="review"),
        ],
        "enacted": [
            PolicyKanbanItem(id="p5", title="B20 VIC", jurisdiction="VIC", policy_type="mandate", status="enacted"),
            PolicyKanbanItem(id="p6", title="ERF Expansion", jurisdiction="Federal", policy_type="incentive", status="enacted"),
        ],
    }


# ============================================================================
# Endpoints - Policy Tracker
# ============================================================================

@router.get("/tracker", response_model=List[Policy])
async def get_policy_tracker(
    jurisdiction: Optional[List[Jurisdiction]] = Query(None),
    status: Optional[List[PolicyStatus]] = Query(None),
    policy_type: Optional[List[PolicyType]] = Query(None),
    limit: int = Query(default=50, le=200),
    offset: int = 0,
):
    """
    Get policy tracker with filters.

    Tracks federal and state/territory policies relevant to bioenergy.
    """
    policies = [
        Policy(
            id="pol1",
            title="Queensland SAF Mandate",
            jurisdiction=Jurisdiction.QLD,
            policy_type=PolicyType.MANDATE,
            status=PolicyStatus.PROPOSED,
            summary="Proposed 2% SAF blending mandate for aviation fuel",
            introduced_date=date(2024, 10, 15),
            consultation_start=date(2025, 1, 15),
            consultation_end=date(2025, 3, 15),
            expected_decision=date(2025, 6, 1),
            market_impact="bullish",
            affected_sectors=["aviation", "SAF production"],
            key_provisions=["2% initial blend", "Annual increase pathway"],
            last_updated=datetime.now(),
        ),
        Policy(
            id="pol2",
            title="Victorian B20 Biodiesel Mandate",
            jurisdiction=Jurisdiction.VIC,
            policy_type=PolicyType.MANDATE,
            status=PolicyStatus.ENACTED,
            summary="20% biodiesel blending requirement for diesel sales",
            enacted_date=date(2024, 7, 1),
            effective_date=date(2025, 1, 1),
            market_impact="bullish",
            affected_sectors=["biodiesel", "transport"],
            last_updated=datetime.now(),
        ),
    ]

    if jurisdiction:
        policies = [p for p in policies if p.jurisdiction in jurisdiction]
    if status:
        policies = [p for p in policies if p.status in status]

    return policies[offset:offset + limit]


# ============================================================================
# Endpoints - Carbon Revenue Calculator
# ============================================================================

@router.post("/carbon-calculator", response_model=CarbonCalculatorResult)
async def calculate_carbon_revenue(input: CarbonCalculatorInput):
    """
    Calculate carbon revenue for a bioenergy project.

    Returns ACCU credits, revenue projections, and sensitivity analysis.
    """
    # Calculate ACCU credits
    accu_credits = int(input.annual_output_tonnes * input.emission_factor)
    accu_revenue = accu_credits * input.carbon_price

    # Safeguard mechanism benefit (simplified)
    safeguard_benefit = accu_credits * 0.5 * input.carbon_price

    total = accu_revenue + safeguard_benefit

    return CarbonCalculatorResult(
        accu_credits=accu_credits,
        accu_revenue=accu_revenue,
        safeguard_benefit=safeguard_benefit,
        total_annual_revenue=total,
        sensitivity_low=total * 0.8,  # -20% carbon price
        sensitivity_high=total * 1.2,  # +20% carbon price
    )


@router.get("/carbon-calculator/scenarios")
async def get_carbon_scenarios():
    """Get predefined carbon revenue scenarios."""
    return {
        "scenarios": [
            {
                "name": "Bioenergy Plant",
                "annual_output_tonnes": 50000,
                "emission_factor": 0.85,
                "description": "Standard bioenergy electricity generation",
            },
            {
                "name": "Waste-to-Energy",
                "annual_output_tonnes": 30000,
                "emission_factor": 1.2,
                "description": "Municipal solid waste processing",
            },
            {
                "name": "Biogas Facility",
                "annual_output_tonnes": 20000,
                "emission_factor": 0.6,
                "description": "Agricultural biogas capture and use",
            },
        ],
    }


# ============================================================================
# Endpoints - Mandate Scenarios
# ============================================================================

@router.get("/mandate-scenarios", response_model=List[MandateScenario])
async def get_mandate_scenarios():
    """
    Get mandate scenario comparison for revenue impact.

    Used for horizontal bar chart comparing mandate levels.
    """
    return [
        MandateScenario(name="B20 Mandate", mandate_level="B20", revenue_impact=2_400_000),
        MandateScenario(name="B10 Mandate", mandate_level="B10", revenue_impact=1_200_000),
        MandateScenario(name="B5 Mandate", mandate_level="B5", revenue_impact=600_000),
        MandateScenario(name="No Mandate", mandate_level="None", revenue_impact=150_000),
    ]


# ============================================================================
# Endpoints - Offtake Market
# ============================================================================

@router.get("/offtake-market", response_model=List[OfftakeAgreement])
async def get_offtake_market():
    """
    Get offtake market intelligence.

    Shows active offtake agreements and premiums.
    """
    return [
        OfftakeAgreement(offtaker="Qantas SAF", mandate="SAF 2%", volume="25,000 kL", term="10 years", premium="+$0.45/L"),
        OfftakeAgreement(offtaker="BP Biodiesel", mandate="B5 Fed", volume="50,000 kL", term="5 years", premium="+$0.12/L"),
        OfftakeAgreement(offtaker="Viva Energy", mandate="B2 NSW", volume="15,000 kL", term="3 years", premium="+$0.08/L"),
    ]


# ============================================================================
# Endpoints - Consultations
# ============================================================================

@router.get("/consultations")
async def get_open_consultations():
    """
    Get currently open policy consultations.

    Returns active consultations with deadlines and relevance scoring.
    """
    return [
        {
            "id": "cons1",
            "title": "Renewable Fuel Standard Review",
            "jurisdiction": "Federal",
            "opens": date(2025, 1, 15).isoformat(),
            "closes": date(2025, 3, 15).isoformat(),
            "days_remaining": 45,
            "relevance": "high",
            "submission_url": "https://example.gov.au/consultation",
        },
        {
            "id": "cons2",
            "title": "Queensland Biofuel Mandate Expansion",
            "jurisdiction": "QLD",
            "opens": date(2025, 2, 1).isoformat(),
            "closes": date(2025, 4, 1).isoformat(),
            "days_remaining": 60,
            "relevance": "high",
        },
    ]


# ============================================================================
# Endpoints - Alerts
# ============================================================================

@router.get("/alerts", response_model=List[PolicyAlert])
async def get_policy_alerts():
    """Get configured policy alerts."""
    return [
        PolicyAlert(
            id="alert1",
            name="Consultation Deadline",
            condition="days_remaining < 7",
            is_active=True,
        ),
        PolicyAlert(
            id="alert2",
            name="New Policy Enacted",
            condition="status == enacted",
            is_active=True,
        ),
    ]


@router.post("/alerts")
async def create_policy_alert(alert: PolicyAlert):
    """Create a new policy alert."""
    return {"status": "created", "alert_id": alert.id}


@router.delete("/alerts/{alert_id}")
async def delete_policy_alert(alert_id: str):
    """Delete a policy alert."""
    return {"status": "deleted", "alert_id": alert_id}
