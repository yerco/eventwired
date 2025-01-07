from src.controllers.websocket_controller import WebSocketController
from src.core.decorators import inject
from src.core.event_bus import Event
from src.services.websocket_service import WebSocketService


@inject
async def chat_room_controller(event: Event, websocket_service: WebSocketService):
    # Create the base controller
    controller = WebSocketController(event)

    # Set the controller inside the WebSocketService
    websocket_service.register_client(controller)

    # Define the user logic for message processing
    async def on_message(message):
        # Filter out WebSocket connect/disconnect events from broadcasting
        if message not in {"websocket.connect", "websocket.disconnect"}:
            print(f"Received message: {message}")
            # Process and respond to the message
            broadcast_message = f"User: {message}"
            await websocket_service.broadcast_message(broadcast_message)

    # Start the WebSocket connection
    await websocket_service.accept_client_connection(controller)

    # Listen for messages and handle them with on_message
    await websocket_service.listen(controller, on_message)
