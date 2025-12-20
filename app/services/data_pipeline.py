"""
ABFI Intelligence Suite - Data Pipeline Service
Orchestrates scraping, analysis, and storage of articles.
"""

import asyncio
import logging
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional

import httpx

from app.scrapers.reneweconomy import RenewEconomyScraper, Article
from app.scrapers.cefc import CEFCScraper
from app.scrapers.arena import ARENAScraper
from app.services.llm_analyzer import LLMAnalyzer, SentimentResult, get_analyzer
from app.db import database as db
from app.core.config import settings

logger = logging.getLogger(__name__)


class DataPipeline:
    """
    Main data pipeline that:
    1. Scrapes articles from all sources
    2. Analyzes each article for sentiment using LLM
    3. Stores results in database
    4. Calculates aggregate sentiment index
    """

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=60.0)
        self.scrapers = {
            "reneweconomy": RenewEconomyScraper(self.client),
            # Additional scrapers can be added here
        }
        self.analyzer = get_analyzer()

    async def close(self):
        """Clean up resources."""
        await self.client.aclose()
        await self.analyzer.close()

    async def run_full_pipeline(self) -> Dict[str, Any]:
        """
        Run the complete data pipeline:
        1. Scrape all sources
        2. Analyze new articles
        3. Update sentiment index

        Returns:
            Summary of pipeline run
        """
        logger.info("Starting full data pipeline run...")
        start_time = datetime.now()

        results = {
            "articles_scraped": 0,
            "articles_analyzed": 0,
            "errors": [],
            "sources_processed": [],
        }

        # Step 1: Scrape articles from all sources
        all_articles = []

        try:
            # RenewEconomy
            renew_articles = await self._scrape_reneweconomy()
            all_articles.extend(renew_articles)
            results["sources_processed"].append({
                "source": "RenewEconomy",
                "articles": len(renew_articles),
            })
        except Exception as e:
            logger.error(f"Error scraping RenewEconomy: {e}")
            results["errors"].append(f"RenewEconomy: {str(e)}")

        results["articles_scraped"] = len(all_articles)
        logger.info(f"Scraped {len(all_articles)} articles from all sources")

        # Step 2: Analyze and store each article
        analyzed_count = 0
        for article in all_articles:
            try:
                # Insert raw article
                doc_id = db.insert_article(
                    title=article.title,
                    content=article.summary or article.title,
                    url=article.url,
                    source=article.source,
                    published_date=article.published_date,
                    author=article.author,
                )

                if not doc_id:
                    continue  # Article already exists

                # Analyze sentiment
                analysis = await self.analyzer.analyze_article(
                    title=article.title,
                    content=article.summary or article.title,
                    source=article.source,
                )

                if analysis:
                    # Store processed article
                    db.insert_processed_article(
                        raw_document_id=doc_id,
                        title=article.title,
                        content_text=article.summary or article.title,
                        url=article.url,
                        source=article.source,
                        sentiment=analysis.sentiment,
                        sentiment_score=analysis.sentiment_score,
                        intensity=analysis.intensity,
                        confidence=analysis.confidence,
                        fear_components=analysis.fear_components,
                        lenders_mentioned=analysis.lenders_mentioned,
                        published_date=article.published_date,
                        summary=analysis.summary,
                    )
                    analyzed_count += 1

                # Rate limiting
                await asyncio.sleep(0.5)

            except Exception as e:
                logger.error(f"Error processing article '{article.title}': {e}")
                results["errors"].append(f"Article: {str(e)}")

        results["articles_analyzed"] = analyzed_count
        logger.info(f"Analyzed {analyzed_count} new articles")

        # Step 3: Update sentiment index
        try:
            await self.update_sentiment_index()
        except Exception as e:
            logger.error(f"Error updating sentiment index: {e}")
            results["errors"].append(f"Index update: {str(e)}")

        # Calculate duration
        duration = (datetime.now() - start_time).total_seconds()
        results["duration_seconds"] = round(duration, 2)

        logger.info(f"Pipeline complete in {duration:.1f}s: {analyzed_count} new articles analyzed")
        return results

    async def _scrape_reneweconomy(self) -> List[Article]:
        """Scrape articles from RenewEconomy."""
        scraper = self.scrapers.get("reneweconomy")
        if not scraper:
            return []

        articles = []

        # Scrape multiple feeds
        for feed in ["main", "hydrogen", "biomass"]:
            try:
                feed_articles = await scraper.get_latest_articles(feed=feed, limit=20)
                articles.extend(feed_articles)
            except Exception as e:
                logger.warning(f"Error scraping {feed} feed: {e}")

        # Deduplicate by URL
        seen_urls = set()
        unique_articles = []
        for article in articles:
            if article.url not in seen_urls:
                unique_articles.append(article)
                seen_urls.add(article.url)

        return unique_articles

    async def update_sentiment_index(self) -> Dict[str, Any]:
        """
        Calculate and save today's sentiment index from processed articles.
        """
        today = date.today()

        # Get article counts
        counts = db.get_article_counts_by_sentiment(days=1)
        total_docs = sum(counts.values())

        if total_docs == 0:
            # No articles today, use recent data
            counts = db.get_article_counts_by_sentiment(days=7)
            total_docs = sum(counts.values())

        # Get recent articles for fear component analysis
        recent_articles = db.get_recent_articles(limit=100)

        # Calculate fear component breakdown
        fear_counts = {
            "regulatory_risk": 0,
            "technology_risk": 0,
            "feedstock_risk": 0,
            "counterparty_risk": 0,
            "market_risk": 0,
            "esg_concerns": 0,
        }

        for article in recent_articles:
            components = article.get("fear_components", "[]")
            if isinstance(components, str):
                import json
                components = json.loads(components)

            for comp in components:
                comp_key = comp.lower()
                if comp_key in fear_counts:
                    fear_counts[comp_key] += 1

        # Normalize to percentages
        total_fear = sum(fear_counts.values()) or 1
        fear_breakdown = {
            k: round((v / total_fear) * 100, 1)
            for k, v in fear_counts.items()
        }

        # Calculate overall sentiment index (-100 to +100)
        bullish = counts.get("BULLISH", 0)
        bearish = counts.get("BEARISH", 0)
        neutral = counts.get("NEUTRAL", 0)

        if total_docs > 0:
            # Net sentiment formula
            overall_index = ((bullish - bearish) / total_docs) * 100
        else:
            overall_index = 0

        # Get lender scores
        lender_scores = {}
        lenders = db.get_lender_sentiment_scores(limit=10)
        for lender in lenders:
            lender_scores[lender["lender"]] = lender["sentiment"]

        # Save to database
        db.save_daily_sentiment_index(
            index_date=today,
            overall_index=round(overall_index, 1),
            bullish_count=bullish,
            bearish_count=bearish,
            neutral_count=neutral,
            documents_analyzed=total_docs,
            fear_breakdown=fear_breakdown,
            lender_scores=lender_scores,
        )

        logger.info(f"Updated sentiment index: {overall_index:.1f} ({bullish}B/{bearish}R/{neutral}N)")

        return {
            "date": today.isoformat(),
            "overall_index": round(overall_index, 1),
            "bullish_count": bullish,
            "bearish_count": bearish,
            "neutral_count": neutral,
            "documents_analyzed": total_docs,
            "fear_breakdown": fear_breakdown,
        }


# Global pipeline instance
_pipeline: Optional[DataPipeline] = None


def get_pipeline() -> DataPipeline:
    """Get the global pipeline instance."""
    global _pipeline
    if _pipeline is None:
        _pipeline = DataPipeline()
    return _pipeline


async def run_pipeline() -> Dict[str, Any]:
    """Run the data pipeline."""
    pipeline = get_pipeline()
    return await pipeline.run_full_pipeline()


async def refresh_sentiment_index() -> Dict[str, Any]:
    """Refresh the sentiment index from existing data."""
    pipeline = get_pipeline()
    return await pipeline.update_sentiment_index()
