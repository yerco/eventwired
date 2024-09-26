from src.controllers.base_controller import BaseController
from src.event_bus import Event

from demo_app.di_setup import di_container


async def websocket_test_controller(event: Event):
    template_service = await di_container.get('TemplateService')
    controller = BaseController(event)

    rendered_content = template_service.render_template('test_websocket.html', {})
    await controller.send_html(rendered_content)
