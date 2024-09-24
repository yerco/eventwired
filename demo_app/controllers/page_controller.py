from src.controllers.base_controller import BaseController
from src.event_bus import Event


async def page_detail_controller(event: Event):
    controller = BaseController(event)
    page_id = event.data['path_params']['id']  # Extracted path parameter
    await controller.send_text(f"Page ID: {page_id}")
