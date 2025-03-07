import os
from aiofiles import open as aio_open

from src.core.event_bus import Event, EventBus


class StaticFilesHandler:
    def __init__(self, static_dir, static_url_path, event_bus: EventBus):
        self.static_dir = os.path.abspath(static_dir)
        self.static_url_path = static_url_path
        self.event_bus = event_bus

    async def handle(self, event: Event):
        request = event.data['request']
        send = event.data.get('send')

        if not request.path.startswith(self.static_url_path):
            return  # Not a static file request; let other handlers process it

        filename = request.path[len(self.static_url_path):].lstrip("/")
        file_path = os.path.join(self.static_dir, filename)

        # Check if file exists and is a valid file
        if not os.path.isfile(file_path):
            await send({
                'type': 'http.response.start',
                'status': 404,
                'headers': [[b'content-type', b'text/plain']],
            })
            await send({
                'type': 'http.response.body',
                'body': b'File not found.',
            })
            await self.emit_request_completed(event)
            event.data['response_already_sent'] = True
            return

        # Determine the content type based on file extension
        content_type = self._get_content_type(file_path)

        try:
            # Read the file content asynchronously
            async with aio_open(file_path, mode='rb') as f:
                content = await f.read()

            # Send the response using the 'send' callable from the ASGI scope
            await send({
                'type': 'http.response.start',
                'status': 200,
                'headers': [[b'content-type', content_type.encode()]],
            })
            await send({
                'type': 'http.response.body',
                'body': content,
            })
            await self.emit_request_completed(event)
            event.data['response_already_sent'] = True
        except Exception as e:
            # In case of an error, send a 500 response
            await send({
                'type': 'http.response.start',
                'status': 500,
                'headers': [[b'content-type', b'text/plain']],
            })
            await send({
                'type': 'http.response.body',
                'body': b'Internal server error.',
            })
            await self.emit_request_completed(event)
            event.data['response_already_sent'] = True

    def _get_content_type(self, file_path):
        if file_path.endswith('.css'):
            return 'text/css'
        elif file_path.endswith('.js'):
            return 'application/javascript'
        elif file_path.endswith('.png'):
            return 'image/png'
        elif file_path.endswith('.jpg') or file_path.endswith('.jpeg'):
            return 'image/jpeg'
        elif file_path.endswith('.svg'):
            return 'image/svg+xml'
        elif file_path.endswith('.html'):
            return 'text/html'
        else:
            return 'application/octet-stream'

    async def emit_request_completed(self, event: Event): # Access di_container from event
        completed_event = Event(name='http.request.completed', data=event.data)
        await self.event_bus.publish(completed_event)