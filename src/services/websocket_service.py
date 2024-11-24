import asyncio
from typing import List, Set, Callable, Awaitable

from src.services.websocket_handler import WebSocketHandler


# Manages multiple WebSocket client connections, providing shared services like broadcasting messages,
# starting/stopping connections, and managing the list of active clients.
class WebSocketService:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            print(f"Creating new instance of WebSocketService at {hex(id(cls))}")
            cls._instance = super().__new__(cls)
            cls._instance.clients = []
            cls._instance._lock = asyncio.Lock()
        return cls._instance

    def __init__(self):
        if not self._initialized:
            print(f"Initializing WebSocketService instance at {hex(id(self))}")
            # 'self.clients' is used instead of 'self.controllers' to keep it generic
            self.clients: List[WebSocketHandler] = []
            self._lock = asyncio.Lock()
            self._initialized = True
        else:
            print(f"WebSocketService instance at {hex(id(self))} already initialized")

    # Registers a new WebSocket client. Internally, creates a WebSocketHandler for managing client communication.
    def register_client(self, client: WebSocketHandler):
        self.clients.append(client)
        return client

    async def accept_client_connection(self, client: WebSocketHandler):
        if not client.connection_accepted:
            await client.accept_websocket()
            client.connection_accepted = True  # Mark the connection as accepted

    async def terminate_client_connection(self, client: WebSocketHandler):
        if client.connection_accepted:
            await self.graceful_shutdown(client)
            client.connection_accepted = False  # Reset state per client

    # Listens for incoming WebSocket messages from a client until a termination condition is met
    async def listen(self, client: WebSocketHandler, on_message: Callable[[str], Awaitable[None]]):
        try:
            while True:
                should_break = await self._listen(client, on_message)
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
            await self.terminate_client_connection(client)

    # Wrapped by listen
    async def _listen(self, client: WebSocketHandler, on_message: Callable[[str], Awaitable[None]]) -> bool:
        message = await client.receive_websocket_message()

        if message is None or message.lower() in {"disconnect", "exit"}:
            if message:
                print(f"Received {message}, closing WebSocket connection.")
            return True  # Signal to break the loop
        elif message.lower() == "ping":
            await client.send_websocket_message("pong")
        else:
            await on_message(message)
        return False

    async def graceful_shutdown(self, client: WebSocketHandler) -> None:
        try:
            await client.send_websocket_message("Server is shutting down. Please reconnect later.")
            await client.close_websocket()
        except asyncio.CancelledError:
            pass
        except Exception as close_error:
            if "websocket.close" not in str(close_error):
                print(f"Error during WebSocket closure: {close_error}")

    # Add a WebSocket client to the connected clients list
    def add_client(self, client: WebSocketHandler) -> None:
        if client not in self.clients:
            self.clients.append(client)

    # Remove a WebSocket client from the connected clients list
    def remove_client(self, client: WebSocketHandler) -> None:
        if client in self.clients:
            self.clients.remove(client)

    # Broadcast a message to all connected clients
    async def broadcast_message(self, message: str) -> None:
        clients_to_remove = []
        for client in self.clients:
            if not client.connection_accepted:
                print(f"Skipping client {client}: connection not accepted.")
                # Add client to the removal list if connection is closed
                clients_to_remove.append(client)
                continue
            try:
                await client.send_websocket_message(message)
            except Exception as e:
                print(f"Error broadcasting message to {client}: {e}")
                # Add client to the removal list if sending the message failed
                clients_to_remove.append(client)

        # Remove inactive clients
        await self._remove_inactive_clients(clients_to_remove)

    # Helper method to remove inactive clients from the list
    async def _remove_inactive_clients(self, clients_to_remove: List[WebSocketHandler]) -> None:
        async with self._lock:
            for client in clients_to_remove:
                if client in self.clients:
                    self.clients.remove(client)

    async def broadcast_shutdown(self) -> None:
        clients_to_remove = []

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

            # Mark the client for removal regardless of whether the notification was successful
            clients_to_remove.append(client)

        # Remove inactive clients and clear the list after shutdown
        await self._remove_inactive_clients(clients_to_remove)
