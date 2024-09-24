from typing import Union

from src.event_bus import Event
from src.core.response import Response

from demo_app.di_setup import di_container


class BaseController:
    def __init__(self, event: Event):
        self.event = event
        self.send = event.data['send']

    # Create a Response object without sending it, for further modification (e.g., setting cookies)
    def create_response(self, content: Union[str, dict, bytes], status: int = 200, content_type: str = 'text/plain'):
        return Response(content=content, status_code=status, content_type=content_type)

    async def create_html_response(self, html: str = None, template: str = None, context: dict = None,
                             status: int = 200) -> Response:
        if template:
            template_service = await di_container.get('TemplateService')
            html = template_service.render_template(template, context or {})
        return self.create_response(html, status=status, content_type='text/html')

    def create_json_response(self, json_body: dict, status: int = 200) -> Response:
        return self.create_response(json_body, status=status, content_type='application/json')

    async def send_response(self, response: Response):
        # Store the response in the event so that it can be sent after middleware processing
        self.event.data['response'] = response
        return response  # Return the response for further middleware processing

    async def send_text(self, text: str, status: int = 200):
        response = self.create_response(text, status, content_type='text/plain')
        await self.send_response(response)

    async def send_html(self, html: str, status: int = 200):
        response = self.create_response(html, status, content_type='text/html')
        await self.send_response(response)

    async def send_json(self, json_body: dict, status: int = 200):
        response = self.create_response(json_body, status, content_type='application/json')
        await self.send_response(response)

    async def send_error(self, status: int, message: str = "Error"):
        response = self.create_response(message, status, content_type='text/plain')
        await self.send_response(response)

    # Placeholder for future protocols like WebSockets
    async def handle_websocket(self):
        pass
