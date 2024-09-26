import asyncio
from typing import Union

from src.event_bus import Event
from src.core.response import Response

from demo_app.di_setup import di_container


class BaseController:
    def __init__(self, event: Event):
        self.event = event
        self.send = event.data['send']
        self.receive = event.data.get('receive')  # Get the ASGI receive callable from the event data

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

    # WebSocket Methods
    async def accept_websocket(self):
        await self.send({
            'type': 'websocket.accept'
        })

    async def receive_websocket_message(self):
        event = await self.receive()

        if event['type'] == 'websocket.connect':
            print("WebSocket connected.")
            return event['type']
        elif event['type'] == 'websocket.receive':
            return event.get('text') or event.get('bytes')
        elif event['type'] == 'websocket.disconnect':
            return "disconnect"
        else:
            return None

    async def receive_websocket_message_with_timeout(controller, timeout=3):
        try:
            return await asyncio.wait_for(controller.receive_websocket_message(), timeout=timeout)
        except asyncio.TimeoutError:
            print("WebSocket message receive timed out.")
            return None

    async def send_websocket_message(self, message: str):
        # Ensure the message is properly formatted as a text WebSocket message
        await self.send({
            'type': 'websocket.send',
            'text': message
        })

    async def close_websocket(self, code: int = 1000):
        # Ensure proper closing of the WebSocket with the correct code
        await self.send({
            'type': 'websocket.close',
            'code': code
        })
