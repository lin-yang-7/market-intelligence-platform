from typing import Protocol

import httpx
from pydantic import BaseModel


class ScoreClientResult(BaseModel):
    score: float
    confidence: float
    factors: dict[str, float]
    modelVersion: str | None = None
    opportunityScore: float | None = None
    riskScore: float | None = None
    riskWarning: str | None = None


class RankingScoreClient(Protocol):
    async def score(
        self,
        score_type: str,
        symbol: str,
        exchange: str,
        factors: dict[str, float],
    ) -> ScoreClientResult | None:
        ...


class DisabledRankingScoreClient:
    async def score(
        self,
        score_type: str,
        symbol: str,
        exchange: str,
        factors: dict[str, float],
    ) -> ScoreClientResult | None:
        return None


class HttpRankingScoreClient:
    def __init__(self, base_url: str, timeout_seconds: float = 0.8) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    async def score(
        self,
        score_type: str,
        symbol: str,
        exchange: str,
        factors: dict[str, float],
    ) -> ScoreClientResult | None:
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(
                    f"{self.base_url}/v1/score/calculate",
                    json={
                        "symbol": symbol,
                        "exchange": exchange,
                        "scoreType": score_type,
                        "factors": factors,
                    },
                )
            response.raise_for_status()
            data = response.json()["data"]
        except (httpx.HTTPError, KeyError, ValueError, TypeError):
            return None
        return ScoreClientResult(
            score=float(data["score"]),
            confidence=float(data["confidence"]),
            factors={key: float(value) for key, value in data.get("factors", {}).items()},
            modelVersion=data.get("modelVersion"),
            opportunityScore=data.get("opportunityScore"),
            riskScore=data.get("riskScore"),
            riskWarning=data.get("riskWarning"),
        )
