import asyncio
import pytest
import fakeredis.aioredis as fakeredis
from redis.exceptions import RedisError

from src.services.redis_service import RedisService


# Fixture for initializing RedisService with a mocked Redis client
@pytest.fixture
async def redis_service():
    # Use fakeredis to create an in-memory mock of Redis
    fake_redis = await fakeredis.FakeRedis(decode_responses=True)
    service = RedisService(redis_client=fake_redis)
    yield service
    await fake_redis.aclose()
    await fake_redis.connection_pool.disconnect()  # Ensure all connections are closed


# Tests for Cache Management
@pytest.mark.asyncio
async def test_set_and_get_cache(redis_service: RedisService):
    key = "test_cache_key"
    value = "test_value"

    # Test set_cache
    await redis_service.set_cache(key, value, expiration=10)
    # Test get_cache
    result = await redis_service.get_cache(key)

    assert result == value, f"Expected value: {value}, but got: {result}"


@pytest.mark.asyncio
async def test_get_cache_missing_key(redis_service: RedisService):
    key = "non_existent_key"

    result = await redis_service.get_cache(key)
    assert result is None, "Expected None for missing key"


# Tests for Session Management
@pytest.mark.asyncio
async def test_set_and_get_session(redis_service: RedisService):
    session_id = "test_session_id"
    data = {"user_id": "123", "role": "admin"}

    # Test set_session
    await redis_service.set_session(session_id, data, expiration=10)
    # Test get_session
    result = await redis_service.get_session(session_id)

    assert result == data, f"Expected session data: {data}, but got: {result}"


@pytest.mark.asyncio
async def test_get_session_missing(redis_service: RedisService):
    session_id = "non_existent_session"

    result = await redis_service.get_session(session_id)
    assert result == {}, "Expected empty dictionary for missing session"


# Tests for Event Bus (Pub/Sub)
@pytest.mark.asyncio
async def test_publish_and_subscribe(redis_service: RedisService):
    channel = "test_channel"
    message = "test_message"

    received_messages = []

    async def listener(data):
        received_messages.append(data)

    # Run subscriber in a separate task
    subscriber_task = asyncio.create_task(redis_service.subscribe(channel, listener))

    # Publish message
    await asyncio.sleep(1)  # Give some time for the subscription to start
    await redis_service.publish(channel, message)
    await asyncio.sleep(1)  # Give some time for the message to be received

    assert message in received_messages, f"Expected message '{message}' to be received"
    subscriber_task.cancel()  # Cleanup: Cancel the subscriber task


# Tests for Message Queue (Using Lists)
@pytest.mark.asyncio
async def test_enqueue_and_dequeue(redis_service: RedisService):
    queue_name = "test_queue"
    value = "test_task"

    # Test enqueue
    await redis_service.enqueue(queue_name, value)
    # Test dequeue
    result = await redis_service.dequeue(queue_name)

    assert result == value, f"Expected dequeued value: {value}, but got: {result}"


@pytest.mark.asyncio
async def test_dequeue_empty_queue(redis_service: RedisService):
    queue_name = "empty_queue"

    result = await redis_service.dequeue(queue_name)
    assert result is None, "Expected None for an empty queue"


# Tests for Cleanup and Graceful Shutdown
@pytest.mark.asyncio
async def test_cleanup(redis_service: RedisService):
    await redis_service.cleanup()
    # After cleanup, attempting to use the client should return None or fail silently
    result = await redis_service.get_cache("some_key")
    assert result is None, "Expected None after cleanup, indicating the Redis client is no longer operational"


# Tests for Retry Logic
@pytest.mark.asyncio
async def test_retry_operation(redis_service: RedisService):
    # A function to simulate failure a couple of times before succeeding
    call_counter = {"count": 0}

    async def operation():
        call_counter["count"] += 1
        if call_counter["count"] < 3:
            raise RedisError("Temporary failure")
        return "success"

    # Test retry_operation
    result = await redis_service.retry_operation(operation, retries=5, delay=0.1)
    assert result == "success", "Expected operation to eventually succeed"
    assert call_counter["count"] == 3, f"Expected 3 attempts, but got: {call_counter['count']}"
