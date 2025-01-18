import os
from src.controllers.http_controller import HTTPController
from src.core.decorators import inject
from src.core.event_bus import Event
from src.services.config_service import ConfigService


@inject
async def favicon_controller(event: Event, config_service: ConfigService):
    favicon_path = os.path.join(config_service.get('TEMPLATE_DIR'), 'favicon.ico')
    http_controller = HTTPController(event)
    if not os.path.exists(favicon_path):
        await http_controller.send_error(404, "Favicon not found")
        return
    await http_controller.send_file(favicon_path, content_type='image/x-icon')
