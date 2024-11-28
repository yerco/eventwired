import asyncio
import hashlib
import json

from datetime import datetime, timezone
from typing import Callable, Dict, List, Union, Awaitable, Any, Coroutine


class Event:
    def __init__(self, name: str, data: Dict = None):
        self.name = name
        self.data = data or {}
        self.timestamp = datetime.now(timezone.utc)

    def __hash__(self):
        # Convert the event's data to a JSON string and hash it with its name
        event_data_str = json.dumps(self.data, sort_keys=True)
        event_id_str = f"{self.name}:{self.timestamp.isoformat()}:{event_data_str}"
        return int(hashlib.sha256(event_id_str.encode('utf-8')).hexdigest(), 16)


Listener = Union[Callable[[Event], None], Callable[[Event], Awaitable[None]], Coroutine[Any, Any, None]]


class EventBus:
    def __init__(self):
        self.listeners: Dict[str, List[Listener]] = {}

    def subscribe(self, event_name: str, listener: Listener):
        if event_name not in self.listeners:
            self.listeners[event_name] = []
        self.listeners[event_name].append(listener)

    async def publish(self, event: Event):
        handled = False
        if event.name in self.listeners:
            for listener in self.listeners[event.name]:
                if event.data.get('response_already_sent', False):
                    break  # Stop processing further listeners
                try:
                    if asyncio.iscoroutinefunction(listener):
                        await listener(event)  # Await the coroutine function
                        handled = True
                    elif asyncio.iscoroutine(listener):
                        await listener  # Await if it's already a coroutine object
                        handled = True
                    else:
                        listener(event)  # Synchronous function call
                        handled = True
                except Exception as e:
                    if "websocket.close" in str(e):
                        # Gracefully handle WebSocket closure errors
                        print(f"WebSocket already closed for event '{event.name}': {e}")
                    else:
                        print(f"Error in listener for event '{event.name}': {e}")
        if not handled:
            await self.handle_unhandled_event(event)  # Call the fallback if not handled

    async def handle_unhandled_event(self, event):
        # Default behavior for unhandled events
        print(f"Event '{event.name}' was not handled. Triggering fallback.")
        if 'send' in event.data:
            if 'scope' in event.data and event.data['scope']['type'] == 'websocket':
                print("Cannot send HTTP response for WebSocket event")
                return  # Skip sending HTTP response for WebSocket events

            # Check if a response has already been sent
            if event.data.get('response_already_sent', False):
                print("Response already sent, skipping fallback response.")
                return

            # Mark the response as sent to prevent duplicate responses
            event.data['response_already_sent'] = True

            # Send the fallback HTTP response
            try:
                await event.data['send']({
                    'type': 'http.response.start',
                    'status': 500,
                    'headers': [[b'content-type', b'text/plain']],
                })
                await event.data['send']({
                    'type': 'http.response.body',
                    'body': b'Internal Server Error - Event not handled',
                })
            except Exception as e:
                print(f"Error sending fallback response: {e}")
