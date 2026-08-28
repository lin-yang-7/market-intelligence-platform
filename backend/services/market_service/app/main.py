from fastapi import Depends, FastAPI, Query, Request
from mip_common.errors import service_error_handler
from mip_common.logging import install_logging
from mip_common.middleware import RequestIdMiddleware
from mip_common.ops import install_ops_routes
from mip_common.responses import ServiceError, ok

from .dependencies import get_market_service
from .services import MarketService

app = FastAPI(title="Market Service", version="0.1.0")
install_logging(app, "market-service")
app.add_middleware(RequestIdMiddleware)


app.add_exception_handler(ServiceError, service_error_handler)
install_ops_routes(app, "market-service")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/v1/market/ticker")
async def get_ticker(
    request: Request,
    symbol: str = Query(..., min_length=3, max_length=30),
    exchange: str | None = Query(default=None, min_length=2, max_length=30),
    service: MarketService = Depends(get_market_service),
):
    ticker = await service.get_ticker(symbol=symbol, exchange=exchange)
    return ok(ticker, request_id=request.state.request_id)


@app.get("/v1/market/kline")
async def get_kline(
    request: Request,
    symbol: str = Query(..., min_length=3, max_length=30),
    interval: str = Query(..., min_length=2, max_length=8),
    exchange: str | None = Query(default=None, min_length=2, max_length=30),
    startTime: int | None = Query(default=None, ge=0),
    endTime: int | None = Query(default=None, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    service: MarketService = Depends(get_market_service),
):
    klines = await service.get_klines(
        symbol=symbol,
        interval=interval,
        exchange=exchange,
        start_time=startTime,
        end_time=endTime,
        limit=limit,
    )
    return ok(klines, request_id=request.state.request_id)


@app.get("/v1/market/trades")
async def get_trades(
    request: Request,
    symbol: str = Query(..., min_length=3, max_length=30),
    exchange: str | None = Query(default=None, min_length=2, max_length=30),
    startTime: int | None = Query(default=None, ge=0),
    endTime: int | None = Query(default=None, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    service: MarketService = Depends(get_market_service),
):
    trades = await service.get_trades(
        symbol=symbol,
        exchange=exchange,
        start_time=startTime,
        end_time=endTime,
        limit=limit,
    )
    return ok(trades, request_id=request.state.request_id)


@app.get("/v1/market/funding")
async def get_funding(
    request: Request,
    symbol: str = Query(..., min_length=3, max_length=30),
    exchange: str | None = Query(default=None, min_length=2, max_length=30),
    startTime: int | None = Query(default=None, ge=0),
    endTime: int | None = Query(default=None, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    service: MarketService = Depends(get_market_service),
):
    funding = await service.get_funding_rates(
        symbol=symbol,
        exchange=exchange,
        start_time=startTime,
        end_time=endTime,
        limit=limit,
    )
    return ok(funding, request_id=request.state.request_id)


@app.get("/v1/market/openInterest")
async def get_open_interest(
    request: Request,
    symbol: str = Query(..., min_length=3, max_length=30),
    exchange: str | None = Query(default=None, min_length=2, max_length=30),
    startTime: int | None = Query(default=None, ge=0),
    endTime: int | None = Query(default=None, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    service: MarketService = Depends(get_market_service),
):
    open_interest = await service.get_open_interest(
        symbol=symbol,
        exchange=exchange,
        start_time=startTime,
        end_time=endTime,
        limit=limit,
    )
    return ok(open_interest, request_id=request.state.request_id)


@app.get("/v1/market/liquidation")
async def get_liquidation(
    request: Request,
    symbol: str = Query(..., min_length=3, max_length=30),
    exchange: str | None = Query(default=None, min_length=2, max_length=30),
    startTime: int | None = Query(default=None, ge=0),
    endTime: int | None = Query(default=None, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    service: MarketService = Depends(get_market_service),
):
    liquidations = await service.get_liquidations(
        symbol=symbol,
        exchange=exchange,
        start_time=startTime,
        end_time=endTime,
        limit=limit,
    )
    return ok(liquidations, request_id=request.state.request_id)
