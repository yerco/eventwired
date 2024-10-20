import datetime
from src.core.event_bus import Event


async def log_request_response(event: Event):
    request = event.data.get('request')
    response = event.data.get('response')

    # Assuming the request and response objects have some relevant details
    request_path = request.path if request else "Unknown path"
    status_code = response.status_code if response else "No status"

    # Log the completed request with response status and timestamp
    completion_time = datetime.datetime.now().isoformat()
    print(f"[{completion_time}] Completed request for {request_path}")
