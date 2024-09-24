from typing import Callable

from src.core.lifecycle import handle_lifespan_events
from src.core.http_handler import handle_http_requests
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


async def app(scope: dict, receive: Callable, send: Callable) -> None:
    request = Request(scope, receive)

    # Main ASGI application function
    if scope['type'] == 'lifespan':
        await handle_lifespan_events(scope, receive, send, request, di_container, user_startup_callback)
    elif scope['type'] == 'http':
        await handle_http_requests(scope, receive, send, request, di_container)
