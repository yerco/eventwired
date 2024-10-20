import datetime
from src.core.event_bus import Event

# Dictionary to store request start times (could also use a more robust storage if needed)
request_timing = {}


async def request_received(event: Event):
    request = event.data.get('request')
    request_id = id(request)  # Use request object ID as a unique identifier
    start_time = datetime.datetime.now()
    request_timing[request_id] = start_time
    print(f"[{start_time}] Timing Subscriber - Request received: {request.path}")


async def request_completed(event: Event):
    request_id = id(event.data.get('request'))
    start_time = request_timing.pop(request_id, None)  # Get and remove start time

    if start_time:
        end_time = datetime.datetime.now()
        elapsed_time = (end_time - start_time).total_seconds()
        request_path = event.data.get('request').path if event.data.get('request') else "Unknown path"
        print(
            f"[{end_time}] Timing Subscriber - Request completed for {request_path}. "
            f"Time taken: {elapsed_time} seconds."
        )
    else:
        print(
            "Timing Subscriber - Warning: Received 'http.request.completed' without corresponding"
            " 'http.request.received'."
        )
