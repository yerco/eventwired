from typing import Callable
import traceback

# from src.core.error_handling import handle_error
from src.core.lifecycle import handle_lifespan_events
from src.core.http_handler import handle_http_requests
from src.core.request import Request
from src.core.websocket import handle_websocket_connections
from src.dicontainer import di_container


async def framework_app(scope: dict, receive: Callable, send: Callable, user_startup_callback=None) -> None:
    try:
        request = Request(scope, receive)
        if scope['type'] == 'lifespan':
            await handle_lifespan_events(scope, receive, send, request, di_container, user_startup_callback)
        elif scope['type'] == 'http':
            await handle_http_requests(scope, receive, send, request, di_container)
        elif scope['type'] == 'websocket':
            await handle_websocket_connections(scope, receive, send, request, di_container)
    except SystemExit as e:
        print(f"SystemExit triggered with code: {e.code}")
    except Exception as e:
        # Log error with traceback for better debug
        print(f"Error in ASGI application: {e}")
        print(traceback.format_exc())  # Log the traceback
        await send({
            "type": "http.response.start",
            "status": 500,
            "headers": [[b"content-type", b"text/plain"]],
        })
        await send({
            "type": "http.response.body",
            "body": b"Internal Server Error",
        })
        # await handle_error(500, event=None, di_container=di_container)
