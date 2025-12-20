"""
ABFI Intelligence Suite - Carbon Revenue Calculator API
"""

from datetime import date
from typing import List, Optional
from enum import Enum
from fastapi import APIRouter, Query
from pydantic import BaseModel, Field


router = APIRouter()


class ProjectType(str, Enum):
    """Biofuel project types."""
    SAF = "saf"
    BIODIESEL = "biodiesel"
    RENEWABLE_DIESEL = "renewable_diesel"
    BIOGAS = "biogas"
    BIOMETHANE = "biomethane"


class FeedstockSource(str, Enum):
    """Feedstock source types."""
    UCO = "uco"  # Used Cooking Oil
    TALLOW = "tallow"
    CANOLA = "canola"
    WHEAT_STRAW = "wheat_straw"
    SUGARCANE_BAGASSE = "sugarcane_bagasse"
    FORESTRY_RESIDUE = "forestry_residue"
    MUNICIPAL_WASTE = "municipal_waste"


class TargetMarket(str, Enum):
    """Target market for product."""
    DOMESTIC = "domestic"
    EXPORT = "export"
    EU = "eu"
    US = "us"
    ASIA = "asia"


class CarbonPathway(str, Enum):
    """Carbon credit/certificate pathways."""
    ACCU = "accu"  # Australian Carbon Credit Units
    CORSIA = "corsia"  # Carbon Offsetting for Aviation
    EU_RED = "eu_red"  # EU Renewable Energy Directive
    SCOPE3 = "scope3"  # Scope 3 certificates
    VCM = "vcm"  # Voluntary Carbon Market


# Request/Response Models
class ProjectParameters(BaseModel):
    """Input parameters for carbon revenue calculation."""
    project_type: ProjectType
    feedstock: FeedstockSource
    feedstock_ci_score: Optional[float] = Field(
        None,
        description="Carbon intensity score (gCO2e/MJ). If not provided, default for feedstock used."
    )
    annual_volume_litres: int = Field(..., gt=0)
    production_process: Optional[str] = None
    target_market: TargetMarket = TargetMarket.DOMESTIC
    include_transport_emissions: bool = True
    project_start_year: int = Field(default=2025, ge=2024, le=2035)


class PathwayEligibility(BaseModel):
    """Eligibility assessment for a carbon pathway."""
    pathway: CarbonPathway
    eligible: bool
    eligibility_confidence: float = Field(..., ge=0, le=1)
    requirements_met: List[str]
    requirements_missing: List[str]
    verification_requirements: List[str]
    estimated_verification_cost: float
    notes: Optional[str]


class PathwayRevenue(BaseModel):
    """Revenue calculation for a single pathway."""
    pathway: CarbonPathway
    eligible: bool
    annual_credits: float  # Tonnes CO2e or equivalent
    price_scenario_low: float
    price_scenario_base: float
    price_scenario_high: float
    revenue_low: float
    revenue_base: float
    revenue_high: float
    crediting_period_years: int
    total_revenue_low: float
    total_revenue_base: float
    total_revenue_high: float
    methodology: str
    notes: Optional[str]


class StackingOption(BaseModel):
    """Stackable pathway combination."""
    pathways: List[CarbonPathway]
    description: str
    combined_revenue_base: float
    legal_certainty: str  # high, medium, low
    regulatory_risk: str


class CarbonRevenueAssessment(BaseModel):
    """Complete carbon revenue assessment."""
    project_id: Optional[str]
    calculated_at: date
    project_parameters: ProjectParameters
    baseline_emissions_tco2: float
    project_emissions_tco2: float
    net_abatement_tco2: float
    pathway_assessments: List[PathwayRevenue]
    stackable_options: List[StackingOption]
    total_revenue_per_litre_low: float
    total_revenue_per_litre_base: float
    total_revenue_per_litre_high: float
    key_assumptions: List[str]
    risks: List[str]
    recommendations: List[str]


class CarbonPrices(BaseModel):
    """Current carbon price benchmarks."""
    accu_spot: float
    accu_forward_1y: float
    corsia_eligible: float
    eu_ets: float
    voluntary_premium: float
    as_of_date: date
    source: str


