from src.controllers.http_controller import HTTPController
from src.event_bus import Event

from demo_app.di_setup import di_container


async def welcome_controller(event: Event):
    controller = HTTPController(event)
    template_service = await di_container.get('TemplateService')
    rendered_content = template_service.render_template('welcome.html', {})
    await controller.send_html(rendered_content)
