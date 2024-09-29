from src.event_bus import Event
from src.controllers.http_controller import HTTPController

from demo_app.di_setup import di_container


async def logout_controller(event: Event):
    # Access the session from the event data
    session = event.data.get('session')

    # Initialize the controller for sending the response
    controller = HTTPController(event)

    publisher_service = await di_container.get('PublisherService')

    if session:
        session_service = await di_container.get('SessionService')
        # Delete the session from the database
        await session_service.delete_session(session.session_id)

        # Create the response and set the session_id cookie to expire (removing it from the client)
        response = await controller.create_html_response(html="You have been logged out.")
        response.set_cookie(
            'session_id', '', expires='Thu, 01 Jan 1970 00:00:00 GMT', path='/', http_only=True
        )

        # Emit user.logout.success event
        await publisher_service.publish_logout_success(session.get('user_id'))

        # Send the response
        await controller.send_response(response)
    else:
        # No session found, return a generic response
        await controller.send_text("No active session found.", status=400)

        # Emit user.logout.failure event
        await publisher_service.publish_logout_failure()
