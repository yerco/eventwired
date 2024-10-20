from src.core.event_bus import Event
from src.middleware.base_middleware import BaseMiddleware
import datetime


class TimingMiddleware(BaseMiddleware):
    async def before_request(self, event: Event) -> Event:
        # Add data to the event before the request is processed
        event.data['before_request_data'] = datetime.datetime.now().isoformat()
        # print(f"Before request middleware: {event.data['before_request_data']}")
        return event

    async def after_request(self, event: Event) -> None:
        # Add a timestamp to the event after the request has been processed
        event.data['after_request_timestamp'] = datetime.datetime.now().isoformat()
        # print(f"After request middleware: {event.data['after_request_timestamp']}")
        # Calculate the time difference
        before_time = datetime.datetime.fromisoformat(event.data['before_request_data'])
        after_time = datetime.datetime.fromisoformat(event.data['after_request_timestamp'])
        processing_time = (after_time - before_time).total_seconds()
        print(f"Request processing time: {processing_time} seconds")
