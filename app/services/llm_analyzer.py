"""
ABFI Intelligence Suite - LLM-Based Sentiment Analyzer
Uses OpenRouter API for sentiment analysis of bioenergy articles.
"""

import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

import httpx
from pydantic import BaseModel, Field

from app.core.config import settings

logger = logging.getLogger(__name__)


class SentimentResult(BaseModel):
    """Result of LLM sentiment analysis."""
    sentiment: str = Field(..., description="BULLISH, BEARISH, or NEUTRAL")
    sentiment_score: float = Field(..., ge=-1, le=1, description="Score from -1 to 1")
    intensity: int = Field(..., ge=1, le=5, description="Intensity 1-5")
    confidence: float = Field(..., ge=0, le=1, description="Confidence 0-1")
    fear_components: List[str] = Field(default_factory=list)
    lenders_mentioned: List[str] = Field(default_factory=list)
    summary: str = Field(..., description="Brief summary")
    reasoning: str = Field(..., description="Explanation of sentiment")


# System prompt for sentiment analysis
SENTIMENT_SYSTEM_PROMPT = """You are an expert financial analyst specializing in the Australian bioenergy and renewable energy sector.
Your task is to analyze news articles and documents for their sentiment regarding lending and investment in bioenergy projects.

When analyzing, consider:
1. **Lending Sentiment**: How does this affect banks' willingness to lend to bioenergy projects?
2. **Fear Components**: Identify specific risk factors mentioned:
   - REGULATORY_RISK: Policy uncertainty, regulatory changes
   - TECHNOLOGY_RISK: Technology maturity, operational issues
   - FEEDSTOCK_RISK: Feedstock supply, price volatility
   - COUNTERPARTY_RISK: Offtaker reliability, credit risk
   - MARKET_RISK: Price volatility, demand uncertainty
   - ESG_CONCERNS: Environmental or social concerns

3. **Lenders Mentioned**: Identify any financial institutions mentioned:
   - Major banks: NAB, CBA, ANZ, Westpac, Macquarie
   - Green banks: CEFC (Clean Energy Finance Corporation), ARENA
   - International: ADB, World Bank, EIB
   - Other institutions

Respond with ONLY a valid JSON object (no markdown, no explanation) in this format:
{
    "sentiment": "BULLISH" | "BEARISH" | "NEUTRAL",
    "sentiment_score": <float -1 to 1>,
    "intensity": <int 1-5>,
    "confidence": <float 0-1>,
    "fear_components": ["REGULATORY_RISK", ...],
    "lenders_mentioned": ["CEFC", "NAB", ...],
    "summary": "<one-sentence summary>",
    "reasoning": "<brief explanation of your assessment>"
}"""


