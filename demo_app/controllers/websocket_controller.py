from src.controllers.base_controller import BaseController
from src.event_bus import Event

from demo_app.di_setup import di_container


async def websocket_controller(event: Event):
    # Resolve the WebSocketService from the DI container
    websocket_service = await di_container.get('WebSocketService')

    # Create the base controller
    controller = BaseController(event)

    # Set the controller inside the WebSocketService
    websocket_service.set_controller(controller)

    # Define the user logic for message processing
    async def on_message(message):
        # Process and respond to the message
        processed_message = f"Processed: {message}"
        await controller.send_websocket_message(processed_message)

    # Start the WebSocket connection
    await websocket_service.start()

    # Listen for messages and handle them with on_message
    await websocket_service.listen(on_message)
