import asyncio
from typing import Awaitable, Callable


class WebSocketService:
    def __init__(self):
        # Store connected clients (could be expanded to handle multiple clients)
        self.clients = []
        self.controller = None
        self.connection_accepted = False  # Track connection state

    def set_controller(self, controller):
        self.controller = controller

    async def start(self):
        # Ensure the controller has been set
        if not self.controller:
            raise ValueError("Controller must be set before starting the WebSocketService.")
        if not self.connection_accepted:
            await self.controller.accept_websocket()
            self.connection_accepted = True  # Mark the connection as accepted

    async def stop(self):
        if self.connection_accepted:
            await self._graceful_shutdown()
            self.connection_accepted = False  # Reset state on close

    async def listen(self, on_message):
        try:
            while True:
                should_break = await self._listen(on_message)
                if should_break:
                    break
        except asyncio.CancelledError:
            pass
        except RuntimeError as e:
            if "websocket.close" not in str(e):
                print(f"WebSocket RuntimeError during shutdown: {e}")
        except Exception as e:
            print(f"WebSocket error: {e}")
        finally:
            print("Finally block reached")
            await self.stop()

    async def _listen(self, on_message):
        message = await self.controller.receive_websocket_message()

        if message is None or message.lower() in {"disconnect", "exit"}:
            if message:
                print(f"Received {message}, closing WebSocket connection.")
            return True  # Signal to break the loop
        elif message.lower() == "ping":
            await self.controller.send_websocket_message("pong")
        else:
            await on_message(message)

    async def _graceful_shutdown(self):
        try:
            await self.controller.send_websocket_message("Server is shutting down. Please reconnect later.")
            await self.controller.close_websocket()
            self.connection_accepted = False  # Reset state after a successful close
        except asyncio.CancelledError:
            pass
        except Exception as close_error:
            if "websocket.close" not in str(close_error):
                print(f"Error during WebSocket closure: {close_error}")

    # Add a WebSocket client to the connected clients list
    def add_client(self, client_id: str):
        if client_id not in self.clients:
            self.clients.append(client_id)

    # Remove a WebSocket client from the connected clients list
    def remove_client(self, client_id: str):
        if client_id in self.clients:
            self.clients.remove(client_id)

    # Broadcast a message to all connected clients
    async def broadcast_message(self, message: str):
        # Placeholder logic for broadcasting (assuming we have client connections)
        for client in self.clients:
            await self.send_message(client, message)

    async def broadcast_shutdown(self):
        for client in self.clients:
            try:
                # Notify the client about the server shutdown
                print(f"Notifying {client} about server shutdown.")
                await self.send_message(client, "Server is shutting down. Closing connection.")
            except Exception as e:
                print(f"Error notifying client {client}: {e}")
        # Optionally, clear the clients list after shutdown
        self.clients.clear()

    # Receive WebSocket messages
    async def receive_message(self, receive: Callable) -> str:
        event = await receive()
        if event['type'] == 'websocket.receive':
            return event.get('text') or event.get('bytes')

    # Send WebSocket messages
    async def send_message(self, send: Callable, message: str):
        await send({
            'type': 'websocket.send',
            'text': message
        })
