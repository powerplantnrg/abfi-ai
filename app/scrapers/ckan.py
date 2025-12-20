"""
CKAN API Client - Priority 4
Primary programmatic gateway for structured government data.

Supports all Australian government data portals:
- data.gov.au (federal)
- data.qld.gov.au (Queensland)
- discover.data.vic.gov.au (Victoria)
- data.nsw.gov.au (NSW)
- data.sa.gov.au (South Australia)
"""

import asyncio
from datetime import datetime
from typing import Any, Optional

import httpx
from pydantic import BaseModel


class CKANDataset(BaseModel):
    """CKAN dataset metadata."""
    id: str
    name: str
    title: str
    notes: Optional[str] = None
    url: Optional[str] = None
    organization: Optional[str] = None
    resources: list[dict] = []
    tags: list[str] = []
    created: Optional[datetime] = None
    modified: Optional[datetime] = None


class CKANResource(BaseModel):
    """CKAN dataset resource (file)."""
    id: str
    name: str
    format: str
    url: str
    description: Optional[str] = None
    size: Optional[int] = None
    last_modified: Optional[datetime] = None


class CKANClient:
    """
    CKAN API client for Australian government data portals.

    API Documentation: https://docs.ckan.org/en/latest/api/
    """

    # Australian government CKAN endpoints
    PORTALS = {
        "federal": "https://data.gov.au/data/api/action",
        "queensland": "https://data.qld.gov.au/api/action",
        "victoria": "https://discover.data.vic.gov.au/api/action",
        "nsw": "https://data.nsw.gov.au/api/action",
        "south_australia": "https://data.sa.gov.au/api/action",
        "western_australia": "https://data.wa.gov.au/api/action",
    }

    # Key bioenergy datasets
    BIOENERGY_DATASETS = [
        "australian-biomass-for-bioenergy-assessment",
        "resources-and-energy-quarterly",
        "australian-energy-statistics",
    ]

    def __init__(
        self,
        portal: str = "federal",
        client: Optional[httpx.AsyncClient] = None
    ):
        self.base_url = self.PORTALS.get(portal, self.PORTALS["federal"])
        self.portal = portal
        self.client = client or httpx.AsyncClient(timeout=60.0)
        self._rate_limit_delay = 1.0

    async def close(self):
        await self.client.aclose()

    async def _api_call(
        self,
        action: str,
        params: Optional[dict] = None,
        method: str = "GET"
    ) -> dict:
        """Make CKAN API call."""
        await asyncio.sleep(self._rate_limit_delay)

        url = f"{self.base_url}/{action}"

        if method == "GET":
            response = await self.client.get(url, params=params)
        else:
            response = await self.client.post(url, json=params)

        response.raise_for_status()
        data = response.json()

        if not data.get("success"):
            raise ValueError(f"CKAN API error: {data.get('error', 'Unknown error')}")

        return data.get("result", {})

    async def search_datasets(
        self,
        query: str,
        limit: int = 10,
        offset: int = 0
    ) -> list[CKANDataset]:
        """
        Search for datasets matching query.

        Args:
            query: Search query (supports Solr syntax)
            limit: Maximum results to return
            offset: Pagination offset
        """
        result = await self._api_call("package_search", {
            "q": query,
            "rows": limit,
            "start": offset,
        })

        datasets = []
        for pkg in result.get("results", []):
            datasets.append(CKANDataset(
                id=pkg.get("id", ""),
                name=pkg.get("name", ""),
                title=pkg.get("title", ""),
                notes=pkg.get("notes"),
                url=pkg.get("url"),
                organization=pkg.get("organization", {}).get("title"),
                resources=[{
                    "id": r.get("id"),
                    "name": r.get("name"),
                    "format": r.get("format"),
                    "url": r.get("url"),
                } for r in pkg.get("resources", [])],
                tags=[t.get("name", "") for t in pkg.get("tags", [])],
            ))

        return datasets

    async def get_dataset(self, dataset_id: str) -> Optional[CKANDataset]:
        """Get dataset by ID or name."""
        try:
            result = await self._api_call("package_show", {"id": dataset_id})
            return CKANDataset(
                id=result.get("id", ""),
                name=result.get("name", ""),
                title=result.get("title", ""),
                notes=result.get("notes"),
                url=result.get("url"),
                organization=result.get("organization", {}).get("title"),
                resources=[{
                    "id": r.get("id"),
                    "name": r.get("name"),
                    "format": r.get("format"),
                    "url": r.get("url"),
                } for r in result.get("resources", [])],
                tags=[t.get("name", "") for t in result.get("tags", [])],
            )
        except Exception:
            return None

    async def datastore_search(
        self,
        resource_id: str,
        filters: Optional[dict] = None,
        limit: int = 100,
        offset: int = 0
    ) -> list[dict]:
        """
        Search resource data using DataStore API.

        Args:
            resource_id: Resource ID
            filters: Key-value filters
            limit: Maximum records
            offset: Pagination offset
        """
        params = {
            "resource_id": resource_id,
            "limit": limit,
            "offset": offset,
        }
        if filters:
            params["filters"] = filters

        result = await self._api_call("datastore_search", params)
        return result.get("records", [])

    async def datastore_search_sql(self, sql: str) -> list[dict]:
        """
        Execute SQL query on DataStore.

        Example:
            SELECT * FROM "resource_id" WHERE category = 'bioenergy' LIMIT 100
        """
        result = await self._api_call("datastore_search_sql", {"sql": sql}, method="POST")
        return result.get("records", [])

    async def get_bioenergy_datasets(self) -> list[CKANDataset]:
        """Search for bioenergy-related datasets."""
        return await self.search_datasets("bioenergy OR biomass OR biogas", limit=50)

    async def get_abba_data(self) -> Optional[CKANDataset]:
        """
        Get Australian Biomass for Bioenergy Assessment (ABBA) dataset.

        Contains state-by-state biomass volumes.
        """
        return await self.get_dataset("australian-biomass-for-bioenergy-assessment")

    async def get_energy_statistics(self) -> Optional[CKANDataset]:
        """Get Australian Energy Statistics dataset."""
        datasets = await self.search_datasets("australian energy statistics")
        if datasets:
            return datasets[0]
        return None


class StateCKANClient(CKANClient):
    """
    State-specific CKAN client with additional datasets.
    """

    # State-specific bioenergy datasets
    STATE_DATASETS = {
        "queensland": [
            "abba-cropping-residues",
            "sugarcane-bagasse-availability",
        ],
        "nsw": [
            "renewable-energy-zones",
        ],
        "victoria": [
            "renewable-energy-target-progress",
        ],
        "south_australia": [
            "energy-mining-data",
        ],
    }

    async def get_state_bioenergy_data(self) -> list[CKANDataset]:
        """Get state-specific bioenergy datasets."""
        datasets = []
        state_datasets = self.STATE_DATASETS.get(self.portal, [])

        for dataset_name in state_datasets:
            ds = await self.get_dataset(dataset_name)
            if ds:
                datasets.append(ds)

        return datasets


async def fetch_all_bioenergy_data() -> dict[str, list[CKANDataset]]:
    """Fetch bioenergy data from all Australian CKAN portals."""
    results = {}

    for portal_name in CKANClient.PORTALS:
        client = CKANClient(portal=portal_name)
        try:
            datasets = await client.get_bioenergy_datasets()
            results[portal_name] = datasets
        except Exception:
            results[portal_name] = []
        finally:
            await client.close()

    return results
