from src.event_bus import Event
from src.controllers.http_controller import HTTPController

from demo_app.di_setup import di_container


async def logout_controller(event: Event):
    # Access the session from the event data
    session = event.data.get('session')

    # Retrieve TemplateService from the DI container
    template_service = await di_container.get('TemplateService')

    # Initialize the controller for sending the response, providing the TemplateService
    controller = HTTPController(event, template_service=template_service)

    publisher_service = await di_container.get('PublisherService')

    if session:
        try:
            session_service = await di_container.get('SessionService')
            # Delete the session from the database
            await session_service.delete_session(session.session_id)

            # Emit user.logout.success event
            await publisher_service.publish_logout_success(session.get('user_id'))

            cookies = [
                ('session_id', '', {
                    'expires': 'Thu, 01 Jan 1970 00:00:00 GMT',
                    'path': '/',
                    'http_only': True
                })
            ]
            await controller.send_html(template='logout.html', cookies=cookies)

        except Exception as e:
            print(f"Error during logout: {e}")
            # Send a 500 Internal Server Error response in case of an exception
            await controller.send_error(500, "Internal Server Error")

    else:
        # No session found, send an appropriate response
        await controller.send_html(template='logout.html', context={"message": "No active session found"})

        # Emit user.logout.failure event
        await publisher_service.publish_logout_failure()
