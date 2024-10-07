import redis.asyncio as aioredis
import redis
import asyncio
from typing import Any, Dict, Callable, Optional
from redis.exceptions import RedisError


class RedisService:
    def __init__(self, redis_url: str = "redis://localhost:6379", max_connections: int = 10, redis_client=None, critical: bool = True):
        # Allow dependency injection for testing with a mock client
        self.pool = None  # Always initialize self.pool, either with None or an actual pool
        self.critical = critical

        try:
            if redis_client:
                self.client = redis_client
            else:
                # Initialize Redis connection pool
                self.pool = aioredis.ConnectionPool.from_url(
                    redis_url,
                    decode_responses=True,
                    max_connections=max_connections
                )
                self.client = aioredis.Redis(connection_pool=self.pool)
        except (redis.ConnectionError, redis.TimeoutError) as e:
            # If Redis is critical, raise an error
            if critical:
                raise Exception(f"Failed to connect to Redis: {e}")
            else:
                print(f"Warning: Failed to connect to Redis. Proceeding without Redis functionality: {e}")
                self.client = None

    # Cache Management
    async def set_cache(self, key: str, value: Any, expiration: int = 3600) -> None:
        try:
            await self.client.set(key, value, ex=expiration)
            print(f"Cache set for key: {key}")
        except RedisError as e:
            print(f"Error setting cache for key '{key}': {e}")
            raise

    async def get_cache(self, key: str) -> Optional[Any]:
        try:
            return await self.client.get(key)
        except RedisError as e:
            print(f"Error getting cache for key '{key}': {e}")
            raise

    # Session Management
    async def set_session(self, session_id: str, data: Dict[str, Any], expiration: int = 3600) -> None:
        try:
            await self.client.hset(session_id, mapping=data)
            await self.client.expire(session_id, expiration)
            print(f"Session set for session_id: {session_id}")
        except RedisError as e:
            print(f"Error setting session for session_id '{session_id}': {e}")
            raise

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        try:
            session_data = await self.client.hgetall(session_id)
            if session_data:
                print(f"Session retrieved for session_id: {session_id}")
            return session_data
        except RedisError as e:
            print(f"Error getting session for session_id '{session_id}': {e}")
            raise

    # Event Bus (Pub/Sub)
    async def publish(self, channel: str, message: str) -> None:
        try:
            await self.client.publish(channel, message)
            print(f"Published message to channel '{channel}': {message}")
        except RedisError as e:
            print(f"Error publishing to channel '{channel}': {e}")
            raise

    async def subscribe(self, channel: str, listener: Callable[[str], None]) -> None:
        try:
            pubsub = self.client.pubsub()
            await pubsub.subscribe(channel)

            print(f"Subscribed to channel: {channel}")
            async for message in pubsub.listen():
                if message["type"] == "message":
                    await listener(message["data"])
        except RedisError as e:
            print(f"Error subscribing to channel '{channel}': {e}")
            raise

    # Message Queue (Using Lists)
    async def enqueue(self, queue_name: str, value: Any) -> None:
        try:
            await self.client.rpush(queue_name, value)
            print(f"Enqueued value '{value}' to queue '{queue_name}'")
        except RedisError as e:
            print(f"Error enqueuing to queue '{queue_name}': {e}")
            raise

    async def dequeue(self, queue_name: str) -> Optional[Any]:
        try:
            value = await self.client.lpop(queue_name)
            if value:
                print(f"Dequeued value '{value}' from queue '{queue_name}'")
            return value
        except RedisError as e:
            print(f"Error dequeuing from queue '{queue_name}': {e}")
            raise

    # Cleanup and Graceful Shutdown
    async def cleanup(self) -> None:
        try:
            await self.client.aclose()
            if self.pool:
                await self.pool.disconnect()
            print("Redis connections closed successfully.")
        except RedisError as e:
            print(f"Error during Redis cleanup: {e}")
            raise

    # Retry Logic
    async def retry_operation(self, operation: Callable, *args, retries: int = 3, delay: int = 1, **kwargs):
        """Retries the given operation multiple times in case of failure."""
        for attempt in range(1, retries + 1):
            try:
                return await operation(*args, **kwargs)
            except RedisError as e:
                if attempt < retries:
                    print(f"Retry {attempt}/{retries} for operation '{operation.__name__}' failed: {e}")
                    await asyncio.sleep(delay)
                else:
                    print(f"Operation '{operation.__name__}' failed after {retries} retries.")
                    raise
