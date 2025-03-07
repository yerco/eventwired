import os
from typing import Union, Optional, List, Tuple

from src.core.event_bus import Event
from src.core.response import Response
from src.services.template_service import TemplateService


class HTTPController:
    def __init__(self, event: Event, template_service: Optional[TemplateService] = None):
        self.event = event
        self.send = event.data['send']
        self.receive = event.data.get('receive')
        self.template_service = template_service

    def create_response(
            self, content: Union[str, dict, bytes], status: int = 200, content_type: str = 'text/plain',
            cookies: Optional[List[Tuple[str, str, dict]]] = None
    ) -> Response:
        response = Response(content=content, status_code=status, content_type=content_type)
        if cookies:
            for name, value, options in cookies:
                response.set_cookie(name, value, **options)
        return response

    async def create_html_response(
            self, html: Optional[str] = None, template: Optional[str] = None, context: Optional[dict] = None,
            status: int = 200, cookies: Optional[List[Tuple[str, str, dict]]] = None
    ) -> Response:
        if template and self.template_service:
            # Render the template if provided
            html = self.template_service.render_template(template, context or {})
        elif html is None:
            # If neither HTML nor template is provided, return a default message
            html = "No content available."

        return self.create_response(html, status=status, content_type='text/html', cookies=cookies)

    def create_json_response(self, json_body: dict, status: int = 200, cookies: Optional[List[Tuple[str, str, dict]]] = None) -> Response:
        return self.create_response(json_body, status=status, content_type='application/json', cookies=cookies)

    async def send_response(self, response: Response):
        # Store the response in the event so that it can be sent after middleware processing
        self.event.data['response'] = response
        return response  # Return the response for further middleware processing

    async def send_file(
            self, file_path: str, content_type: str = 'application/octet-stream',
            status: int = 200, cookies: Optional[List[Tuple[str, str, dict]]] = None
    ):
        if not os.path.exists(file_path):
            # Handle file not found
            await self.send_error(404, "File not found")
            return

        try:
            with open(file_path, 'rb') as f:
                content = f.read()
        except Exception as e:
            await self.send_error(500, f"Unable to read file: {str(e)}")
            return

        response = self.create_response(content, status=status, content_type=content_type, cookies=cookies)
        await self.send_response(response)
    async def send_text(self, text: str, status: int = 200, cookies: Optional[List[Tuple[str, str, dict]]] = None):
        response = self.create_response(text, status, content_type='text/plain', cookies=cookies)
        await self.send_response(response)

    async def send_html(
            self, html: Optional[str] = None, template: Optional[str] = None, context: Optional[dict] = None,
            status: int = 200, cookies: Optional[List[Tuple[str, str, dict]]] = None
    ):
        response = await self.create_html_response(html=html, template=template, context=context, status=status, cookies=cookies)
        await self.send_response(response)

    async def send_json(self, json_body: dict, status: int = 200, cookies: Optional[List[Tuple[str, str, dict]]] = None):
        response = self.create_json_response(json_body, status=status, cookies=cookies)
        await self.send_response(response)

    async def send_error(self, status: int, message: str = "Error", cookies: Optional[List[Tuple[str, str, dict]]] = None):
        response = self.create_response(message, status, content_type='text/plain', cookies=cookies)
        await self.send_response(response)
