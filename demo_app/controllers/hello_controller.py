from src.controllers.http_controller import HTTPController
from src.core.event_bus import Event

from demo_app.di_setup import di_container
from demo_app.models.user import User


async def hello_controller(event: Event):
    # Access the ORMService and User model from the DI container
    orm_service = await di_container.get('ORMService')
    template_service = await di_container.get('TemplateService')

    # Fetch all users from the database
    users = await orm_service.all(User)

    # Extract usernames
    usernames = [user.username for user in users]

    # Initialize the controller for sending the response
    controller = HTTPController(event, template_service=template_service)

    # Define context to pass to the template
    context = {
        "title": "Hello from YASGI!",
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
