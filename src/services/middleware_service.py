from typing import Callable, List, Tuple

from src.event_bus import Event
from src.middleware.base_middleware import BaseMiddleware


class MiddlewareService:
    def __init__(self):
        self.middlewares: List[Tuple[BaseMiddleware, int]] = []

    def register_middleware(self, middleware: BaseMiddleware, priority: int = 0) -> None:
        self.middlewares.append((middleware, priority))
        # Sort middleware by priority (highest priority first)
        self.middlewares.sort(key=lambda m: m[1], reverse=True)

    async def execute(self, event: Event, handler: Callable[[Event], None]) -> None:
        # Pass the event through all registered middlewares before reaching the handler
        for middleware, _ in self.middlewares:
            if hasattr(middleware, 'before_request'):
                event = await middleware.before_request(event)

        # Call the main handler (controller logic) after all middlewares have run
        await handler(event)

        # Pass the event and response back through the middlewares (after_request)
        for middleware, _ in reversed(self.middlewares):
            if hasattr(middleware, 'after_request'):
                await middleware.after_request(event)

        # Now, after all middlewares, send the response
        response = event.data.get('response')  # Fetch the response prepared by the controller
        if response:
            # Add response headers from the event data if available (including Set-Cookie)
            if 'response_headers' in event.data:
                for header in event.data['response_headers']:
                    response.headers.append(header)

            # print(f"Final response headers: {response.headers}")
            # Finally, send the response
            await response.send(event.data['send'])
