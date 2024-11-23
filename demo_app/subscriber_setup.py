# Fallbacks
from src.subscribers.error_subscribers import handle_404_event, handle_405_event, handle_500_event

from demo_app.subscribers.logging_subscriber import log_request_response
from demo_app.subscribers.timing_subscriber import request_received, request_completed
from demo_app.subscribers.event_log_subscriber import log_event_to_db
# Overridden fallbacks
from demo_app.subscribers.error_subscribers import handle_403_event, handle_404_event, handle_405_event, handle_500_event, handle_no_csrf_event


async def register_subscribers(event_bus):

    event_bus.subscribe("http.request.completed", log_request_response)

    event_bus.subscribe('http.request.received', request_received)
    event_bus.subscribe('http.request.completed', request_completed)

    event_bus.subscribe("user.logout.success", log_event_to_db)
    event_bus.subscribe("user.logout.failure", log_event_to_db)
    event_bus.subscribe("user.login.success", log_event_to_db)
    event_bus.subscribe("user.login.failure", log_event_to_db)

    event_bus.subscribe('http.error.403', handle_403_event)
    event_bus.subscribe('http.error.404', handle_404_event)
    event_bus.subscribe('http.error.405', handle_405_event)
    event_bus.subscribe('http.error.500', handle_500_event)

    event_bus.subscribe('http.error.no_csrf', handle_no_csrf_event)
