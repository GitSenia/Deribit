import asyncio

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.services.deribit_client import fetch_all_tickers
from app.services.prices import save_price
from config import settings
from logger import get_logger
from worker.celery_app import celery

logger = get_logger(__name__)


async def _fetch_and_store() -> int:
    engine = create_async_engine(settings.database_url, poolclass=NullPool)
    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        autoflush=False,
        expire_on_commit=False,
    )

    try:
        prices = await fetch_all_tickers()
        saved = 0

        async with session_factory() as session:
            for item in prices:
                await save_price(
                    session,
                    ticker=item["ticker"],
                    price=item["price"],
                    timestamp=item["timestamp"],
                )
                saved += 1

        logger.info("Сохранено цен: %s", saved)
        return saved
    finally:
        await engine.dispose()


@celery.task(name="worker.fetch_prices")
def fetch_prices() -> int:
    return asyncio.run(_fetch_and_store())
