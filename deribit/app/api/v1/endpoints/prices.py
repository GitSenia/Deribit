from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.schemas.price import PriceOut, TickerName
from app.services.prices import get_all_prices, get_latest_price, get_prices_by_range

router = APIRouter(prefix="/prices")


@router.get("", response_model=list[PriceOut])
async def list_prices(
    ticker: TickerName = Query(..., description="Currency ticker"),
    db: AsyncSession = Depends(get_db),
) -> list[PriceOut]:
    return await get_all_prices(db, ticker.value)


@router.get("/latest", response_model=PriceOut)
async def latest_price(
    ticker: TickerName = Query(..., description="Currency ticker"),
    db: AsyncSession = Depends(get_db),
) -> PriceOut:
    tick = await get_latest_price(db, ticker.value)
    if tick is None:
        raise HTTPException(status_code=404, detail=f"No prices found for ticker={ticker.value}")
    return tick


@router.get("/filter", response_model=list[PriceOut])
async def filter_prices(
    ticker: TickerName = Query(..., description="Currency ticker"),
    from_ts: int = Query(..., alias="from", description="UNIX timestamp from"),
    to_ts: int = Query(..., alias="to", description="UNIX timestamp to"),
    db: AsyncSession = Depends(get_db),
) -> list[PriceOut]:
    if from_ts > to_ts:
        raise HTTPException(status_code=422, detail="'from' must be <= 'to'")
    return await get_prices_by_range(db, ticker.value, from_ts, to_ts)
