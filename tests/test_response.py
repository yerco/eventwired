import pytest
from unittest.mock import AsyncMock
from src.core.response import Response


# Test for content encoding (string)
@pytest.mark.asyncio
async def test_response_string_content():
    mock_send = AsyncMock()
    response = Response(content="Hello, World!", status_code=200, content_type="text/plain")

    await response.send(mock_send)

    # Assert that the content was encoded correctly
    assert response.body == b"Hello, World!"

    # Assert that the headers include the correct content-type
    assert (b'content-type', b'text/plain') in response.headers

    # Assert that the send method was called with the correct data
    mock_send.assert_any_call({
        'type': 'http.response.start',
        'status': 200,
        'headers': [(b'content-type', b'text/plain')]
    })
    mock_send.assert_any_call({
        'type': 'http.response.body',
        'body': b"Hello, World!"
    })


# Test for content encoding (json)
@pytest.mark.asyncio
async def test_response_json_content():
    mock_send = AsyncMock()
    response = Response(content={"key": "value"}, status_code=200)

    await response.send(mock_send)

    # Assert that the content was encoded correctly as JSON
    assert response.body == b'{"key": "value"}'

    # Assert that the headers include the correct content-type for JSON
    assert (b'content-type', b'application/json') in response.headers

    # Assert that the send method was called with the correct data
    mock_send.assert_any_call({
        'type': 'http.response.start',
        'status': 200,
        'headers': [(b'content-type', b'application/json')]
    })
    mock_send.assert_any_call({
        'type': 'http.response.body',
        'body': b'{"key": "value"}'
    })


# Test for content encoding (bytes)
@pytest.mark.asyncio
async def test_response_bytes_content():
    mock_send = AsyncMock()
    response = Response(content=b"Binary data", status_code=200)

    await response.send(mock_send)

    # Assert that the content was encoded correctly as bytes
    assert response.body == b"Binary data"

    # Assert that the headers include the correct content-type
    assert (b'content-type', b'text/plain') in response.headers

    # Assert that the send method was called with the correct data
    mock_send.assert_any_call({
        'type': 'http.response.start',
        'status': 200,
        'headers': [(b'content-type', b'text/plain')]
    })
    mock_send.assert_any_call({
        'type': 'http.response.body',
        'body': b"Binary data"
    })


# Test for setting cookies
@pytest.mark.asyncio
async def test_response_set_cookie():
    response = Response(content="Cookie test", status_code=200)
    response.set_cookie(name="sessionid", value="abc123")

    # Assert that the set-cookie header was added
    assert (b'set-cookie', b'sessionid=abc123; Path=/; HttpOnly; Secure') in response.headers


# Test for json response class method
@pytest.mark.asyncio
async def test_response_json_class_method():
    mock_send = AsyncMock()
    await Response.json(mock_send, data={"key": "value"}, status_code=200)

    # Assert that the send method was called with the correct data
    mock_send.assert_any_call({
        'type': 'http.response.start',
        'status': 200,
        'headers': [(b'content-type', b'application/json')]
    })
    mock_send.assert_any_call({
        'type': 'http.response.body',
        'body': b'{"key": "value"}'
    })


# Test for html response class method
@pytest.mark.asyncio
async def test_response_html_class_method():
    mock_send = AsyncMock()
    await Response.html(mock_send, html_content="<html>Hello</html>", status_code=200)

    # Assert that the send method was called with the correct data
    mock_send.assert_any_call({
        'type': 'http.response.start',
        'status': 200,
        'headers': [(b'content-type', b'text/html')]
    })
    mock_send.assert_any_call({
        'type': 'http.response.body',
        'body': b'<html>Hello</html>'
    })


# Test for plain_text response class method
@pytest.mark.asyncio
async def test_response_plain_text_class_method():
    mock_send = AsyncMock()
    await Response.plain_text(mock_send, text_content="Hello, World!", status_code=200)

    # Assert that the send method was called with the correct data
    mock_send.assert_any_call({
        'type': 'http.response.start',
        'status': 200,
        'headers': [(b'content-type', b'text/plain')]
    })
    mock_send.assert_any_call({
        'type': 'http.response.body',
        'body': b"Hello, World!"
    })