# Endpoints
@router.post("/calculate", response_model=CarbonRevenueAssessment)
async def calculate_carbon_revenue(project: ProjectParameters):
    """
    Calculate carbon revenue scenarios for a biofuel project.

    Analyzes eligibility across multiple pathways (ACCU, CORSIA, EU RED,
    Scope 3 certificates) and calculates revenue under low/base/high
    price scenarios.

    Returns:
    - Pathway eligibility assessments
    - Revenue projections per pathway
    - Stacking opportunities
    - Revenue per litre calculations
    """
    # TODO: Implement full calculation engine
    return CarbonRevenueAssessment(
        calculated_at=date.today(),
        project_parameters=project,
        baseline_emissions_tco2=25000,
        project_emissions_tco2=5000,
        net_abatement_tco2=20000,
        pathway_assessments=[
            PathwayRevenue(
                pathway=CarbonPathway.ACCU,
                eligible=True,
                annual_credits=18000,
                price_scenario_low=30,
                price_scenario_base=45,
                price_scenario_high=65,
                revenue_low=540000,
                revenue_base=810000,
                revenue_high=1170000,
                crediting_period_years=7,
                total_revenue_low=3780000,
                total_revenue_base=5670000,
                total_revenue_high=8190000,
                methodology="Emissions Reduction Fund - Transport",
                notes="Subject to ERF method eligibility confirmation",
            ),
        ],
        stackable_options=[],
        total_revenue_per_litre_low=0.054,
        total_revenue_per_litre_base=0.081,
        total_revenue_per_litre_high=0.117,
        key_assumptions=[
            "ACCU prices remain within historical range",
            "ERF method continues to apply",
            "Feedstock CI score as specified",
        ],
        risks=[
            "Policy uncertainty around ERF continuation",
            "Price volatility in carbon markets",
        ],
        recommendations=[
            "Pursue ACCU registration early",
            "Consider Scope 3 certificate sales to airlines",
        ],
    )


@router.get("/pathways/{pathway}/eligibility")
async def check_pathway_eligibility(
    pathway: CarbonPathway,
    project_type: ProjectType,
    feedstock: FeedstockSource,
    target_market: TargetMarket = TargetMarket.DOMESTIC,
):
    """
    Quick eligibility check for a specific pathway.

    Returns eligibility assessment without full revenue calculation.
    """
    # TODO: Implement
    pass


@router.get("/prices", response_model=CarbonPrices)
async def get_carbon_prices():
    """
    Get current carbon price benchmarks.

    Returns spot and forward prices for ACCU, CORSIA,
    EU ETS, and voluntary market premiums.
    """
    return CarbonPrices(
        accu_spot=38.50,
        accu_forward_1y=42.00,
        corsia_eligible=12.50,
        eu_ets=85.00,  # EUR, needs conversion
        voluntary_premium=15.00,
        as_of_date=date.today(),
        source="ABFI market intelligence",
    )


@router.get("/methodologies")
async def list_carbon_methodologies():
    """
    List available carbon credit methodologies.

    Returns methodologies applicable to biofuel projects
    with eligibility criteria summaries.
    """
    return [
        {
            "id": "erf-transport",
            "name": "ERF Transport Method",
            "pathway": "ACCU",
            "applicable_fuels": ["biodiesel", "renewable_diesel", "saf"],
            "baseline_approach": "fossil_fuel_displacement",
            "crediting_period": "7 years",
            "status": "active",
        },
        {
            "id": "corsia-saf",
            "name": "CORSIA Eligible SAF",
            "pathway": "CORSIA",
            "applicable_fuels": ["saf"],
            "baseline_approach": "icao_lcaf",
            "crediting_period": "ongoing",
            "status": "active",
            "requirements": [
                "RSB, ISCC, or equivalent certification",
                "LCA < 10% of jet fuel baseline",
            ],
        },
    ]


@router.get("/ci-scores")
async def get_default_ci_scores():
    """
    Get default carbon intensity scores by feedstock.

    Returns gCO2e/MJ values used when project-specific
    LCA is not provided.
    """
    return {
        "uco": 14.0,
        "tallow": 20.0,
        "canola": 32.0,
        "wheat_straw": 8.0,
        "sugarcane_bagasse": 12.0,
        "forestry_residue": 6.0,
        "municipal_waste": 18.0,
        "jet_fuel_baseline": 89.0,
        "diesel_baseline": 94.0,
        "source": "CORSIA default values / GREET model",
    }
