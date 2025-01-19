from src.core.event_bus import Event


async def request_received(event: Event):
    request = event.data.get('request')
    print(f"Subscriber - Request received: {request.path}")


async def request_completed(event: Event):
    request_path = event.data.get('request').path if event.data.get('request') else "Unknown path"
    print(f"Request completed for {request_path}. ")

