from src.controllers.http_controller import HTTPController
from src.core.event_bus import Event

from demo_app.di_setup import di_container


async def cors_test_controller(event: Event):
    template_service = await di_container.get('TemplateService')
    controller = HTTPController(event, template_service=template_service)
    request = event.data['request']
    http_method = request.method
    if http_method == "OPTIONS":
        await controller.send_response(event.data['response'])
        return
    await controller.send_json({'some': 'data'})