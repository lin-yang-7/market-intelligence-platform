from functools import lru_cache

from mip_common.config import get_settings
from services.feature_service.app.dependencies import get_repository

from .ai_scorer import DisabledAiRankingScorer, HttpAiRankingScorer
from .score_client import DisabledRankingScoreClient, HttpRankingScoreClient
from .services import RankingService


@lru_cache
def get_ranking_service() -> RankingService:
    settings = get_settings()
    ai_scorer = (
        HttpAiRankingScorer(settings.ai_service_url)
        if settings.ai_scoring_enabled
        else DisabledAiRankingScorer()
    )
    score_client = (
        HttpRankingScoreClient(settings.score_service_url)
        if settings.score_service_enabled
        else DisabledRankingScoreClient()
    )
    return RankingService(get_repository(), ai_scorer, score_client)
