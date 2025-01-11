import traceback
from typing import Callable

from src.core.lifecycle import handle_lifespan_events
from src.core.http_handler import handle_http_requests
from src.core.request import Request
from src.core.setup_registry import run_setups
from src.core.websocket import handle_websocket_connections
from src.core.dicontainer import DIContainer
from src.core.event_bus import Event


class FrameworkApp:
    def __init__(self, container: DIContainer, register_routes: Callable):
        self.container = container
        self.register_routes = register_routes

    async def __call__(self, scope: dict, receive: Callable, send: Callable) -> None:
        try:
            request = Request(scope, receive)
            if scope['type'] == 'lifespan':
                await handle_lifespan_events(scope, receive, send)
            elif scope['type'] == 'http':
                await handle_http_requests(scope, receive, send, request, self.container)
            elif scope['type'] == 'websocket':
                await handle_websocket_connections(scope, receive, send, request, self.container)
        except Exception as e:
            traceback.print_exc()  # Print traceback for debugging
            print(f"Error in ASGI application: {e}")

            # Publish the error event without sending the response directly
            event_bus = await self.container.get('EventBus')
            event = Event(name="http.error.500", data={'exception': e, 'traceback': traceback.format_exc(), 'send': send})
            await event_bus.publish(event)

    async def setup(self):
        await run_setups(self.container)
        routing_service = await self.container.get('RoutingService')
        # Custom route registration logic for the user app
        await self.register_routes(routing_service)