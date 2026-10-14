from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import PriceTick


async def save_price(session: AsyncSession,ticker: str,price: float,timestamp: int,) -> PriceTick:
    tick = PriceTick(ticker=ticker, price=price, timestamp=timestamp)
    session.add(tick)
    await session.commit()
    await session.refresh(tick)
    return tick


async def get_all_prices(session: AsyncSession, ticker: str) -> list[PriceTick]:
    stmt = (select(PriceTick).where(PriceTick.ticker == ticker).order_by(PriceTick.timestamp.asc()))
    result = await session.scalars(stmt)
    return list(result.all())


async def get_latest_price(session: AsyncSession, ticker: str) -> PriceTick | None:
    stmt = (select(PriceTick).where(PriceTick.ticker == ticker).order_by(PriceTick.timestamp.desc()).limit(1))
    result = await session.scalars(stmt)
    return result.first()


async def get_prices_by_range(session: AsyncSession,ticker: str, from_ts: int,to_ts: int,) -> list[PriceTick]:
    stmt = (select(PriceTick)
            .where( PriceTick.ticker == ticker,PriceTick.timestamp >= from_ts,PriceTick.timestamp <= to_ts,).order_by(PriceTick.timestamp.asc()))
    result = await session.scalars(stmt)
    return list(result.all())
