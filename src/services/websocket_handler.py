import asyncio
from typing import Callable


# Server-side handler for managing WebSocket communication.
# Represents a single WebSocket client connection (e.g., a browser).
# Handles low-level operations for a single WebSocket client, including sending and receiving messages.
class WebSocketHandler:
    def __init__(self, send, receive):
        self.send = send
        self.receive = receive
        self.connection_accepted = False

    async def accept_websocket(self):
        await self.send({
            'type': 'websocket.accept'
        })
        self.connection_accepted = True

    async def receive_websocket_message(self):
        event = await self.receive()

        if event['type'] == 'websocket.connect':
            print("WebSocket connected.")
            return event['type']
        elif event['type'] == 'websocket.receive':
            return event.get('text') or event.get('bytes')
        elif event['type'] == 'websocket.disconnect':
            return "disconnect"
        else:
            return None

    async def receive_websocket_message_with_timeout(controller, timeout=3):
        try:
            return await asyncio.wait_for(controller.receive_websocket_message(), timeout=timeout)
        except asyncio.TimeoutError:
            print("WebSocket message receive timed out.")
            return None

    async def send_websocket_message(self, message: str):
        # Ensure the message is properly formatted as a text WebSocket message
        await self.send({
            'type': 'websocket.send',
            'text': message
        })

    async def close_websocket(self, code: int = 1000):
        # Ensure proper closing of the WebSocket with the correct code
        await self.send({
            'type': 'websocket.close',
            'code': code
        })

    async def receive_message(self, receive: Callable) -> str:
        event = await receive()
        if event['type'] == 'websocket.receive':
            return event.get('text') or event.get('bytes')

    async def send_message(self, send: Callable, message: str):
        await send({
            'type': 'websocket.send',
            'text': message
        })
