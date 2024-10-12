import asyncio
import time

import aiohttp
import logging

from src.middleware.base_middleware import BaseMiddleware
from src.event_bus import Event

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


class IpGeolocationMiddleware(BaseMiddleware):
    def __init__(self):
        self.throttler = SimpleThrottler(rate_limit=100, period=15)  # 100 requests per 15 seconds

    async def before_request(self, event: Event) -> Event:
        request = event.data['request']
        try:
            geolocation_data = await self.get_ip_geolocation(request.real_ip)
            if geolocation_data:
                logger.info(f"Geolocation data: {geolocation_data}")
            else:
                logger.info(f"Could not retrieve geolocation data for {request.real_ip}")
        except Exception as e:
            logger.error(f"Geolocation lookup failed: {str(e)}")
            # Proceed without geolocation to avoid degrading the user experience
        return event

    async def after_request(self, event: Event) -> None:
        pass

    async def get_ip_geolocation(self, ip_address: str):
        await self.throttler.throttle()  # Apply throttling
        url = f"https://ipinfo.io/{ip_address}/json"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=2) as response:
                    logger.debug(f"Geolocation API status: {response.status}")
                    if response.status == 200:
                        json_data = await response.json()
                        logger.debug(f"Geolocation API response: {json_data}")
                        return json_data
                    else:
                        logger.warning(f"Failed to get geolocation data from ipinfo.io for {ip_address}: {response.status}")
        except aiohttp.ClientError as e:
            logger.error(f"Error fetching geolocation data from ipinfo.io: {str(e)}")

        # Fallback to another geolocation service
        try:
            fallback_url = f"https://geojs.io/v1/ip/geo/{ip_address}.json"
            async with aiohttp.ClientSession() as session:
                async with session.get(fallback_url, timeout=5) as response:
                    logger.debug(f"Fallback geolocation API status: {response.status}")
                    if response.status == 200:
                        fallback_data = await response.json()
                        logger.debug(f"Fallback geolocation API response: {fallback_data}")
                        return fallback_data
                    else:
                        logger.warning(f"Failed to get geolocation data from fallback service for {ip_address}: {response.status}")
        except aiohttp.ClientError as e:
            logger.error(f"Error fetching geolocation data from fallback service: {str(e)}")

        return None  # Return None if both services fail


class SimpleThrottler:
    def __init__(self, rate_limit, period):
        self.rate_limit = rate_limit
        self.period = period
        self.request_times = []
        self.lock = asyncio.Lock()

    async def throttle(self):
        async with self.lock:
            now = time.time()
            self.request_times = [t for t in self.request_times if now - t < self.period]

            if len(self.request_times) >= self.rate_limit:
                wait_time = self.period - (now - self.request_times[0])
                await asyncio.sleep(wait_time)

            self.request_times.append(time.time())
