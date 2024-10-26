import json
from typing import Dict, Optional
from src.core.framework_app import FrameworkApp


# A custom response class to simulate ASGI response handling
class EWTestClientResponse:
    def __init__(self, status_code, headers: dict, body: bytes):
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

    # Extract cookies from headers if any are set
    def cookies(self):
        return {k: v for k, v in self.headers.items() if k.lower() == "set-cookie"}


# A TestClient to simulate HTTP requests within EventWired
class EWTestClient:
    def __init__(self, app: FrameworkApp):
        self.app = app

    # Simulate an HTTP request to the ASGI app and capture the response
    async def _make_request(self, method: str, path: str, headers: Optional[Dict] = None, body: Optional[bytes] = None) -> EWTestClientResponse:
        scope = {
            "type": "http",
            "method": method.upper(),
            "path": path,
            "headers": [(k.encode("utf-8"), v.encode("utf-8")) for k, v in (headers or {}).items()],
            "query_string": b"",
        }

        response_body = b""
        status_code = None
        headers = {}

        async def receive():
            return {"type": "http.request", "body": body or b""}

        async def send(message):
            nonlocal response_body, status_code, headers
            if message["type"] == "http.response.start":
                status_code = message["status"]
                headers = {k.decode("utf-8"): v.decode("utf-8") for k, v in message["headers"]}
            elif message["type"] == "http.response.body":
                response_body += message.get("body", b"")
                print("checkpoint")

        # Run the ASGI app with the simulated scope, send, and receive
        await self.app(scope, receive, send)

        # Wrap the response details in TestClientResponse for ease of testing
        return EWTestClientResponse(status_code, headers, response_body)

    # Simulate a GET request
    async def get(self, path: str, headers: Optional[Dict[str, str]] = None) -> EWTestClientResponse:
        return await self._make_request("GET", path, headers=headers)

    # Simulate a POST request with JSON data
    async def post(self, path: str, json_data: Optional[Dict] = None, headers: Optional[Dict[str, str]] = None) -> EWTestClientResponse:
        body = json.dumps(json_data).encode("utf-8") if json_data else b""
        headers = headers or {}
        headers["Content-Type"] = "application/json"
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
