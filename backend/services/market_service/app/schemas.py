from pydantic import BaseModel, Field


class TickerResponse(BaseModel):
    symbol: str
    exchange: str
    price: float
    change24h: float | None = None
    volume24h: float | None = None
    timestamp: int = Field(description="Unix timestamp in milliseconds.")
    source: str = "exchange"


class KlineResponse(BaseModel):
    symbol: str
    exchange: str
    interval: str
    timestamp: int = Field(description="Unix timestamp in milliseconds.")
    open: float
    high: float
    low: float
    close: float
    volume: float
    quoteVolume: float | None = None
    source: str = "exchange"


class TradeResponse(BaseModel):
    symbol: str
    exchange: str
    tradeId: str
    price: float
    quantity: float
    side: str
    timestamp: int = Field(description="Unix timestamp in milliseconds.")
    source: str = "exchange"


class FundingRateResponse(BaseModel):
    symbol: str
    exchange: str
    fundingRate: float
    nextFundingTime: int = Field(description="Unix timestamp in milliseconds.")
    timestamp: int = Field(description="Unix timestamp in milliseconds.")
    source: str = "exchange"


class OpenInterestResponse(BaseModel):
    symbol: str
    exchange: str
    openInterest: float
    changeRate: float
    timestamp: int = Field(description="Unix timestamp in milliseconds.")
    source: str = "exchange"


class LiquidationResponse(BaseModel):
    symbol: str
    exchange: str
    side: str
    price: float
    quantity: float
    value: float
    timestamp: int = Field(description="Unix timestamp in milliseconds.")
    source: str = "exchange"
