from typing import Callable
import traceback

from src.core.lifecycle import handle_lifespan_events
from src.core.http_handler import handle_http_requests
from src.core.request import Request
from src.core.websocket import handle_websocket_connections
from src.dicontainer import di_container
from src.event_bus import Event


class FrameworkApp:
    def __init__(self, user_startup_callback: Callable = None):
        self.user_startup_callback = user_startup_callback
        self._initialized = False

    async def __call__(self, scope: dict, receive: Callable, send: Callable) -> None:
        if not self._initialized:
            await self.startup()
            self._initialized = True

        try:
            request = Request(scope, receive)
            if scope['type'] == 'lifespan':
                await handle_lifespan_events(scope, receive, send, request, di_container, self.user_startup_callback)
            elif scope['type'] == 'http':
                await handle_http_requests(scope, receive, send, request, di_container)
            elif scope['type'] == 'websocket':
                await handle_websocket_connections(scope, receive, send, request, di_container)
        except Exception as e:
            print(f"Error in ASGI application: {e}")
            #print(traceback.format_exc())

            # Publish the error event without sending the response directly
            event_bus = await di_container.get('EventBus')
            event = Event(name="http.error.500", data={'exception': e, 'traceback': traceback.format_exc(), 'request': request, 'send': send})
            await event_bus.publish(event)

    async def startup(self):
        # Run the user-defined startup callback if provided
        if self.user_startup_callback:
            await self.user_startup_callback(di_container)
