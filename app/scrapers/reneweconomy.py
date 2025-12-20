"""
RenewEconomy RSS Scraper - Priority 3
Highest-value free news source for Australian renewable energy.

RSS Feeds:
- Main: https://reneweconomy.com.au/feed
- Hydrogen: /category/hydrogen/feed
- Biomass: /category/biomass/feed
- Markets: /category/markets/feed

Sister sites:
- The Driven: thedriven.io/feed
- One Step Off The Grid: onestepoffthegrid.com.au/feed
"""

import asyncio
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Optional
from html import unescape
import re

import httpx
from pydantic import BaseModel


class Article(BaseModel):
    """News article from RSS feed."""
    title: str
    url: str
    published_date: datetime
    author: Optional[str] = None
    summary: str
    content: Optional[str] = None
    categories: list[str] = []
    source: str = "RenewEconomy"


class RenewEconomyScraper:
    """
    RenewEconomy RSS feed scraper.

    WordPress-based site with clean HTML structure.
    """

    BASE_URL = "https://reneweconomy.com.au"

    FEEDS = {
        "main": f"{BASE_URL}/feed",
        "hydrogen": f"{BASE_URL}/category/hydrogen/feed",
        "biomass": f"{BASE_URL}/category/biomass/feed",
        "markets": f"{BASE_URL}/category/markets/feed",
        "storage": f"{BASE_URL}/category/storage/feed",
        "solar": f"{BASE_URL}/category/solar/feed",
        "wind": f"{BASE_URL}/category/wind/feed",
    }

    SISTER_FEEDS = {
        "the_driven": "https://thedriven.io/feed",
        "one_step": "https://onestepoffthegrid.com.au/feed",
    }

    def __init__(self, client: Optional[httpx.AsyncClient] = None):
        self.client = client or httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": "ABFI-Bot/1.0 (+https://abfi.io)",
            }
        )
        self._rate_limit_delay = 5.0  # 5 seconds between requests

    async def close(self):
        await self.client.aclose()

    async def _fetch_feed(self, url: str) -> str:
        """Fetch RSS feed XML."""
        await asyncio.sleep(self._rate_limit_delay)
        response = await self.client.get(url)
        response.raise_for_status()
        return response.text

    def _parse_rss(self, xml_content: str, source: str = "RenewEconomy") -> list[Article]:
        """Parse RSS 2.0 feed."""
        articles = []

        try:
            root = ET.fromstring(xml_content)
            channel = root.find("channel")

            if channel is None:
                return articles

            for item in channel.findall("item"):
                title_elem = item.find("title")
                link_elem = item.find("link")
                pub_date_elem = item.find("pubDate")
                description_elem = item.find("description")
                creator_elem = item.find("{http://purl.org/dc/elements/1.1/}creator")

                if not all([title_elem, link_elem]):
                    continue

                # Parse categories
                categories = []
                for cat in item.findall("category"):
                    if cat.text:
                        categories.append(cat.text)

                # Parse date
                pub_date = datetime.now()
                if pub_date_elem is not None and pub_date_elem.text:
                    try:
                        # RSS date format: "Mon, 01 Jan 2024 12:00:00 +0000"
                        pub_date = datetime.strptime(
                            pub_date_elem.text.strip(),
                            "%a, %d %b %Y %H:%M:%S %z"
                        )
                    except ValueError:
                        pass

                # Clean summary
                summary = ""
                if description_elem is not None and description_elem.text:
                    summary = self._clean_html(description_elem.text)

                articles.append(Article(
                    title=title_elem.text or "",
                    url=link_elem.text or "",
                    published_date=pub_date,
                    author=creator_elem.text if creator_elem is not None else None,
                    summary=summary,
                    categories=categories,
                    source=source,
                ))

        except ET.ParseError:
            pass

        return articles

    def _clean_html(self, html: str) -> str:
        """Remove HTML tags and decode entities."""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', html)
        # Decode HTML entities
        text = unescape(text)
        # Normalize whitespace
        text = ' '.join(text.split())
        return text.strip()

    async def get_latest_articles(
        self,
        feed: str = "main",
        limit: int = 20
    ) -> list[Article]:
        """
        Fetch latest articles from specified feed.

        Args:
            feed: Feed name (main, hydrogen, biomass, markets, etc.)
            limit: Maximum number of articles to return
        """
        url = self.FEEDS.get(feed, self.FEEDS["main"])
        xml_content = await self._fetch_feed(url)
        articles = self._parse_rss(xml_content)
        return articles[:limit]

    async def get_biomass_articles(self, limit: int = 20) -> list[Article]:
        """Fetch latest biomass/bioenergy articles."""
        return await self.get_latest_articles("biomass", limit)

    async def get_all_feeds(self) -> list[Article]:
        """
        Fetch articles from all RenewEconomy feeds.

        Returns deduplicated list sorted by date.
        """
        all_articles = []
        seen_urls = set()

        for feed_name in self.FEEDS:
            try:
                articles = await self.get_latest_articles(feed_name)
                for article in articles:
                    if article.url not in seen_urls:
                        all_articles.append(article)
                        seen_urls.add(article.url)
            except Exception:
                continue

        # Sort by date, newest first
        all_articles.sort(key=lambda a: a.published_date, reverse=True)
        return all_articles

    async def get_sister_site_articles(
        self,
        site: str = "the_driven",
        limit: int = 10
    ) -> list[Article]:
        """Fetch articles from sister sites."""
        url = self.SISTER_FEEDS.get(site)
        if not url:
            return []

        source = "The Driven" if site == "the_driven" else "One Step Off The Grid"
        xml_content = await self._fetch_feed(url)
        articles = self._parse_rss(xml_content, source=source)
        return articles[:limit]

    async def search_articles(
        self,
        keywords: list[str],
        limit: int = 50
    ) -> list[Article]:
        """
        Search recent articles for keywords.

        Searches title and summary for any of the keywords.
        """
        all_articles = await self.get_all_feeds()
        matching = []

        for article in all_articles:
            text = f"{article.title} {article.summary}".lower()
            if any(kw.lower() in text for kw in keywords):
                matching.append(article)

            if len(matching) >= limit:
                break

        return matching


async def fetch_bioenergy_news() -> list[Article]:
    """Convenience function for bioenergy news."""
    scraper = RenewEconomyScraper()
    try:
        # Search for bioenergy-related terms
        articles = await scraper.search_articles([
            "bioenergy", "biomass", "biogas", "biofuel",
            "biodiesel", "SAF", "sustainable aviation fuel",
            "waste-to-energy", "bagasse", "landfill gas"
        ])
        return articles
    finally:
        await scraper.close()
