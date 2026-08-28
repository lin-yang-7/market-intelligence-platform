class MarketIntelligenceError(Exception):
    """Base SDK error."""


class ApiError(MarketIntelligenceError):
    def __init__(
        self,
        message: str,
        code: int | None = None,
        status_code: int | None = None,
        request_id: str | None = None,
    ) -> None:
        self.code = code
        self.status_code = status_code
        self.request_id = request_id
        super().__init__(message)


class AuthenticationError(ApiError):
    pass


class RateLimitError(ApiError):
    pass


class ParameterError(ApiError):
    pass


class ServerError(ApiError):
    pass
