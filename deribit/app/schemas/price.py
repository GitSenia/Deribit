from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class TickerName(str, Enum):
    BTC_USD = "btc_usd"
    ETH_USD = "eth_usd"


class PriceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ticker: TickerName
    price: float = Field(..., description="цена")
    timestamp: int = Field(..., description="UNIX вреия в сек")
