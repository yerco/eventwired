from src.middleware.base_middleware import BaseMiddleware
from src.core.event_bus import Event


class LoggingMiddleware(BaseMiddleware):
    async def before_request(self, event: Event) -> Event:
        request = event.data['request']
        print(f"Logging before request: {request.path}")
        return event  # Return the event object (possibly modified)

    async def after_request(self, event: Event) -> None:
        request = event.data['request']
        print(f"Logging after request: {request.path}")
