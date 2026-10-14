
import time
import asyncio
from typing import Any

import aiohttp

from config import settings
from logger import get_logger

logger = get_logger(__name__)

# отдельный ворер
class DeribitClient:
    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = (base_url or settings.DERIBIT_API_BASE).rstrip("/")
    #ticker btc_usd или  eth_usd
    async def get_index_price(self, ticker: str) -> dict[str, Any]:
        url = f"{self.base_url}/public/get_index_price"
        params = {"index_name": ticker}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=15)) as response:
                response.raise_for_status()
                payload = await response.json()

        result = payload.get("result")
        price = result.get("index_price")
        if price is None:
            raise ValueError(f"Deribit response has no index_price for {ticker}: {payload}")

        # если нет служебных меток записываем своё вреся
        timestamp = payload.get("usOut") or payload.get("usIn")
        if timestamp is not None:

            timestamp = int(timestamp) // 1_000_000
        else:


            timestamp = int(time.time())

        return {
            "ticker": ticker,
            "price": float(price),
            "timestamp": timestamp,
        }


async def fetch_all_tickers(client: DeribitClient | None = None) -> list[dict[str, Any]]:
    client = client or DeribitClient()
    # сделал влодженную функцию так как использщуется тольок тут а светить её в модуле нет смысла и опасно
    async def _one(ticker: str) -> dict[str, Any] | None:
        try:
            return await client.get_index_price(ticker)
        except Exception:
            logger.exception("Не удалось получить цену: %s", ticker)
            return None

    gathered = await asyncio.gather(*[_one(ticker) for ticker in settings.TICKERS])
    return [item for item in gathered if item is not None]# фильтруе без ответов
