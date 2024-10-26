import pytest
from src.test_utils.test_client import EWTestClient, EWTestClientResponse
from src.core.framework_app import FrameworkApp
from typing import Callable


# Define a simple mock ASGI app
class MockASGIApp:
    async def __call__(self, scope: dict, receive: Callable, send: Callable):
        method = scope["method"]
        path = scope["path"]

        if path == "/" and method == "GET":
            await send({
                "type": "http.response.start",
                "status": 200,
                "headers": [(b"content-type", b"text/plain")]
            })
            await send({"type": "http.response.body", "body": b"Hello, World!"})

        elif path == "/json" and method == "POST":
            await send({
                "type": "http.response.start",
                "status": 201,
                "headers": [(b"content-type", b"application/json")]
            })
            await send({"type": "http.response.body", "body": b'{"message": "Data received"}'})

        elif path == "/not-found":
            await send({
                "type": "http.response.start",
                "status": 404,
                "headers": [(b"content-type", b"text/plain")]
            })
            await send({"type": "http.response.body", "body": b"Not Found"})

        else:
            await send({
                "type": "http.response.start",
                "status": 405,
                "headers": [(b"content-type", b"text/plain")]
            })
            await send({"type": "http.response.body", "body": b"Method Not Allowed"})


# Test suite for EWTestClient
@pytest.mark.asyncio
class TestEWTestClient:
    @pytest.fixture
    def test_client(self):
        app = MockASGIApp()
        return EWTestClient(app)

    async def test_get_request(self, test_client: EWTestClient):
        response = await test_client.get("/")
        assert response.status_code == 200
        assert response.text == "Hello, World!"
        assert response.headers["content-type"] == "text/plain"

    async def test_post_json_request(self, test_client: EWTestClient):
        response = await test_client.post("/json", json_data={"name": "test"})
        assert response.status_code == 201
        assert response.json() == {"message": "Data received"}
        assert response.headers["content-type"] == "application/json"

    async def test_not_found(self, test_client: EWTestClient):
        response = await test_client.get("/not-found")
        assert response.status_code == 404
        assert response.text == "Not Found"

    async def test_method_not_allowed(self, test_client: EWTestClient):
        response = await test_client.put("/")
        assert response.status_code == 405
        assert response.text == "Method Not Allowed"

    async def test_delete_request(self, test_client: EWTestClient):
        response = await test_client.delete("/json")
        assert response.status_code == 405
        assert response.text == "Method Not Allowed"
