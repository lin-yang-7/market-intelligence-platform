from scripts.internal_smart_coin_app import build_snapshot, score_ticker, with_changes


def ticker(symbol: str, change: float, volume: float, high: float = 110, low: float = 95):
    return {
        "symbol": symbol,
        "lastPrice": "100",
        "priceChangePercent": str(change),
        "quoteVolume": str(volume),
        "count": "50000",
        "highPrice": str(high),
        "lowPrice": str(low),
        "openPrice": "100",
    }


def test_score_ticker_produces_directional_scores() -> None:
    bullish = score_ticker(ticker("AAAUSDT", 8, 200_000_000))
    bearish = score_ticker(ticker("BBBUSDT", -9, 5_000_000))

    assert bullish.abnormalBullishScore > bullish.riskBearishScore
    assert bearish.riskBearishScore > bearish.opportunityBullishScore
    for score in [
        bullish.abnormalBullishScore,
        bullish.opportunityBullishScore,
        bullish.riskBearishScore,
        bearish.abnormalBullishScore,
        bearish.opportunityBullishScore,
        bearish.riskBearishScore,
    ]:
        assert 0 <= score <= 100


def test_snapshot_lists_use_condition_membership_then_rank_independently() -> None:
    rows = [
        score_ticker(ticker("AAAUSDT", 12, 400_000_000)),
        score_ticker(ticker("BBBUSDT", 9, 300_000_000)),
        score_ticker(ticker("CCCUSDT", 0.5, 500_000_000)),
        score_ticker(ticker("DDDUSDT", 4, 500_000)),
        score_ticker(ticker("EEEUSDT", -8, 15_000_000)),
        score_ticker(ticker("FFFUSDT", -7, 20_000_000)),
    ]

    snapshot = build_snapshot(rows, limit=2)

    assert [item.symbol for item in snapshot.abnormalBullish] == ["AAAUSDT", "BBBUSDT"]
    assert [item.symbol for item in snapshot.opportunityBullish] == ["AAAUSDT", "BBBUSDT"]
    assert [item.symbol for item in snapshot.riskBearish] == ["EEEUSDT", "FFFUSDT"]
    assert "CCCUSDT" not in {item.symbol for item in snapshot.abnormalBullish}
    assert "DDDUSDT" not in {item.symbol for item in snapshot.opportunityBullish}


def test_snapshot_changes_report_entered_exited_and_moved() -> None:
    previous = build_snapshot(
        [
            score_ticker(ticker("AAAUSDT", 9, 300_000_000)),
            score_ticker(ticker("BBBUSDT", 8, 250_000_000)),
        ],
        limit=2,
    )
    current = build_snapshot(
        [
            score_ticker(ticker("BBBUSDT", 12, 400_000_000)),
            score_ticker(ticker("CCCUSDT", 7, 260_000_000)),
        ],
        limit=2,
    )

    changed = with_changes(previous, current)

    abnormal = changed.changes["abnormalBullish"]
    assert [item["symbol"] for item in abnormal["entered"]] == ["CCCUSDT"]
    assert [item["symbol"] for item in abnormal["exited"]] == ["AAAUSDT"]
    assert abnormal["moved"][0]["symbol"] == "BBBUSDT"
    assert abnormal["moved"][0]["fromRank"] == 2
    assert abnormal["moved"][0]["toRank"] == 1
