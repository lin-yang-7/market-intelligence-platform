from typing import Protocol

import httpx
from pydantic import BaseModel


class AiScore(BaseModel):
    modelVersion: str
    opportunityScore: float
    riskScore: float
    confidence: float
    overallScore: float
    riskWarning: str
    factors: dict[str, float]


class AiScoreClient(Protocol):
    async def score(self, symbol: str, exchange: str, factors: dict[str, float]) -> AiScore | None:
        ...


class DisabledAiScoreClient:
    async def score(self, symbol: str, exchange: str, factors: dict[str, float]) -> AiScore | None:
        return None


class HttpAiScoreClient:
    def __init__(self, base_url: str, timeout_seconds: float = 0.6) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    async def score(self, symbol: str, exchange: str, factors: dict[str, float]) -> AiScore | None:
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(
                    f"{self.base_url}/v1/ai/predict",
                    json={
                        "symbol": symbol,
                        "exchange": exchange,
                        "features": self._to_ai_features(factors),
                    },
                )
            response.raise_for_status()
            data = response.json()["data"]
        except (httpx.HTTPError, KeyError, ValueError, TypeError):
            return None
        return AiScore(
            modelVersion=data["model_version"],
            opportunityScore=float(data["opportunity_score"]),
            riskScore=float(data["risk_score"]),
            confidence=float(data["confidence"]),
            overallScore=float(data["overall_score"]),
            riskWarning=data["risk_warning"],
            factors={
                f"ai_{factor['factor']}": float(factor["contribution"])
                for factor in data.get("factors", [])
            },
        )

    def _to_ai_features(self, factors: dict[str, float]) -> dict[str, float]:
        long_inflow_score = factors.get("long_inflow_score", 0.0)
        volume_activity = factors.get("volume_activity", 0.0)
        price_momentum = factors.get("price_momentum", 0.0)
        return {
            "capital_flow": max(-1.0, long_inflow_score / 100) * 5_000_000_000,
            "volume_imbalance": self._clamp(volume_activity / 50 - 1, -1, 1),
            "price_momentum": self._clamp(price_momentum / 100, -1, 1),
            "volatility": self._clamp(abs(price_momentum) / 100, 0, 1),
            "liquidity": self._clamp(volume_activity / 100, 0, 1) * 2_000_000_000,
        }

    @staticmethod
    def _clamp(value: float, lower: float, upper: float) -> float:
        return max(lower, min(upper, value))
