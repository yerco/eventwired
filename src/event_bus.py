import asyncio
import hashlib
import json

from datetime import datetime
from typing import Callable, Dict, List, Union, Awaitable, Any, Coroutine


class Event:
    def __init__(self, name: str, data: Dict = None):
        self.name = name
        self.data = data or {}
        self.timestamp = datetime.utcnow()
        self.handled = False

    def __hash__(self):
        # Convert the event's data to a JSON string and hash it with its name
        event_data_str = json.dumps(self.data, sort_keys=True)
        event_id_str = f"{self.name}:{self.timestamp.isoformat()}:{event_data_str}"
        return int(hashlib.sha256(event_id_str.encode('utf-8')).hexdigest(), 16)


class EventBus:
    def __init__(self):
        self.listeners: Dict[str, List[Union[Callable[[Event], None], Callable[[Event], Awaitable[None]]]]] = {}

    def subscribe(self, event_name: str, listener: Union[
        Callable[[Event], None], Callable[[Event], Awaitable[None]], Coroutine[Any, Any, None]]):
        if event_name not in self.listeners:
            self.listeners[event_name] = []
        self.listeners[event_name].append(listener)

    async def publish(self, event: Event):
        if event.name in self.listeners:
            for listener in self.listeners[event.name]:
                try:
                    if asyncio.iscoroutinefunction(listener):
                        await listener(event)  # Await the coroutine function
                    elif asyncio.iscoroutine(listener):
                        await listener  # Await if it's already a coroutine object
                    else:
                        listener(event)  # Synchronous function call
                except Exception as e:
                    # Log the exception or handle it appropriately
                    print(f"Error in listener for event '{event.name}': {e}")
