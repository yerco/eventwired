from src.controllers.http_controller import HTTPController
from src.core.event_bus import Event
from src.core.decorators import inject
from src.services.template_service import TemplateService


@inject
async def home_controller(event: Event, template_service: TemplateService):
    http_controller = HTTPController(event)
    rendered_content = template_service.render_template('home.html', {})
    await http_controller.send_html(rendered_content)
