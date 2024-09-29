from src.controllers.http_controller import HTTPController
from src.event_bus import Event

from demo_app.di_setup import di_container
from demo_app.models.user import User


async def hello_controller(event: Event):
    # Access the ORMService and User model from the DI container
    orm_service = await di_container.get('ORMService')

    # Fetch all users from the database
    users = await orm_service.all(User)

    # Extract usernames
    usernames = [user.username for user in users]

    # Prepare response message
    response_message = f"Hello from the demo app! Users: {', '.join(usernames)}"

    # Send the usernames in the response
    controller = HTTPController(event)
    await controller.send_text(response_message)
