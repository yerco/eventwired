import asyncio
from typing import Callable, Any

from src.core.request import Request
from src.core.event_bus import Event
from src.core.context_manager import set_container


async def handle_websocket_connections(scope: dict, receive: Callable, send: Callable, request: Request,
                                       container: Any) -> None:
    set_container(container)
    event_bus = await container.get('EventBus')
    try:
        middleware_service = await container.get('MiddlewareService')

        # Prepare the event data for WebSocket connections
        event_data = {
            'scope': scope,
            'receive': receive,
            'send': send,
            'request': request,
        }
        event = Event(name='websocket.connection.received', data=event_data)

        # Define the final event handler for middleware execution
        async def final_event_handler(ev: Event):
            await event_bus.publish(ev)

        # Middleware execution with graceful error handling
        try:
            if middleware_service:
                await middleware_service.execute(event, final_event_handler)
            else:
                await event_bus.publish(event)  # Continue without middleware

        except Exception as e:
            # Handle middleware errors (you may log this in production)
            await event_bus.publish(Event(name="websocket.connection.closed", data=event.data))
            #await send({'type': 'websocket.close', 'code': 1011})  # Server error code
            return

        # Delegate message handling to the WebSocket controller
        await event_bus.publish(event)

    except ConnectionError:
        # Handle WebSocket disconnection without logging redundantly
        await event_bus.publish(Event(name="websocket.connection.closed", data={}))
        #await send({'type': 'websocket.close', 'code': 1000})  # Normal closure
    except asyncio.CancelledError:
        # Graceful handling of cancellation without logging too much
        pass
    except Exception as e:
        # Handle unexpected WebSocket errors
        # Get necessary services from the DI container
        await event_bus.publish(Event(name="websocket.connection.closed", data={}))
        # await send({'type': 'websocket.close', 'code': 1011})  # Server error

    finally:
        # Ensure WebSocket is closed properly with minimal logging
        try:
            await send({'type': 'websocket.close', 'code': 1000})  # Normal closure
        except Exception as close_error:
            if "websocket.close" not in str(close_error):
                # Only log the error if it's not a redundant close message
                print(f"Failed to close WebSocket gracefully: {close_error}")

        # Optionally publish the closure event
        closed_event = Event(name='websocket.connection.closed', data={})
        await event_bus.publish(closed_event)
