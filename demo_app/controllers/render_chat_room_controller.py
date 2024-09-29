from src.controllers.http_controller import HTTPController
from src.event_bus import Event

from demo_app.di_setup import di_container


async def render_chat_room_controller(event: Event):
    template_service = await di_container.get('TemplateService')
    controller = HTTPController(event)

    rendered_content = template_service.render_template('chat_room.html', {})
    await controller.send_html(rendered_content)
