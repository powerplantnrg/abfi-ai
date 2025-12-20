"""
Intelligence Orchestrator Service
Unified interface for all ABFI data sources and intelligence gathering.

This service combines:
- Government policy signals
- Financial sector intelligence
- Energy market data
- Industry news and announcements
- Carbon market data

Provides:
- Real-time data aggregation
- Historical trend analysis
- Predictive signals for bankability assessments
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import httpx

from app.scrapers import (
    AEMOScraper,
    CERScraper,
    ARENAScraper,
    CEFCScraper,
    RenewEconomyScraper,
    GovernmentDataAggregator,
    FinancialIntelligenceAggregator,
)


class IntelligenceSummary(BaseModel):
    """Summary of current market intelligence."""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    lending_sentiment_index: float = 0.5  # 0-1 scale
    policy_risk_score: float = 0.5  # 0-1 scale (higher = more risk)
    market_conditions_score: float = 0.5  # 0-1 scale
    carbon_revenue_outlook: str = "stable"  # positive, stable, negative
    key_signals: List[str] = []
    recommendations: List[str] = []


class SectorIntelligence(BaseModel):
    """Sector-specific intelligence report."""
    sector: str
    subsector: Optional[str] = None
    sentiment: str  # bullish, neutral, bearish
    key_developments: List[str] = []
    risks: List[str] = []
    opportunities: List[str] = []
    data_freshness: Dict[str, datetime] = {}


class ProjectRiskSignals(BaseModel):
    """Risk signals for a specific project type."""
    project_type: str  # biomass, biogas, SAF, etc.
    technology_maturity: str  # mature, emerging, experimental
    policy_support_level: str  # strong, moderate, weak
    financing_availability: str  # high, medium, low
    offtake_demand: str  # growing, stable, declining
    key_risks: List[str] = []
    mitigation_factors: List[str] = []


class IntelligenceOrchestrator:
    """
    Central orchestrator for all intelligence gathering.
    
    Coordinates data collection from:
    - AEMO (energy market data)
    - CER (renewable energy certificates)
    - ARENA/CEFC (funding programs)
    - Government sources (policy signals)
    - Financial sector (lending sentiment)
    - News sources (market sentiment)
    """
    
    def __init__(self, client: Optional[httpx.AsyncClient] = None):
        self.client = client or httpx.AsyncClient(timeout=120.0)
        
        # Initialize all data source scrapers
        self.aemo = AEMOScraper(self.client)
        self.cer = CERScraper(self.client)
        self.arena = ARENAScraper(self.client)
        self.cefc = CEFCScraper(self.client)
        self.news = RenewEconomyScraper(self.client)
        self.government = GovernmentDataAggregator(self.client)
        self.financial = FinancialIntelligenceAggregator(self.client)
        
        # Cache for expensive operations
        self._cache: Dict[str, Any] = {}
        self._cache_ttl: Dict[str, datetime] = {}
    
    async def close(self):
        """Clean up resources."""
        await self.client.aclose()
    
    def _is_cache_valid(self, key: str, ttl_minutes: int = 60) -> bool:
        """Check if cached data is still valid."""
        if key not in self._cache:
            return False
        if key not in self._cache_ttl:
            return False
        return datetime.utcnow() - self._cache_ttl[key] < timedelta(minutes=ttl_minutes)
    
    def _set_cache(self, key: str, value: Any):
        """Set cache value with timestamp."""
        self._cache[key] = value
        self._cache_ttl[key] = datetime.utcnow()
    
    async def get_market_summary(
        self,
        use_cache: bool = True
    ) -> IntelligenceSummary:
        """
        Get comprehensive market intelligence summary.
        
        Combines signals from all sources into actionable insights.
        """
        cache_key = "market_summary"
        
        if use_cache and self._is_cache_valid(cache_key, ttl_minutes=30):
            return self._cache[cache_key]
        
        # Gather data from all sources concurrently
        tasks = [
            self.financial.get_lending_sentiment_index(),
            self._assess_policy_risk(),
            self._assess_market_conditions(),
            self._get_carbon_outlook(),
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        lending_data = results[0] if not isinstance(results[0], Exception) else {}
        policy_risk = results[1] if not isinstance(results[1], Exception) else 0.5
        market_score = results[2] if not isinstance(results[2], Exception) else 0.5
        carbon_outlook = results[3] if not isinstance(results[3], Exception) else "stable"
        
        # Generate key signals and recommendations
        key_signals = await self._extract_key_signals()
        recommendations = self._generate_recommendations(
            lending_data.get("overall_index", 0.5),
            policy_risk,
            market_score,
            carbon_outlook
        )
        
        summary = IntelligenceSummary(
            lending_sentiment_index=lending_data.get("overall_index", 0.5),
            policy_risk_score=policy_risk,
            market_conditions_score=market_score,
            carbon_revenue_outlook=carbon_outlook,
            key_signals=key_signals,
            recommendations=recommendations,
        )
        
        self._set_cache(cache_key, summary)
        return summary
    
    async def get_sector_intelligence(
        self,
        sector: str = "bioenergy"
    ) -> SectorIntelligence:
        """Get detailed intelligence for a specific sector."""
        # Would aggregate sector-specific data
        return SectorIntelligence(
            sector=sector,
            sentiment="neutral",
            key_developments=[
                "Renewable gas production targets announced",
                "SAF mandate consultation opened",
                "CEFC green hydrogen funding expanded",
            ],
            risks=[
                "Feedstock price volatility",
                "Policy uncertainty on carbon credits",
                "Competition from electrification",
            ],
            opportunities=[
                "Growing corporate offtake demand",
                "Export potential for SAF",
                "Green gas certification premiums",
            ],
            data_freshness={
                "market_data": datetime.utcnow() - timedelta(hours=1),
                "policy_data": datetime.utcnow() - timedelta(hours=24),
                "financial_data": datetime.utcnow() - timedelta(hours=12),
            }
        )
    
    async def get_project_risk_signals(
        self,
        project_type: str
    ) -> ProjectRiskSignals:
        """Get risk signals for a specific project type."""
        # Project type profiles
        profiles = {
            "biomass_power": {
                "technology_maturity": "mature",
                "policy_support_level": "moderate",
                "financing_availability": "medium",
                "offtake_demand": "stable",
                "key_risks": [
                    "Feedstock supply security",
                    "Competition from solar/wind",
                    "Carbon accounting changes",
                ],
                "mitigation_factors": [
                    "Long-term feedstock contracts",
                    "Co-firing with coal phase-out",
                    "Waste-derived fuel exemptions",
                ],
            },
            "biogas": {
                "technology_maturity": "mature",
                "policy_support_level": "strong",
                "financing_availability": "high",
                "offtake_demand": "growing",
                "key_risks": [
                    "Feedstock competition",
                    "Gas price volatility",
                    "Interconnection delays",
                ],
                "mitigation_factors": [
                    "Green gas certification premium",
                    "Waste disposal revenue",
                    "Corporate PPA demand",
                ],
            },
            "saf": {
                "technology_maturity": "emerging",
                "policy_support_level": "strong",
                "financing_availability": "medium",
                "offtake_demand": "growing",
                "key_risks": [
                    "Technology scale-up risk",
                    "Feedstock certification",
                    "Offtake price uncertainty",
                ],
                "mitigation_factors": [
                    "Airline net-zero commitments",
                    "Government SAF mandates",
                    "CEFC funding support",
                ],
            },
            "renewable_diesel": {
                "technology_maturity": "mature",
                "policy_support_level": "moderate",
                "financing_availability": "high",
                "offtake_demand": "growing",
                "key_risks": [
                    "Feedstock price exposure",
                    "Fossil fuel price competition",
                    "EV transition impacts",
                ],
                "mitigation_factors": [
                    "Heavy transport demand",
                    "Drop-in fuel advantage",
                    "Carbon intensity credits",
                ],
            },
        }
        
        profile = profiles.get(project_type, {
            "technology_maturity": "unknown",
            "policy_support_level": "unknown",
            "financing_availability": "unknown",
            "offtake_demand": "unknown",
            "key_risks": [],
            "mitigation_factors": [],
        })
        
        return ProjectRiskSignals(
            project_type=project_type,
            **profile
        )
    
    async def get_bankability_signals(
        self,
        project_id: Optional[int] = None,
        feedstock_types: Optional[List[str]] = None,
        location_state: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get signals relevant to bankability assessment.
        
        Used by the main platform's bankability scoring system.
        """
        signals = {
            "market_intelligence": {},
            "policy_signals": {},
            "financial_signals": {},
            "risk_indicators": {},
            "opportunity_indicators": {},
        }
        
        # Get lending sentiment
        lending = await self.financial.get_lending_sentiment_index()
        signals["financial_signals"] = {
            "lending_sentiment": lending.get("overall_index", 0.5),
            "bank_stances": lending.get("bank_stances", {}),
            "trend": lending.get("trend", "stable"),
        }
        
        # Get policy signals
        signals["policy_signals"] = {
            "federal_support": "strong",  # Would assess from government data
            "state_support": "moderate" if location_state else "unknown",
            "upcoming_changes": [],
        }
        
        # Get risk indicators
        signals["risk_indicators"] = {
            "policy_risk": await self._assess_policy_risk(),
            "market_risk": 0.3,  # Would calculate
            "technology_risk": 0.2,  # Would calculate based on project type
        }
        
        # Get opportunity indicators
        signals["opportunity_indicators"] = {
            "carbon_premium": True,
            "green_certificate_value": True,
            "corporate_offtake_demand": True,
        }
        
        return signals
    
    async def _assess_policy_risk(self) -> float:
        """Assess current policy risk level (0-1)."""
        # Would analyze recent policy announcements and stability
        return 0.3
    
    async def _assess_market_conditions(self) -> float:
        """Assess current market conditions score (0-1)."""
        # Would analyze energy prices, demand, supply dynamics
        return 0.6
    
    async def _get_carbon_outlook(self) -> str:
        """Get carbon market outlook."""
        # Would analyze ACCU prices, scheme changes, demand trends
        return "positive"
    
    async def _extract_key_signals(self) -> List[str]:
        """Extract key market signals from recent data."""
        # Would process recent news and announcements
        return [
            "Renewable gas targets announced in Federal Budget",
            "Major banks expand green lending programs",
            "ACCU prices stable above $30",
            "SAF mandate consultation closes next month",
        ]
    
    def _generate_recommendations(
        self,
        lending_score: float,
        policy_risk: float,
        market_score: float,
        carbon_outlook: str
    ) -> List[str]:
        """Generate actionable recommendations based on signals."""
        recommendations = []
        
        if lending_score > 0.7:
            recommendations.append(
                "Favorable lending environment - consider accelerating financing discussions"
            )
        elif lending_score < 0.3:
            recommendations.append(
                "Challenging lending environment - strengthen bankability documentation"
            )
        
        if policy_risk > 0.6:
            recommendations.append(
                "Elevated policy risk - monitor upcoming legislation and diversify revenue"
            )
        
        if carbon_outlook == "positive":
            recommendations.append(
                "Strong carbon outlook - highlight carbon revenue in financial models"
            )
        
        if market_score > 0.6:
            recommendations.append(
                "Favorable market conditions - optimal time for offtake negotiations"
            )
        
        return recommendations


# Convenience function for quick intelligence access
async def get_quick_summary() -> IntelligenceSummary:
    """Get quick market intelligence summary."""
    async with httpx.AsyncClient() as client:
        orchestrator = IntelligenceOrchestrator(client)
        return await orchestrator.get_market_summary(use_cache=False)
