import json
from http.cookies import SimpleCookie
from typing import Dict, Optional
from urllib.parse import urlencode

from src.core.framework_app import FrameworkApp


# A custom response class to simulate ASGI response handling
class EWTestClientResponse:
    def __init__(self, status_code, headers: list, body: bytes):
        self.status_code = status_code
        self.headers = headers
        self._body = body

    # Return the body decoded as a string
    @property
    def body(self) -> str:
        return self._body.decode()

    # Decode JSON from response body if possible
    def json(self) -> Optional[Dict]:
        try:
            return json.loads(self.body)
        except json.JSONDecodeError:
            return None

    # Return the body as plain text
    @property
    def text(self) -> str:
        return self.body

    @property
    def cookies(self) -> Dict[str, str]:
        cookie_jar = SimpleCookie()
        for header, value in self.headers:
            if header.lower() == 'set-cookie':
                cookie_jar.load(value)
        return {key: morsel.value for key, morsel in cookie_jar.items()}


# A TestClient to simulate HTTP requests within EventWired
class EWTestClient:
    def __init__(self, app: FrameworkApp):
        self.app = app
        self.cookie_store = {}

    # Simulate an HTTP request to the ASGI app and capture the response
    async def _make_request(self, method: str, path: str, headers: Optional[Dict] = None, body: Optional[bytes] = None) -> EWTestClientResponse:
        headers = headers or {}
        # Include stored cookies in the 'Cookie' header
        if self.cookie_store:
            cookie_str = '; '.join([f'{key}={value}' for key, value in self.cookie_store.items()])
            headers['cookie'] = cookie_str

        scope = {
            "type": "http",
            "method": method.upper(),
            "path": path,
            "headers": [(k.encode("utf-8"), v.encode("utf-8")) for k, v in (headers or {}).items()],
            "query_string": b"",
        }

        response_body = b""
        status_code = None
        response_headers = []

        async def receive():
            return {"type": "http.request", "body": body or b""}

        async def send(message):
            nonlocal response_body, status_code, response_headers
            if message["type"] == "http.response.start":
                status_code = message["status"]
                response_headers.extend([(k.decode("utf-8"), v.decode("utf-8")) for k, v in message["headers"]])
            elif message["type"] == "http.response.body":
                response_body += message.get("body", b"")

        # Run the ASGI app with the simulated scope, send, and receive
        await self.app(scope, receive, send)

        # Create a response object
        response = EWTestClientResponse(status_code, response_headers, response_body)

        # Extract and store cookies from the response
        for header, value in response_headers:
            if header.lower() == 'set-cookie':
                cookie_jar = SimpleCookie(value)
                for key, morsel in cookie_jar.items():
                    self.cookie_store[key] = morsel.value

        return response

    # Simulate a GET request
    async def get(self, path: str, headers: Optional[Dict[str, str]] = None, cookies: Optional[Dict[str, str]] = None) -> EWTestClientResponse:
        headers = headers or {}
        if cookies:
            # Format cookies as 'key1=value1; key2=value2' and add them to the 'Cookie' header
            cookie_str = '; '.join([f'{key}={value}' for key, value in cookies.items()])
            headers['cookie'] = cookie_str

        return await self._make_request("GET", path, headers=headers)

    async def post(self, path: str, form_data: Optional[Dict[str, str]] = None, json_data: Optional[Dict] = None, headers: Optional[Dict[str, str]] = None) -> EWTestClientResponse:
        headers = headers or {}

        if json_data is not None:
            body = json.dumps(json_data).encode('utf-8')
            headers["Content-Type"] = "application/json"
        elif form_data is not None:
            body = urlencode(form_data).encode('utf-8')
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        else:
            body = b""

        return await self._make_request("POST", path, headers=headers, body=body)

    async def put(self, path: str, json_data: Optional[Dict] = None, headers: Optional[Dict[str, str]] = None) -> EWTestClientResponse:
        body = json.dumps(json_data).encode("utf-8") if json_data else b""
        headers = headers or {}
        headers["Content-Type"] = "application/json"
        return await self._make_request("PUT", path, headers=headers, body=body)

    async def delete(self, path: str, headers: Optional[Dict[str, str]] = None) -> EWTestClientResponse:
        return await self._make_request("DELETE", path, headers=headers)

    async def patch(self, path: str, json_data: Optional[Dict] = None, headers: Optional[Dict[str, str]] = None) -> EWTestClientResponse:
        body = json.dumps(json_data).encode("utf-8") if json_data else b""
        headers = headers or {}
        headers["Content-Type"] = "application/json"
        return await self._make_request("PATCH", path, headers=headers, body=body)

    async def options(self, path: str, headers: Optional[Dict[str, str]] = None) -> EWTestClientResponse:
        return await self._make_request("OPTIONS", path, headers=headers)
