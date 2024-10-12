import pytest
import time
from aioresponses import aioresponses
from unittest.mock import AsyncMock, patch

from src.event_bus import Event

from demo_app.middleware.ip_geolocation_middleware import IpGeolocationMiddleware, SimpleThrottler


@pytest.mark.asyncio
async def test_ip_geolocation_middleware_success(monkeypatch):
    # Mock event and request
    request_mock = AsyncMock()
    request_mock.real_ip = "8.8.8.8"  # Mocking a valid IP address
    event = Event(name="http.request.received", data={"request": request_mock})

    # Mock successful geolocation API response
    with aioresponses() as mock_responses:
        mock_responses.get(
            "https://ipinfo.io/8.8.8.8/json",
            payload={"ip": "8.8.8.8", "country": "US", "region": "California", "city": "Mountain View"}
        )

        middleware = IpGeolocationMiddleware()

        # Run before_request and assert the log call
        with patch('logging.Logger.info') as mock_logger_info:
            await middleware.before_request(event)
            mock_logger_info.assert_any_call(
                "Geolocation data: {'ip': '8.8.8.8', 'country': 'US', 'region': 'California', 'city': 'Mountain View'}"
            )


@pytest.mark.asyncio
async def test_ip_geolocation_middleware_fallback(monkeypatch):
    # Mock event and request
    request_mock = AsyncMock()
    request_mock.real_ip = "8.8.8.8"
    event = Event(name="http.request.received", data={"request": request_mock})

    # Mock a failure on ipinfo.io and a successful fallback to geojs.io
    with aioresponses() as mock_responses:
        # ipinfo.io fails
        mock_responses.get("https://ipinfo.io/8.8.8.8/json", status=500)

        # geojs.io succeeds
        mock_responses.get(
            "https://geojs.io/v1/ip/geo/8.8.8.8.json",
            payload={"ip": "8.8.8.8", "country": "US", "city": "Mountain View"}
        )

        middleware = IpGeolocationMiddleware()

        # Run before_request and assert the fallback log
        with patch('logging.Logger.info') as mock_logger_info:
            await middleware.before_request(event)

            # Ensure the fallback geolocation service was logged
            mock_logger_info.assert_any_call(
                "Geolocation data: {'ip': '8.8.8.8', 'country': 'US', 'city': 'Mountain View'}"
            )


@pytest.mark.asyncio
async def test_ip_geolocation_middleware_throttling(monkeypatch):
    # Mock event and request
    request_mock = AsyncMock()
    request_mock.client_ip = "8.8.8.8"
    event = Event(name="http.request.received", data={"request": request_mock})

    # Mock successful geolocation API response
    with aioresponses() as mock_responses:
        mock_responses.get(
            "https://ipinfo.io/8.8.8.8/json",
            payload={"ip": "8.8.8.8", "country": "US", "region": "California", "city": "Mountain View"}
        )

        # Replace the throttler with a mock that simulates throttling behavior
        throttler_mock = AsyncMock()
        middleware = IpGeolocationMiddleware()
        middleware.throttler = throttler_mock

        await middleware.before_request(event)

        # Assert throttler was called
        throttler_mock.throttle.assert_awaited_once()

@pytest.mark.asyncio
async def test_throttler_behavior():
    throttler = SimpleThrottler(rate_limit=2, period=3)  # 2 requests per 3 seconds

    start_time = time.time()

    # Make 2 requests successfully
    await throttler.throttle()
    await throttler.throttle()

    # Make a third request, which should be throttled
    await throttler.throttle()

    elapsed_time = time.time() - start_time

    # Ensure that the throttler made the third request wait
    assert elapsed_time >= 3, "Throttler did not properly enforce the rate limit"
