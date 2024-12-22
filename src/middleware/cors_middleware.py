import re

from src.middleware.base_middleware import BaseMiddleware
from src.core.response import Response
from src.services.config_service import ConfigService


class CORSMiddleware(BaseMiddleware):
    def __init__(self, config_service: ConfigService):
        self.allowed_origins = config_service.get('CORS_ALLOWED_ORIGINS', [])
        self.allowed_methods = config_service.get('CORS_ALLOWED_METHODS', ["GET", "POST", "PUT", "DELETE", "OPTIONS"])
        self.allowed_headers = config_service.get('CORS_ALLOWED_HEADERS', ["Content-Type", "Authorization"])
        self.allow_credentials = config_service.get('CORS_ALLOW_CREDENTIALS', False)
        # Compile regex patterns for origins with wildcards
        self.origin_patterns = self._generate_origin_patterns(self.allowed_origins)

    # Check if the request origin matches any allowed origin pattern
    def _is_origin_allowed(self, origin):
        for pattern in self.origin_patterns:
            if pattern.match(origin):
                print(f"DEBUG: Origin {origin} matched pattern {pattern.pattern}")
                return True
        print(f"DEBUG: Origin {origin} did not match any patterns")
        return False

    # Generate regex patterns for each origin in allowed_origins
    def _generate_origin_patterns(self, origins):
        return [self._convert_to_regex(origin) for origin in origins]

    # Convert wildcard patterns to regex patterns
    def _convert_to_regex(self, origin):
        if origin == "*":
            return re.compile(r".*")  # Match all origins
        elif "*" in origin:
            # Escape dots, replace * with .*, and anchor the pattern
            pattern = re.escape(origin).replace(r"\*", ".*")
            return re.compile(f"^{pattern}$")
        else:
            # Exact match, not a wildcard pattern
            return re.compile(f"^{re.escape(origin)}$")

    async def before_request(self, event):
        request = event.data['request']
        headers = request.headers
        origin = headers.get("origin") or headers.get("Origin")  # Check both lowercase and uppercase

        # Skip adding CORS headers if no 'Origin' header is present or method not allowed
        if origin is None or request.method not in self.allowed_methods:
            return event

        # Allow any origin if "*" is in allowed_origins
        if "*" in self.allowed_origins and request.method in self.allowed_methods:
            event.data['add_headers'] = self._cors_headers(origin="*")
        elif self._is_origin_allowed(origin) and request.method in self.allowed_methods:
            event.data['add_headers'] = self._cors_headers(origin=origin)

        # Handle preflight requests (OPTIONS)
        if request.method == "OPTIONS":
            response = self._build_preflight_response(origin=origin)
            event.data['response'] = response
            return event

        return event

    async def after_request(self, event):
        response = event.data.get('response')

        if response:
            # Convert headers to a dictionary to modify them
            headers_dict = {k if isinstance(k, bytes) else k.encode(): v if isinstance(v, bytes) else v.encode()
                            for k, v in response.headers}

            # Add CORS headers to the dictionary
            try:
                if 'add_headers' in event.data:
                    for header, value in event.data['add_headers'].items():
                        headers_dict[header.encode()] = value.encode()  # Consistently encode all as bytes

                # Reassign headers as a list of tuples
                # print("Final headers before response:", headers_dict)
                response.headers = list(headers_dict.items())  # Convert back to list of tuples for ASGI compatibility

            except Exception as e:
                print(f"Error adding CORS headers to response: {e}")
                print(f"headers_dict content: {headers_dict}")  # Debugging

        return event

    # Create a response for preflight (OPTIONS) requests.
    def _build_preflight_response(self, origin):
        # Initialize an empty response with a 204 No Content status code
        response = Response(content=b'', status_code=204)

        # Get the CORS headers
        headers = self._cors_headers(origin=origin)

        # Append headers to the response
        for header, value in headers.items():
            response.headers.append((header.encode(), value.encode()))

        return response

    # Return CORS headers based on allowed origins, methods, headers, and credentials
    def _cors_headers(self, origin=None):
        # Check if wildcard origin is allowed
        allow_any_origin = "*" in self.allowed_origins
        headers = {}

        # Set Access-Control-Allow-Origin to either * or the specific origin
        if allow_any_origin:
            headers["Access-Control-Allow-Origin"] = "*"
        elif self._is_origin_allowed(origin):
            headers["Access-Control-Allow-Origin"] = origin  # Only set the origin if allowed

        # Set other CORS headers
        headers["Access-Control-Allow-Methods"] = ", ".join(self.allowed_methods)
        headers["Access-Control-Allow-Headers"] = ", ".join(self.allowed_headers)
        headers["Referrer-Policy"] = "origin-when-cross-origin"  # Add a more permissive referrer policy

        if self.allow_credentials:
            headers["Access-Control-Allow-Credentials"] = "true"

        # Remove None values to avoid setting unnecessary headers
        headers = {k: v for k, v in headers.items() if v is not None}

        return headers
