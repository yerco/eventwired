from src.subscribers.error_subscribers import handle_404_event, handle_405_event, handle_500_event


async def register_subscribers(event_bus):
    # Implement your own event listeners (refer to documentation)
    event_bus.subscribe('http.error.404', handle_404_event)
    event_bus.subscribe('http.error.405', handle_405_event)
    event_bus.subscribe('http.error.500', handle_500_event)
    pass
