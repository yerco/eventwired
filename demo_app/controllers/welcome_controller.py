from src.controllers.base_controller import BaseController
from src.event_bus import Event

from demo_app.di_setup import di_container


async def welcome_controller(event: Event):
    controller = BaseController(event)
    template_service = await di_container.get('TemplateService')
    rendered_content = template_service.render_template('welcome.html', {})
    await controller.send_html(rendered_content)
