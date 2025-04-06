from src.core.decorators import inject
from src.controllers.http_controller import HTTPController
from src.core.event_bus import Event
from src.services.orm_service import ORMService
from src.services.template_service import TemplateService

from demo_app.decorators.requires_admin import requires_admin
from demo_app.models.user import User


@requires_admin
@inject
async def admin_users_controller(event: Event, orm_service: ORMService, template_service: TemplateService):
    controller = HTTPController(event)
    users = await orm_service.all(User)
    rendered_content = template_service.render_template('admin/admin_users.html', {'users': users})
    await controller.send_html(rendered_content)
