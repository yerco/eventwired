from typing import Callable
import traceback

from src.core.lifecycle import handle_lifespan_events
from src.core.http_handler import handle_http_requests
from src.core.websocket import handle_websocket_connections
from src.core.request import Request

from demo_app.di_setup import di_container
from demo_app.routes import register_routes


# User-defined startup callback
async def user_startup_callback(di_container):
    routing_service = await di_container.get('RoutingService')

    if routing_service is None:
        raise ValueError("RoutingService is not configured properly")

    # Custom route registration logic for the user app
    register_routes(routing_service)

    # Set up static file routes with the user-provided static directory
    routing_service.setup_static_routes(static_dir="demo_app/static", static_url_path="/static")


async def app(scope: dict, receive: Callable, send: Callable) -> None:
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
