import re
import os

from typing import Callable, Dict, Union, List, Optional

from src.core.static_handler import StaticFilesHandler
from src.core.event_bus import Event, EventBus
from src.services.config_service import ConfigService
from src.services.jwt_service import JWTService
from src.services.security.authentication_service import AuthenticationService


class RoutingService:
    def __init__(self, event_bus: EventBus, auth_service: AuthenticationService, jwt_service: Optional[JWTService], config_service: ConfigService = ConfigService()):
        self.event_bus = event_bus
        self.auth_service = auth_service
        self.jwt_service = jwt_service
        self.config_service = config_service
        self.routes: Dict[str, Dict[str, Callable]] = {}
        self.patterns = {
            r'<int:(\w+)>': r'(?P<\1>[0-9]+)',
            r'<str:(\w+)>': r'(?P<\1>[^/]+)',
            r'<(\w+)>': r'(?P<\1>[^/]+)',  # General pattern for other types
        }
        self.authenticated_routes: List[str] = []
        self.jwt_authenticated_routes: List[str] = []  # New list for JWT protected routes
        self.static_handler = StaticFilesHandler(static_dir="static", static_url_path="/static")

    async def initialize(self):
        static_dir = self.config_service.get('STATIC_DIR', 'static')
        static_url_path = self.config_service.get('STATIC_URL_PATH', '/static')
        self.setup_static_routes(static_dir, static_url_path)
        await self.start_routing()

    def add_route(self, path: str, methods: Union[str, List[str]], handler: Callable, requires_auth: bool = False, requires_jwt_auth: bool = False):
        # Convert the path to a regex pattern
        regex_path = self._convert_path_to_regex(path)

        if regex_path not in self.routes:
            self.routes[regex_path] = {}

        if isinstance(methods, str):
            methods = [methods.upper()]
        else:
            methods = [method.upper() for method in methods]

        for method in methods:
            self.routes[regex_path] = self.routes.get(regex_path, {})
            self.routes[regex_path][method] = handler

            # If session-based authentication is required, add the path to the authenticated routes list
            if requires_auth:
                self.authenticated_routes.append(regex_path)
            # If JWT authentication is required, add the path to the JWT authenticated routes list
            if requires_jwt_auth and self.jwt_service:
                self.jwt_authenticated_routes.append(regex_path)

    def setup_static_routes(self, static_dir: str, static_url_path: str = "/static"):
        # Convert static_dir to an absolute path
        static_dir_abs = os.path.abspath(static_dir)
        # Initialize StaticFilesHandler with the provided directory and URL path
        self.static_handler = StaticFilesHandler(static_dir=static_dir_abs, static_url_path=static_url_path)

        # Convert the static path to a regex
        static_regex = r'^/static/(?P<filename>.+)$'
        self.routes[static_regex] = {
            'GET': self.static_handler.handle
        }

    def _convert_path_to_regex(self, path: str) -> str:
        def replace(match):
            full_match = match.group(0)
            if full_match.startswith('<int:'):
                param_name = full_match[5:-1]
                return fr'(?P<{param_name}>[0-9]+)'
            elif full_match.startswith('<str:'):
                param_name = full_match[5:-1]
                return fr'(?P<{param_name}>[^/]+)'
            else:
                param_name = full_match[1:-1]
                return fr'(?P<{param_name}>[^/]+)'

        return f'^{re.sub(r"<[^>]+>", replace, path)}$'

    def remove_route(self, path: str, method: str):
        method = method.upper()
        regex_path = self._convert_path_to_regex(path)
        if regex_path in self.routes and method in self.routes[regex_path]:
            del self.routes[regex_path][method]
            if not self.routes[regex_path]:  # Remove path if no methods remain
                del self.routes[regex_path]

    async def route_event(self, event: Event):
        # Access the request object from the event
        request = event.data.get('request')
        if not request:
            await self.handle_404(event)
            return

        # Extract the path and method from the request
        path = request.path
        method = request.method

        # Check if the request is for static files first
        if path.startswith(self.static_handler.static_url_path):
            filename = path[len(self.static_handler.static_url_path):].lstrip("/")
            event.data['path_params'] = {'filename': filename}
            return await self.static_handler.handle(event)

        # Check for matching route
        for regex_path, methods in self.routes.items():
            match = re.match(regex_path, path)
            if match:
                if method in methods:
                    # Extract path parameters from the regex match and add to event.data['path_params']
                    event.data['path_params'] = match.groupdict()

                    # Check if session-based authentication is required
                    if regex_path in self.authenticated_routes:
                        # Check if user is logged in (i.e., session contains user_id)
                        session = event.data.get('session')
                        if not session or not session.get('user_id'):
                            return await self.auth_service.send_unauthorized(event)

                    # Check if JWT-based authentication is required
                    if regex_path in self.jwt_authenticated_routes:
                        auth_header = request.headers.get('authorization')
                        if not auth_header or not auth_header.startswith('Bearer '):
                            return await self.auth_service.send_unauthorized(event)

                        token = auth_header.split(" ")[1]
                        if self.jwt_service:
                            try:
                                payload = await self.jwt_service.validate_token(token)
                                event.data["user"] = payload
                            except ValueError:
                                return await self.auth_service.send_unauthorized(event)

                    # If authentication is not required or the user is logged in, proceed with the request
                    handler = methods[method]
                    return await handler(event)
                else:
                    print(f"Method {method} not allowed for {path}")
                    # Send 405 Method Not Allowed response
                    await self.send_405(event)
                    return  # Ensure no further processing happens

        await self.handle_404(event)

    async def send_405(self, event: Event):
        send = event.data.get('send')
        if send:
            await self.event_bus.publish(Event(name="http.error.405", data=event.data))

    async def handle_404(self, event: Event):
        send = event.data.get('send')
        if send:
            await self.event_bus.publish(Event(name="http.error.404", data=event.data))

    async def start_routing(self):
        self.event_bus.subscribe("http.request.received", self.route_event)
        self.event_bus.subscribe("websocket.connection.received", self.route_event)
