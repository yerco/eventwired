import redis

from src.services.redis_service import RedisService


def create_redis_service(redis_url: str = "redis://localhost:6379", max_connections: int = 10, critical: bool = True):
    try:
        # Test Redis connection synchronously
        sync_redis_client = redis.Redis.from_url(redis_url)
        sync_redis_client.ping()  # Ping to verify connection

        # If successful, create an async Redis service
        return RedisService(redis_url=redis_url, max_connections=max_connections, critical=critical)

    except (redis.ConnectionError, redis.TimeoutError) as e:
        if critical:
            raise Exception(f"Failed to connect to Redis: {e}")
        else:
            print(f"Warning: Failed to connect to Redis. Proceeding without Redis functionality: {e}")
            return None

