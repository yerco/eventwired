from src.controllers.http_controller import HTTPController
from src.core.event_bus import Event
from src.core.decorators import inject
from src.services.orm_service import ORMService
from src.services.template_service import TemplateService

from demo_app.models.user import User


@inject
async def hello_controller(event: Event, orm_service: ORMService, template_service: TemplateService):
    # Fetch all users from the database
    users = await orm_service.all(User)

    # Extract usernames
    usernames = [user.username for user in users]

    # Initialize the controller for sending the response
    controller = HTTPController(event, template_service=template_service)

    # Define context to pass to the template
    context = {
        "title": "Hello from Eventwired!",
        "greeting": "Welcome to the Hello Page!",
        "description": "This is a demonstration of our simple ASGI framework, showcasing the hello endpoint.",
        "features": [
            "Fast ASGI framework",
            "Supports both WebSockets and HTTP",
            "Modular design",
            "Built with educational purposes in mind"
        ],
        "users": usernames,
    }

    # Render the 'hello.html' template with the context
    await controller.send_html(template='hello.html', context=context)
