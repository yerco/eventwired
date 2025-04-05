from src.controllers.http_controller import HTTPController
from src.core.event_bus import Event
from src.core.decorators import inject
from src.services.template_service import TemplateService

from demo_app.decorators.requires_admin import requires_admin


@requires_admin
@inject
async def admin_home_controller(event: Event, template_service: TemplateService):
    controller = HTTPController(event)
    rendered_content = template_service.render_template('admin/admin_home.html', {})
    await controller.send_html(rendered_content)
