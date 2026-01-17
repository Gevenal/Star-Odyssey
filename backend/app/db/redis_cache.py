"""Redis cache for hot game state."""
import redis.asyncio as redis
from typing import Optional
import orjson
from app.utils.logger import get_logger

logger = get_logger(__name__)


class RedisCache:
    """Cache layer for active game sessions."""

    def __init__(self, redis_url: str):
        self.redis: Optional[redis.Redis] = None
        self.redis_url = redis_url

    async def connect(self):
        """Initialize Redis connection."""
        try:
            logger.info(f"Connecting to Redis at {self.redis_url}")
            self.redis = await redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=False,
            )
            await self.redis.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def disconnect(self):
        """Close Redis connection."""
        if self.redis:
            logger.info("Closing Redis connection")
            await self.redis.close()
            self.redis = None

    async def get_game_state(self, session_id: str) -> Optional[dict]:
        """Get cached game state."""
        if not self.redis:
            raise RuntimeError("Redis not connected")

        try:
            key = f"game_state:{session_id}"
            data = await self.redis.get(key)

            if data:
                logger.debug(f"Cache hit for session {session_id}")
                return orjson.loads(data)

            logger.debug(f"Cache miss for session {session_id}")
            return None

        except Exception as e:
            logger.error(f"Error getting game state from cache: {e}")
            return None

    async def set_game_state(self, session_id: str, state: dict, ttl: int = 3600):
        """Cache game state with TTL."""
        if not self.redis:
            raise RuntimeError("Redis not connected")

        try:
            key = f"game_state:{session_id}"
            data = orjson.dumps(state)
            await self.redis.setex(key, ttl, data)
            logger.debug(f"Cached game state for session {session_id} (TTL: {ttl}s)")

        except Exception as e:
            logger.error(f"Error setting game state in cache: {e}")

    async def delete_game_state(self, session_id: str):
        """Remove game state from cache."""
        if not self.redis:
            raise RuntimeError("Redis not connected")

        try:
            key = f"game_state:{session_id}"
            await self.redis.delete(key)
            logger.debug(f"Deleted cached game state for session {session_id}")

        except Exception as e:
            logger.error(f"Error deleting game state from cache: {e}")

    async def extend_ttl(self, session_id: str, ttl: int = 3600):
        """Extend cache TTL for active session."""
        if not self.redis:
            raise RuntimeError("Redis not connected")

        try:
            key = f"game_state:{session_id}"
            await self.redis.expire(key, ttl)
            logger.debug(f"Extended TTL for session {session_id} to {ttl}s")

        except Exception as e:
            logger.error(f"Error extending TTL: {e}")
