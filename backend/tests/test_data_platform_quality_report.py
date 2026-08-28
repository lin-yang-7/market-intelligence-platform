from data_platform.app.main import app
from fastapi.testclient import TestClient
from mip_common.responses import now_ms


def test_data_quality_report_api_summarizes_batch() -> None:
    client = TestClient(app)
    current = now_ms()

    response = client.post(
        "/v1/data/quality/report",
        json={
            "events": [
                {
                    "event_type": "market.ticker",
                    "timestamp": current,
                    "source": "binance",
                    "data": {"symbol": "BTCUSDT", "price": 68000},
                },
                {
                    "event_type": "market.ticker",
                    "timestamp": current - 600_000,
                    "source": "binance",
                    "data": {"symbol": "ETHUSDT"},
                },
                {
                    "event_type": "feature.updated",
                    "timestamp": current,
                    "source": "feature-service",
                    "data": {"symbol": "BTCUSDT", "feature": "momentum", "value": 1.2},
                },
            ]
        },
    )

    body = response.json()["data"]

    assert response.status_code == 200
    assert body["totalEvents"] == 3
    assert body["acceptedEvents"] == 2
    assert body["rejectedEvents"] == 1
    assert body["warningEvents"] == 1
    assert body["errorEvents"] == 1
    assert {bucket["eventType"] for bucket in body["buckets"]} == {
        "feature.updated",
        "market.ticker",
    }
    ticker_bucket = next(
        bucket for bucket in body["buckets"] if bucket["eventType"] == "market.ticker"
    )
    assert ticker_bucket["totalEvents"] == 2
    assert ticker_bucket["rejectedEvents"] == 1
