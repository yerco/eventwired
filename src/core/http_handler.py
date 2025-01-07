import traceback
from typing import Any, Callable

from src.core.event_bus import Event
from src.core.request import Request
from src.core.context_manager import set_container


async def handle_http_requests(scope: dict, receive: Callable[[], Any], send: Callable[[dict], None], request: Request,
                               container: Any) -> None:
    try:
        set_container(container)
        event_bus = await container.get('EventBus')
        middleware_service = await container.get('MiddlewareService')
        event_data = {
            'scope': scope,
            'receive': receive,
            'send': send,
            'request': request,
        }
        event = Event(name='http.request.received', data=event_data)

        # Define a handler to pass the event to the event bus for publishing after middleware execution
        async def final_handler(ev: Event):
            await event_bus.publish(ev)

        # Execute middleware chain before publishing the event
        await middleware_service.execute(event, final_handler)

        # Check if a response has already been sent
        if not event.data.get('response_already_sent'):
            # Emit 'http.request.completed' after all processing
            completed_event = Event(name='http.request.completed', data=event_data)
            await event_bus.publish(completed_event)
    except Exception as e:
        print(f"Error during request handling: {e}")
        event_bus = await container.get('EventBus')
        event = Event(name="http.error.500", data={'exception': e, 'traceback': traceback.format_exc(), 'request': request, 'send': send})
        await event_bus.publish(event)
