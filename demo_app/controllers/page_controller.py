from src.controllers.http_controller import HTTPController
from src.core.event_bus import Event


async def page_detail_controller(event: Event):
    controller = HTTPController(event)
    page_id = event.data['path_params']['id']  # Extracted path parameter
    await controller.send_text(f"Page ID: {page_id}")
