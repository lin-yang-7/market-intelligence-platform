import time
from dataclasses import dataclass

from .responses import ServiceError


@dataclass
class RateBucket:
    window_start: int
    count: int = 0


class FixedWindowRateLimiter:
    def __init__(self) -> None:
        self._buckets: dict[str, RateBucket] = {}

    def check(self, key: str, limit: int, window_seconds: int = 60) -> None:
        now = int(time.time())
        window_start = now - (now % window_seconds)
        bucket = self._buckets.get(key)
        if bucket is None or bucket.window_start != window_start:
            self._buckets[key] = RateBucket(window_start=window_start, count=1)
            return

        bucket.count += 1
        if bucket.count > limit:
            raise ServiceError(1003, "Rate limit exceeded")

