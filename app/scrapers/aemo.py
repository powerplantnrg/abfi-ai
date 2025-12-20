"""
AEMO NEMWEB Scraper - Priority 1
Critical data source for real-time energy market intelligence.

Data includes:
- DISPATCHPRICE: 5-minute electricity prices by region
- DISPATCH_UNIT_SCADA: Generator output by DUID (includes bioenergy)
- BIDPEROFFER/BIDDAYOFFER: Market participant bids
"""

import asyncio
import io
import zipfile
from datetime import datetime, timedelta
from typing import Optional
from pathlib import Path

import httpx
from pydantic import BaseModel


class DispatchPrice(BaseModel):
    """5-minute dispatch price data."""
    region_id: str
    settlement_date: datetime
    dispatch_interval: int
    rrp: float  # Regional Reference Price
    raise_reg_rrp: Optional[float] = None
    lower_reg_rrp: Optional[float] = None


class GeneratorOutput(BaseModel):
    """SCADA generator output data."""
    duid: str
    settlement_date: datetime
    scada_value: float  # MW output
    fuel_type: Optional[str] = None


class AEMOScraper:
    """
    AEMO NEMWEB public data scraper.

    Public portal: nemweb.com.au
    Data format: CSV files within ZIP archives, updated real-time
    """

    BASE_URL = "https://nemweb.com.au/Reports/Current"
    ARCHIVE_URL = "https://nemweb.com.au/Reports/Archive"

    # Key data tables
    TABLES = {
        "dispatch_price": "Dispatch_SCADA",
        "trading_price": "Trading",
        "bidperoffer": "Bidperoffer",
        "biddayoffer": "Biddayoffer",
        "dispatch_scada": "Dispatch_SCADA",
    }

    # Bioenergy-related DUIDs (example subset)
    BIOENERGY_DUIDS = [
        "BARCALDN",  # Barcaldine biomass
        "CONDONG1",  # Condong sugar cane
        "INVICTA1",  # Invicta sugar mill
        "KAREEYA1",  # Kareeya hydro (reference)
        "PIONEER1",  # Pioneer sugar mill
        "ROCKHAMP1", # Rockhampton bagasse
    ]

    def __init__(self, client: Optional[httpx.AsyncClient] = None):
        self.client = client or httpx.AsyncClient(timeout=60.0)
        self._rate_limit_delay = 1.0  # 1 second between requests

    async def close(self):
        await self.client.aclose()

    async def _fetch_zip(self, url: str) -> bytes:
        """Fetch a ZIP file from NEMWEB."""
        await asyncio.sleep(self._rate_limit_delay)
        response = await self.client.get(url)
        response.raise_for_status()
        return response.content

    async def _parse_csv_from_zip(self, zip_content: bytes) -> list[dict]:
        """Extract and parse CSV from ZIP archive."""
        records = []
        with zipfile.ZipFile(io.BytesIO(zip_content)) as zf:
            for filename in zf.namelist():
                if filename.endswith('.CSV') or filename.endswith('.csv'):
                    with zf.open(filename) as f:
                        content = f.read().decode('utf-8')
                        records.extend(self._parse_csv_content(content))
        return records

    def _parse_csv_content(self, content: str) -> list[dict]:
        """Parse AEMO CSV format (has header rows marked with 'C' or 'I')."""
        records = []
        lines = content.strip().split('\n')
        headers = None

        for line in lines:
            parts = line.split(',')
            if len(parts) < 2:
                continue

            record_type = parts[0].strip('"')

            # 'I' marks header row, 'D' marks data row
            if record_type == 'I':
                headers = [p.strip('"') for p in parts]
            elif record_type == 'D' and headers:
                row = {}
                for i, val in enumerate(parts):
                    if i < len(headers):
                        row[headers[i]] = val.strip('"')
                records.append(row)

        return records

    async def get_current_dispatch_prices(self) -> list[DispatchPrice]:
        """Get current dispatch prices for all regions."""
        url = f"{self.BASE_URL}/Dispatch_SCADA/"

        # List available files
        response = await self.client.get(url)
        response.raise_for_status()

        # Parse directory listing for latest file
        # In production, would parse HTML for ZIP links
        # For now, return placeholder
        return []

    async def get_dispatch_prices(
        self,
        start_date: datetime,
        end_date: datetime,
        regions: Optional[list[str]] = None
    ) -> list[DispatchPrice]:
        """
        Fetch dispatch prices for date range.

        Args:
            start_date: Start of date range
            end_date: End of date range
            regions: Filter by NEM regions (NSW1, VIC1, QLD1, SA1, TAS1)
        """
        prices = []
        regions = regions or ["NSW1", "VIC1", "QLD1", "SA1", "TAS1"]

        # Would iterate through date range and fetch files
        # This is a skeleton implementation

        return prices

    async def get_bioenergy_generation(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> list[GeneratorOutput]:
        """
        Fetch generation data for bioenergy facilities.

        Filters DISPATCH_UNIT_SCADA for known bioenergy DUIDs.
        """
        outputs = []

        # Would fetch SCADA data and filter for bioenergy DUIDs

        return outputs

    async def get_trading_prices(
        self,
        start_date: datetime,
        end_date: datetime,
        regions: Optional[list[str]] = None
    ) -> list[dict]:
        """
        Fetch 30-minute trading prices.

        Trading prices are the actual settlement prices,
        while dispatch prices are 5-minute operational prices.
        """
        regions = regions or ["NSW1", "VIC1", "QLD1", "SA1", "TAS1"]
        prices = []

        # Would fetch trading price data

        return prices


# Convenience function for one-off fetches
async def fetch_latest_prices() -> list[DispatchPrice]:
    """Fetch latest dispatch prices from AEMO."""
    async with httpx.AsyncClient() as client:
        scraper = AEMOScraper(client)
        return await scraper.get_current_dispatch_prices()