class LLMAnalyzer:
    """LLM-based sentiment analyzer using OpenRouter."""

    def __init__(self):
        self.api_key = settings.openrouter_api_key
        self.model = settings.openrouter_model
        self.base_url = settings.openrouter_base_url
        self.client = httpx.AsyncClient(timeout=60.0)

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def analyze_article(
        self,
        title: str,
        content: str,
        source: Optional[str] = None,
    ) -> Optional[SentimentResult]:
        """
        Analyze a single article for sentiment.

        Args:
            title: Article title
            content: Article content/text
            source: Source name (optional)

        Returns:
            SentimentResult or None if analysis fails
        """
        if not self.api_key:
            logger.warning("OpenRouter API key not configured, using fallback")
            return self._fallback_analysis(title, content)

        # Truncate content if too long (token limit)
        max_content_length = 4000
        if len(content) > max_content_length:
            content = content[:max_content_length] + "..."

        user_message = f"""Analyze the following article for lending sentiment in the Australian bioenergy sector:

Title: {title}
Source: {source or 'Unknown'}

Content:
{content}

Respond with ONLY a valid JSON object."""

        try:
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "HTTP-Referer": "https://abfi.io",
                    "X-Title": "ABFI Intelligence Suite",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": SENTIMENT_SYSTEM_PROMPT},
                        {"role": "user", "content": user_message},
                    ],
                    "temperature": 0.3,
                    "max_tokens": 500,
                },
            )

            if response.status_code != 200:
                logger.error(f"OpenRouter API error: {response.status_code} - {response.text}")
                return self._fallback_analysis(title, content)

            data = response.json()
            content_text = data["choices"][0]["message"]["content"]

            # Parse JSON response
            try:
                # Clean potential markdown formatting
                if content_text.startswith("```"):
                    content_text = content_text.split("```")[1]
                    if content_text.startswith("json"):
                        content_text = content_text[4:]

                result_data = json.loads(content_text.strip())
                return SentimentResult(**result_data)

            except (json.JSONDecodeError, KeyError, ValueError) as e:
                logger.warning(f"Failed to parse LLM response: {e}")
                return self._fallback_analysis(title, content)

        except httpx.RequestError as e:
            logger.error(f"Request error: {e}")
            return self._fallback_analysis(title, content)

    def _fallback_analysis(
        self,
        title: str,
        content: str,
    ) -> SentimentResult:
        """
        Fallback keyword-based sentiment analysis.
        Used when LLM is unavailable.
        """
        text = f"{title} {content}".lower()

        # Bullish keywords
        bullish_keywords = [
            "investment", "funding", "growth", "expansion", "milestone",
            "partnership", "approval", "granted", "successful", "awarded",
            "billion", "million", "green hydrogen", "renewable", "sustainable",
            "net zero", "clean energy", "breakthrough", "innovation",
        ]

        # Bearish keywords
        bearish_keywords = [
            "delay", "cancelled", "rejected", "uncertainty", "risk",
            "concern", "challenge", "decline", "loss", "failure",
            "struggling", "closure", "bankrupt", "withdraw", "suspended",
        ]

        # Lender keywords
        lender_keywords = {
            "cefc": "CEFC",
            "clean energy finance corporation": "CEFC",
            "arena": "ARENA",
            "nab": "NAB",
            "cba": "CBA",
            "commonwealth bank": "CBA",
            "anz": "ANZ",
            "westpac": "Westpac",
            "macquarie": "Macquarie",
        }

        # Count sentiment keywords
        bullish_count = sum(1 for kw in bullish_keywords if kw in text)
        bearish_count = sum(1 for kw in bearish_keywords if kw in text)

        # Determine sentiment
        if bullish_count > bearish_count + 2:
            sentiment = "BULLISH"
            sentiment_score = min(0.8, 0.3 + (bullish_count - bearish_count) * 0.1)
        elif bearish_count > bullish_count + 2:
            sentiment = "BEARISH"
            sentiment_score = max(-0.8, -0.3 - (bearish_count - bullish_count) * 0.1)
        else:
            sentiment = "NEUTRAL"
            sentiment_score = 0.0

        # Find lenders mentioned
        lenders_mentioned = []
        for keyword, lender in lender_keywords.items():
            if keyword in text and lender not in lenders_mentioned:
                lenders_mentioned.append(lender)

        # Identify fear components
        fear_components = []
        if any(word in text for word in ["regulation", "policy", "government", "legislation"]):
            fear_components.append("REGULATORY_RISK")
        if any(word in text for word in ["technology", "technical", "operational"]):
            fear_components.append("TECHNOLOGY_RISK")
        if any(word in text for word in ["feedstock", "supply", "biomass"]):
            fear_components.append("FEEDSTOCK_RISK")
        if any(word in text for word in ["offtake", "counterparty", "contract"]):
            fear_components.append("COUNTERPARTY_RISK")

        return SentimentResult(
            sentiment=sentiment,
            sentiment_score=round(sentiment_score, 2),
            intensity=3,
            confidence=0.5,  # Lower confidence for fallback
            fear_components=fear_components,
            lenders_mentioned=lenders_mentioned,
            summary=title[:200],
            reasoning="Keyword-based analysis (LLM unavailable)",
        )

    async def analyze_batch(
        self,
        articles: List[Dict[str, str]],
    ) -> List[SentimentResult]:
        """
        Analyze multiple articles.

        Args:
            articles: List of dicts with 'title', 'content', and optional 'source'

        Returns:
            List of SentimentResult objects
        """
        results = []
        for article in articles:
            result = await self.analyze_article(
                title=article.get("title", ""),
                content=article.get("content", ""),
                source=article.get("source"),
            )
            if result:
                results.append(result)

        return results


# Singleton analyzer instance
_analyzer: Optional[LLMAnalyzer] = None


def get_analyzer() -> LLMAnalyzer:
    """Get the global analyzer instance."""
    global _analyzer
    if _analyzer is None:
        _analyzer = LLMAnalyzer()
    return _analyzer


async def analyze_article(
    title: str,
    content: str,
    source: Optional[str] = None,
) -> Optional[SentimentResult]:
    """Convenience function for single article analysis."""
    analyzer = get_analyzer()
    return await analyzer.analyze_article(title, content, source)
