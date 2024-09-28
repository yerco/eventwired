import asyncio
from typing import Awaitable, Callable


class WebSocketService:
    def __init__(self):
        # Store connected clients (could be expanded to handle multiple client types, such as controllers, services, or bots).
        # 'self.clients' is used instead of 'self.controllers' to keep it generic, allowing flexibility in case the service needs
        # to manage non-controller clients, such as background services or external APIs, in the future.
        self.clients = []
        self.connection_accepted = False  # Track connection state

    def set_controller(self, controller):
        self.clients.append(controller)  # Add the connected client to the list

    async def start(self, controller):
        if not controller.connection_accepted:
            await controller.accept_websocket()
            controller.connection_accepted = True  # Mark the connection as accepted

    async def stop(self, controller):
        if controller.connection_accepted:
            await self._graceful_shutdown(controller)
            controller.connection_accepted = False  # Reset state per client

    async def listen(self, controller, on_message):
        try:
            while True:
                should_break = await self._listen(controller, on_message)
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
            await self.stop(controller)

    async def _listen(self, controller, on_message):
        message = await controller.receive_websocket_message()

        if message is None or message.lower() in {"disconnect", "exit"}:
            if message:
                print(f"Received {message}, closing WebSocket connection.")
            return True  # Signal to break the loop
        elif message.lower() == "ping":
            await controller.send_websocket_message("pong")
        else:
            await on_message(message)

    async def _graceful_shutdown(self, controller):
        try:
            await controller.send_websocket_message("Server is shutting down. Please reconnect later.")
            await controller.close_websocket()
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
        clients_to_remove = []
        for client in self.clients:
            if not client.connection_accepted:
                # Add client to the removal list if connection is closed
                clients_to_remove.append(client)
                continue
            try:
                await client.send_websocket_message(message)
            except Exception as e:
                print(f"Error broadcasting message to {client}: {e}")
                # Add client to the removal list if sending the message failed
                clients_to_remove.append(client)

        # Remove clients that are no longer active
        for client in clients_to_remove:
            if client in self.clients:
                self.clients.remove(client)

    async def broadcast_shutdown(self):
        for client in self.clients:
            try:
                # Check if the connection is already closed before sending the shutdown message
                if client.connection_accepted:
                    print(f"Notifying {client} about server shutdown.")
                    await client.send_websocket_message("Server is shutting down. Closing connection.")
                else:
                    print(f"Skipping client {client}: connection already closed.")
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
