import asyncio

from src.controllers.base_controller import BaseController
from src.event_bus import Event

from demo_app.di_setup import di_container


async def websocket_controller(event: Event):
    # Resolve the WebSocketService from the DI container
    websocket_service = await di_container.get('WebSocketService')

    # Create the base controller
    controller = BaseController(event)

    try:
        # Accept the WebSocket connection (only once)
        await controller.accept_websocket()

        while True:
            # Receive WebSocket message with or without a timeout
            message = await controller.receive_websocket_message()

            if message is None or message.lower() in {"disconnect", "exit"}:
                # Log only when an intentional or explicit disconnect occurs
                if message:
                    print(f"Received {message}, closing WebSocket connection.")
                break
            elif message.lower() == "ping":
                await controller.send_websocket_message("pong")
            else:
                # Process other messages (assuming the WebSocketService adds "Processed: " itself)
                processed_message = await websocket_service.process_message(message)
                await controller.send_websocket_message(processed_message)

    except asyncio.CancelledError:
        # Suppress standard cancellation log during shutdown
        pass
    except RuntimeError as e:
        # Suppress RuntimeErrors related to already-closed connections during shutdown
        if "websocket.close" not in str(e):
            print(f"WebSocket RuntimeError during shutdown: {e}")
    except Exception as e:
        # Log only unexpected errors
        print(f"WebSocket error: {e}")
    finally:
        # Ensure graceful WebSocket closure
        try:
            await controller.send_websocket_message("Server is shutting down. Please reconnect later.")
            await controller.close_websocket()
        except asyncio.CancelledError:
            # Silently handle cancellation during shutdown
            pass
        except Exception as close_error:
            if "websocket.close" not in str(close_error):
                print(f"Error during WebSocket closure: {close_error}")

# Possible TODO: logging.info, logging.error
