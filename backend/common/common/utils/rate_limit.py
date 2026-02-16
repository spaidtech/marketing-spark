from fastapi import HTTPException, status
from redis.asyncio import Redis
from redis.exceptions import RedisError


class RateLimiter:
    def __init__(self, redis_client: Redis, limit: int = 60, window_seconds: int = 60):
        self.redis = redis_client
        self.limit = limit
        self.window = window_seconds

    async def enforce(self, key: str) -> None:
        try:
            current = await self.redis.incr(key)
            if current == 1:
                await self.redis.expire(key, self.window)
            if current > self.limit:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded",
                )
        except RedisError:
            # Fail-open for local/dev environments where Redis may be unavailable.
            return
