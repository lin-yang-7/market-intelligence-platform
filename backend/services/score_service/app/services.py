from mip_common.responses import ServiceError

from .ai_client import AiScoreClient, DisabledAiScoreClient
from .schemas import FactorContribution, ScoreBatchRequest, ScoreRequest, ScoreResult

SCORE_FEATURES: dict[str, str] = {
    "longInflow": "long_inflow_score",
    "momentum": "price_momentum",
    "volume": "volume_activity",
}

OVERALL_WEIGHTS = {
    "long_inflow_score": 0.5,
    "price_momentum": 0.3,
    "volume_activity": 0.2,
}


class ScoreService:
    def __init__(self, ai_client: AiScoreClient | None = None) -> None:
        self.ai_client = ai_client or DisabledAiScoreClient()

    async def calculate(self, request: ScoreRequest) -> ScoreResult:
        score_type = self._normalize_type(request.scoreType)
        ai_score = None
        if score_type in {"overall", "longInflow"}:
            ai_score = await self.ai_client.score(request.symbol, request.exchange, request.factors)
        if ai_score:
            return ScoreResult(
                symbol=request.symbol.upper(),
                exchange=request.exchange.lower(),
                scoreType=score_type,
                score=round(ai_score.overallScore, 4),
                confidence=round(ai_score.confidence, 4),
                factors={**request.factors, **ai_score.factors},
                contributions=[
                    FactorContribution(
                        factor=factor,
                        value=value,
                        weight=1.0,
                        contribution=value,
                    )
                    for factor, value in ai_score.factors.items()
                ],
                modelVersion=ai_score.modelVersion,
                opportunityScore=ai_score.opportunityScore,
                riskScore=ai_score.riskScore,
                riskWarning=ai_score.riskWarning,
            )
        return self._rule_score(request, score_type)

    async def batch(self, request: ScoreBatchRequest) -> list[ScoreResult]:
        return [await self.calculate(item) for item in request.items]

    def _rule_score(self, request: ScoreRequest, score_type: str) -> ScoreResult:
        contributions = self._contributions(score_type, request.factors)
        score = round(min(100.0, sum(item.contribution for item in contributions)), 4)
        return ScoreResult(
            symbol=request.symbol.upper(),
            exchange=request.exchange.lower(),
            scoreType=score_type,
            score=score,
            confidence=self._confidence(request.factors),
            factors=request.factors,
            contributions=contributions,
        )

    def _contributions(
        self,
        score_type: str,
        factors: dict[str, float],
    ) -> list[FactorContribution]:
        if score_type == "overall":
            return [
                FactorContribution(
                    factor=name,
                    value=self._normalized_value(name, value),
                    weight=weight,
                    contribution=self._normalized_value(name, value) * weight,
                )
                for name, weight in OVERALL_WEIGHTS.items()
                for value in [factors.get(name, 0.0)]
            ]

        feature_name = SCORE_FEATURES[score_type]
        value = self._normalized_value(feature_name, factors.get(feature_name, 0.0))
        return [
            FactorContribution(
                factor=feature_name,
                value=value,
                weight=1.0,
                contribution=value,
            )
        ]

    def _normalize_type(self, score_type: str) -> str:
        if score_type == "overall":
            return score_type
        if score_type not in SCORE_FEATURES:
            raise ServiceError(7001, "Invalid score type")
        return score_type

    @staticmethod
    def _normalized_value(feature_name: str, value: float) -> float:
        if feature_name == "price_momentum":
            return max(0.0, value) * 10.0
        return max(0.0, value)

    @staticmethod
    def _confidence(factors: dict[str, float]) -> float:
        required = {"price_momentum", "volume_activity", "long_inflow_score"}
        coverage = len(required.intersection(factors)) / len(required)
        return round(coverage, 4)
