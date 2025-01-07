from src.controllers.http_controller import HTTPController
from src.core.decorators import inject
from src.core.event_bus import Event
from src.services.template_service import TemplateService


@inject
async def render_chat_room_controller(event: Event, template_service: TemplateService):
    controller = HTTPController(event)
    rendered_content = template_service.render_template('chat_room.html', {})
    await controller.send_html(rendered_content)
