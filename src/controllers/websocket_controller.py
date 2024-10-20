from src.core.event_bus import Event
from src.services.websocket_handler import WebSocketHandler


# Provides a high-level interface for developers to implement WebSocket business logic, acting as a wrapper around WebSocketHandler.
# The term "Controller" is used to align with the convention from MVC-like architectures, indicating that this class is intended for managing the flow of data and user interactions.
class WebSocketController(WebSocketHandler):
    def __init__(self, event: Event):
        # Initialize with WebSocket client communication
        super().__init__(event.data['send'], event.data.get('receive'))
        self.event = event
