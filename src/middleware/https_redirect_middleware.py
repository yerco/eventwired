from src.event_bus import Event
from src.middleware.base_middleware import BaseMiddleware
from src.core.response import Response


class HTTPSRedirectMiddleware(BaseMiddleware):
    def __init__(self, permanent: bool = True):
        self.permanent = permanent

    async def before_request(self, event: Event) -> Event:
        request = event.data['request']

        # Check if the request is made over HTTP
        if request.scheme == 'http':
            host = request.headers.get('host')
            path = request.path
            query_string = request.query_string.decode('utf-8')

            # Construct the full URL for redirection
            full_path = path
            if query_string:
                full_path = f"{path}?{query_string}"

            redirect_url = f"https://{host}{full_path}"
            status_code = 301 if self.permanent else 302

            # Modify the response to redirect to HTTPS
            response = Response(
                content=f"Redirecting to {redirect_url}",
                status_code=status_code,
                headers=[(b'Location', redirect_url.encode())]
            )

            # Store the response in the event to prevent further processing
            event.data['response'] = response

        return event

    async def after_request(self, event: Event) -> Event:
        pass
