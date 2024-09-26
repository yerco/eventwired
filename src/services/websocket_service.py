from typing import Awaitable, Callable


class WebSocketService:
    def __init__(self, message_processor: Callable[[str], Awaitable[str]] = None):
        # Store connected clients (could be expanded to handle multiple clients)
        self.clients = []
        self.message_processor = message_processor or self.default_process_message

    async def default_process_message(self, message: str) -> str:
        return f"Echo: {message}"

    async def process_message(self, message: str) -> str:
        # Now the message processor can be an async function
        return await self.message_processor(message)

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
            # In a real scenario, you'd send the message to each client here
            print(f"Broadcasting to {client}: {message}")

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
