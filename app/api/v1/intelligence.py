"""
Intelligence API Endpoints
Unified access to market intelligence for the ABFI platform.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

from app.services.intelligence import IntelligenceOrchestrator, IntelligenceSummary
from app.services.scheduler import get_scheduler


router = APIRouter()


class MarketSummaryResponse(BaseModel):
    """Response model for market summary."""
    timestamp: datetime
    lending_sentiment_index: float
    policy_risk_score: float
    market_conditions_score: float
    carbon_revenue_outlook: str
    key_signals: List[str]
    recommendations: List[str]


class SectorIntelligenceResponse(BaseModel):
    """Response model for sector intelligence."""
    sector: str
    subsector: Optional[str] = None
    sentiment: str
    key_developments: List[str]
    risks: List[str]
    opportunities: List[str]


class ProjectRiskResponse(BaseModel):
    """Response model for project risk signals."""
    project_type: str
    technology_maturity: str
    policy_support_level: str
    financing_availability: str
    offtake_demand: str
    key_risks: List[str]
    mitigation_factors: List[str]


class SchedulerStatusResponse(BaseModel):
    """Response model for scheduler status."""
    running: bool
    task_count: int
    enabled_tasks: int
    tasks: dict


# Global orchestrator instance
_orchestrator: Optional[IntelligenceOrchestrator] = None


def get_orchestrator() -> IntelligenceOrchestrator:
    """Get or create the intelligence orchestrator."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = IntelligenceOrchestrator()
    return _orchestrator


@router.get(
    "/summary",
    response_model=MarketSummaryResponse,
    summary="Get Market Intelligence Summary",
    description="Get comprehensive market intelligence summary including lending sentiment, policy risk, and key signals."
)
async def get_market_summary(
    use_cache: bool = Query(True, description="Use cached data if available")
):
    """Get current market intelligence summary."""
    try:
        orchestrator = get_orchestrator()
        summary = await orchestrator.get_market_summary(use_cache=use_cache)
        return MarketSummaryResponse(
            timestamp=summary.timestamp,
            lending_sentiment_index=summary.lending_sentiment_index,
            policy_risk_score=summary.policy_risk_score,
            market_conditions_score=summary.market_conditions_score,
            carbon_revenue_outlook=summary.carbon_revenue_outlook,
            key_signals=summary.key_signals,
            recommendations=summary.recommendations,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/sector/{sector}",
    response_model=SectorIntelligenceResponse,
    summary="Get Sector Intelligence",
    description="Get detailed intelligence for a specific sector."
)
async def get_sector_intelligence(
    sector: str = "bioenergy"
):
    """Get sector-specific intelligence."""
    try:
        orchestrator = get_orchestrator()
        intel = await orchestrator.get_sector_intelligence(sector)
        return SectorIntelligenceResponse(
            sector=intel.sector,
            subsector=intel.subsector,
            sentiment=intel.sentiment,
            key_developments=intel.key_developments,
            risks=intel.risks,
            opportunities=intel.opportunities,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/project-risk/{project_type}",
    response_model=ProjectRiskResponse,
    summary="Get Project Risk Signals",
    description="Get risk signals for a specific project type."
)
async def get_project_risk(
    project_type: str
):
    """Get project type risk assessment."""
    valid_types = ["biomass_power", "biogas", "saf", "renewable_diesel"]
    
    if project_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid project type. Valid types: {', '.join(valid_types)}"
        )
    
    try:
        orchestrator = get_orchestrator()
        signals = await orchestrator.get_project_risk_signals(project_type)
        return ProjectRiskResponse(
            project_type=signals.project_type,
            technology_maturity=signals.technology_maturity,
            policy_support_level=signals.policy_support_level,
            financing_availability=signals.financing_availability,
            offtake_demand=signals.offtake_demand,
            key_risks=signals.key_risks,
            mitigation_factors=signals.mitigation_factors,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/bankability-signals",
    summary="Get Bankability Signals",
    description="Get signals relevant to bankability assessment for the main platform."
)
async def get_bankability_signals(
    project_id: Optional[int] = None,
    feedstock_types: Optional[str] = None,
    location_state: Optional[str] = None
):
    """Get signals for bankability assessment."""
    try:
        orchestrator = get_orchestrator()
        
        feedstocks = feedstock_types.split(",") if feedstock_types else None
        
        signals = await orchestrator.get_bankability_signals(
            project_id=project_id,
            feedstock_types=feedstocks,
            location_state=location_state,
        )
        return signals
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/lending-sentiment",
    summary="Get Lending Sentiment Index",
    description="Get detailed lending sentiment analysis from major banks."
)
async def get_lending_sentiment():
    """Get bank lending sentiment analysis."""
    try:
        orchestrator = get_orchestrator()
        lending = await orchestrator.financial.get_lending_sentiment_index()
        return lending
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/bank-comparison",
    summary="Compare Bank Lending Appetite",
    description="Compare bioenergy lending appetite across major Australian banks."
)
async def get_bank_comparison():
    """Get bank lending comparison."""
    try:
        orchestrator = get_orchestrator()
        comparison = await orchestrator.financial.get_bank_comparison()
        return {"banks": comparison}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Scheduler endpoints
@router.get(
    "/scheduler/status",
    response_model=SchedulerStatusResponse,
    summary="Get Scheduler Status",
    description="Get the status of the data collection scheduler."
)
async def get_scheduler_status():
    """Get scheduler status."""
    scheduler = get_scheduler()
    status = scheduler.get_status()
    return SchedulerStatusResponse(
        running=status["running"],
        task_count=status["task_count"],
        enabled_tasks=status["enabled_tasks"],
        tasks=status["tasks"],
    )


@router.get(
    "/scheduler/health",
    summary="Get Scheduler Health",
    description="Get health metrics for the data collection scheduler."
)
async def get_scheduler_health():
    """Get scheduler health."""
    scheduler = get_scheduler()
    return scheduler.get_health()


@router.post(
    "/scheduler/task/{task_id}/run",
    summary="Run Task Now",
    description="Manually trigger a data collection task."
)
async def run_task_now(task_id: str):
    """Run a task immediately."""
    scheduler = get_scheduler()
    result = await scheduler.run_task_now(task_id)
    
    if result is None:
        raise HTTPException(status_code=404, detail=f"Task not found: {task_id}")
    
    return {
        "task_id": result.task_id,
        "status": result.status.value,
        "duration_seconds": result.duration_seconds,
        "records_processed": result.records_processed,
        "error_message": result.error_message,
    }


@router.post(
    "/scheduler/task/{task_id}/enable",
    summary="Enable Task",
    description="Enable a disabled data collection task."
)
async def enable_task(task_id: str):
    """Enable a task."""
    scheduler = get_scheduler()
    scheduler.enable_task(task_id)
    return {"status": "enabled", "task_id": task_id}


@router.post(
    "/scheduler/task/{task_id}/disable",
    summary="Disable Task",
    description="Disable a data collection task."
)
async def disable_task(task_id: str):
    """Disable a task."""
    scheduler = get_scheduler()
    scheduler.disable_task(task_id)
    return {"status": "disabled", "task_id": task_id}
