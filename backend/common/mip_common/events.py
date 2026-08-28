from typing import Any

from pydantic import BaseModel, Field


class MarketTickerData(BaseModel):
    symbol: str
    price: float
    change24h: float | None = None
    volume24h: float | None = None
    source: str = "exchange"


class MarketEvent(BaseModel):
    event: str = "market.ticker"
    exchange: str
    timestamp: int = Field(description="Unix timestamp in milliseconds.")
    data: dict[str, Any]

