from src.controllers.http_controller import HTTPController
from src.core.event_bus import Event
from src.core.decorators import inject

from demo_app.models.user import User
from src.services.orm_service import ORMService
from src.services.template_service import TemplateService


@inject
async def home_controller(event: Event, template_service: TemplateService, orm_service: ORMService):
    users = await orm_service.all(User)

    controller = HTTPController(event)

    context = {'title': 'Welcome', 'text': 'Hello from the template!', 'users': users}
    rendered_content = template_service.render_template('home.html', context)

    await controller.send_html(rendered_content, status=200)
