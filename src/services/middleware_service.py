from typing import Callable, List, Tuple

from src.core.event_bus import Event, EventBus
from src.middleware.base_middleware import BaseMiddleware


class MiddlewareService:
    def __init__(self, event_bus: EventBus):
        self.middlewares: List[Tuple[BaseMiddleware, int]] = []
        self.event_bus = event_bus

    def register_middleware(self, middleware: BaseMiddleware, priority: int = 0) -> None:
        if not isinstance(middleware, BaseMiddleware):
            raise TypeError(f"{middleware} must be an instance of BaseMiddleware")
        self.middlewares.append((middleware, priority))
        # Sort middleware by priority (highest priority first)
        self.middlewares.sort(key=lambda m: m[1], reverse=True)

    async def execute(self, event: Event, handler: Callable[[Event], None]) -> None:
        # Pass the event through all registered middlewares before reaching the handler
        for middleware, _ in self.middlewares:
            if hasattr(middleware, 'before_request'):
                try:
                    event = await middleware.before_request(event)
                except Exception as e:
                    print(f"Middleware {middleware} failed: {e}")

        # Call the main handler (controller logic) after all middlewares have run
        await handler(event)

        if event.data.get('response_already_sent', False):
            return  # Stop processing since the response has already been sent e.g. 405

        # Pass the event and response back through the middlewares (after_request)
        for middleware, _ in reversed(self.middlewares):
            if hasattr(middleware, 'after_request'):
                await middleware.after_request(event)

        # Now, after all middlewares, send the response
        response = event.data.get('response')  # Fetch the response prepared by the controller
        if event.data.get('response_already_sent', False):
            return
        if response:
            # Add response headers from the event data if available (including Set-Cookie)
            if 'response_headers' in event.data:
                existing_headers = {k: v for k, v in response.headers}
                for k, v in event.data.get('response_headers', []):
                    if k not in existing_headers:
                        response.headers.append((k, v))

            # print(f"Final response headers: {response.headers}")
            # Finally, send the response
            await response.send(event.data['send'])
            # event.data['response_already_sent'] = True
