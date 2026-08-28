from __future__ import annotations

from dataclasses import dataclass

from .schemas import FactorContribution, FeatureVector, ModelMetadata, PredictionResult


def clamp(value: float, lower: float = 0, upper: float = 100) -> float:
    return max(lower, min(upper, value))


@dataclass(frozen=True)
class HybridScoringWeights:
    ai_prediction: float = 0.5
    rule_score: float = 0.3
    risk_adjustment: float = 0.2


class HybridScoringModel:
    def __init__(
        self,
        model_version: str = "rule-hybrid-v1",
        weights: HybridScoringWeights | None = None,
    ) -> None:
        self.model_version = model_version
        self.weights = weights or HybridScoringWeights()

    def metadata(self) -> ModelMetadata:
        return ModelMetadata(
            model_name="long-inflow-hybrid-scorer",
            model_version=self.model_version,
            strategy="rule + deterministic prediction + risk adjustment",
            weights={
                "ai_prediction": self.weights.ai_prediction,
                "rule_score": self.weights.rule_score,
                "risk_adjustment": self.weights.risk_adjustment,
            },
            supported_scenarios=["coin_ranking", "signal_prediction", "risk_analysis"],
        )

    def predict(self, symbol: str, exchange: str, features: FeatureVector) -> PredictionResult:
        rule_score = self._rule_score(features)
        prediction_score = self._prediction_score(features)
        risk_score = self._risk_score(features)
        confidence = self._confidence(features, rule_score, risk_score)
        overall = clamp(
            prediction_score * self.weights.ai_prediction
            + rule_score * self.weights.rule_score
            + (100 - risk_score) * self.weights.risk_adjustment
        )

        return PredictionResult(
            symbol=symbol,
            exchange=exchange,
            model_version=self.model_version,
            opportunity_score=round(prediction_score, 2),
            risk_score=round(risk_score, 2),
            confidence=round(confidence, 4),
            overall_score=round(overall, 2),
            prediction=round(overall / 100, 4),
            factors=self._factor_contributions(features),
            risk_warning=self._risk_warning(risk_score, features),
        )

    def _rule_score(self, features: FeatureVector) -> float:
        flow_component = clamp(features.capital_flow / 1_000_000_000 * 18)
        volume_component = (features.volume_imbalance + 1) * 18
        momentum_component = (features.price_momentum + 1) * 16
        liquidity_component = clamp(features.liquidity / 1_000_000_000 * 14)
        volatility_penalty = clamp(features.volatility * 22)
        return clamp(
            flow_component
            + volume_component
            + momentum_component
            + liquidity_component
            - volatility_penalty
        )

    def _prediction_score(self, features: FeatureVector) -> float:
        linear = (
            features.capital_flow / 1_000_000_000 * 22
            + features.volume_imbalance * 28
            + features.price_momentum * 30
            + features.liquidity / 1_000_000_000 * 12
            - features.volatility * 18
            + 42
        )
        return clamp(linear)

    def _risk_score(self, features: FeatureVector) -> float:
        volatility_risk = clamp(features.volatility * 64)
        weak_liquidity_risk = clamp(35 - features.liquidity / 1_000_000_000 * 10)
        negative_momentum_risk = clamp(-features.price_momentum * 24)
        return clamp(volatility_risk + weak_liquidity_risk + negative_momentum_risk)

    def _confidence(self, features: FeatureVector, rule_score: float, risk_score: float) -> float:
        data_quality = 0.92 if features.liquidity > 0 and features.capital_flow != 0 else 0.72
        agreement = 1 - abs(rule_score - (100 - risk_score)) / 100
        return max(0.05, min(0.99, data_quality * (0.65 + agreement * 0.35)))

    def _factor_contributions(self, features: FeatureVector) -> list[FactorContribution]:
        return [
            FactorContribution(
                factor="capital_flow",
                contribution=round(clamp(features.capital_flow / 1_000_000_000 * 22), 2),
                direction="positive" if features.capital_flow >= 0 else "negative",
            ),
            FactorContribution(
                factor="volume_imbalance",
                contribution=round(features.volume_imbalance * 28, 2),
                direction="positive" if features.volume_imbalance >= 0 else "negative",
            ),
            FactorContribution(
                factor="price_momentum",
                contribution=round(features.price_momentum * 30, 2),
                direction="positive" if features.price_momentum >= 0 else "negative",
            ),
            FactorContribution(
                factor="volatility",
                contribution=round(-features.volatility * 18, 2),
                direction="negative" if features.volatility > 0.55 else "neutral",
            ),
        ]

    def _risk_warning(self, risk_score: float, features: FeatureVector) -> str:
        if risk_score >= 70:
            return "High volatility or weak liquidity may reduce signal reliability."
        if features.volume_imbalance < 0:
            return "Volume imbalance conflicts with long inflow direction."
        return "Risk level is within the MVP model tolerance."
