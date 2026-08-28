from .model import HybridScoringModel
from .schemas import ModelMetadata, PredictionResult, PredictRequest


class PredictionService:
    def __init__(self, model: HybridScoringModel | None = None) -> None:
        self.model = model or HybridScoringModel()

    def metadata(self) -> ModelMetadata:
        return self.model.metadata()

    def predict(self, request: PredictRequest) -> PredictionResult:
        return self.model.predict(
            symbol=request.symbol,
            exchange=request.exchange,
            features=request.features,
        )

    def explain(self, request: PredictRequest) -> PredictionResult:
        return self.predict(request)


prediction_service = PredictionService()
