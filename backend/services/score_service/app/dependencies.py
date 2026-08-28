from mip_common.config import get_settings

from .ai_client import DisabledAiScoreClient, HttpAiScoreClient
from .services import ScoreService


def get_score_service() -> ScoreService:
    settings = get_settings()
    ai_client = (
        HttpAiScoreClient(settings.ai_service_url)
        if settings.ai_scoring_enabled
        else DisabledAiScoreClient()
    )
    return ScoreService(ai_client)
