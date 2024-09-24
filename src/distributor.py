from datetime import datetime
from typing import List, Callable

from src.services.config_service import ConfigService

config = ConfigService()


class Distributor:
    def __init__(self, services: List[Callable]):
        self.services = services
        self.current_index = 0
        self.handled_events = {}
        self.event_lifetime = config.get("PRUNE_INTERVAL")

    async def distribute(self, event) -> bool:
        self.prune_old_events()  # Prune old events

        event_id = hash(event)  # Define a way to uniquely identify events
        if event_id in self.handled_events and self.handled_events[event_id]:
            return True  # Event already handled

        for _ in range(len(self.services)):
            service = self.services[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.services)

            event.handled = await service(event)
            if event.handled:
                self.handled_events[event_id] = event
                break  # Early exit as soon as a service handles the event

        return event.handled

    def prune_old_events(self):
        now = datetime.utcnow()
        keys_to_delete = []

        for event_id, event in self.handled_events.items():
            if event and now - event.timestamp > self.event_lifetime:
                keys_to_delete.append(event_id)

        for event_id in keys_to_delete:
            del self.handled_events[event_id]
