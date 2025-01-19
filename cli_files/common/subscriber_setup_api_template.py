from src.subscribers.error_subscribers import handle_404_event, handle_405_event, handle_500_event

from {app_name}.subscribers.api_subscribers import request_received, request_completed


async def register_subscribers(event_bus):
    event_bus.subscribe("http.request.received", request_received)
    event_bus.subscribe("http.request.completed", request_completed)

    # Implement your own event listeners (refer to documentation)
    event_bus.subscribe("http.error.404", handle_404_event)
    event_bus.subscribe("http.error.405", handle_405_event)
    event_bus.subscribe("http.error.500", handle_500_event)
    pass
