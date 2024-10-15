from typing import Callable
import traceback

from src.core.lifecycle import handle_lifespan_events
from src.core.http_handler import handle_http_requests
from src.core.request import Request
from src.core.websocket import handle_websocket_connections
from src.dicontainer import di_container
from src.event_bus import Event


async def framework_app(scope: dict, receive: Callable, send: Callable, user_startup_callback=None) -> None:
    try:
        request = Request(scope, receive)
        if scope['type'] == 'lifespan':
            await handle_lifespan_events(scope, receive, send, request, di_container, user_startup_callback)
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