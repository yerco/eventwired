import pytest
from unittest.mock import AsyncMock
from src.core.request import Request


# Test for method and path properties
@pytest.mark.asyncio
async def test_request_method_and_path():
    scope = {
        'method': 'POST',
        'path': '/test',
        'headers': [],
        'query_string': b'',
    }
    request = Request(scope, AsyncMock())

    assert request.method == 'POST'
    assert request.path == '/test'


# Test for headers property
@pytest.mark.asyncio
async def test_request_headers():
    scope = {
        'method': 'GET',
        'path': '/',
        'headers': [(b'host', b'localhost'), (b'user-agent', b'test-agent')],
        'query_string': b'',
    }
    request = Request(scope, AsyncMock())

    assert request.headers == {'host': 'localhost', 'user-agent': 'test-agent'}


# Test for query_params property
@pytest.mark.asyncio
async def test_request_query_params():
    scope = {
        'method': 'GET',
        'path': '/',
        'headers': [],
        'query_string': b'name=john&age=30',
    }
    request = Request(scope, AsyncMock())

    assert request.query_params == {'name': ['john'], 'age': ['30']}


# Test for body() method
@pytest.mark.asyncio
async def test_request_body():
    scope = {
        'method': 'POST',
        'path': '/',
        'headers': [],
        'query_string': b'',
    }
    mock_receive = AsyncMock()
    mock_receive.side_effect = [
        {'body': b'{"key": "value"}', 'more_body': False},
    ]
    request = Request(scope, mock_receive)

    body = await request.body()
    assert body == b'{"key": "value"}'


# Test for json() method
@pytest.mark.asyncio
async def test_request_json():
    scope = {
        'method': 'POST',
        'path': '/',
        'headers': [],
        'query_string': b'',
    }
    mock_receive = AsyncMock()
    mock_receive.side_effect = [
        {'body': b'{"key": "value"}', 'more_body': False},
    ]
    request = Request(scope, mock_receive)

    json_data = await request.json()
    assert json_data == {"key": "value"}


# Test for form() method
@pytest.mark.asyncio
async def test_request_form():
    scope = {
        'method': 'POST',
        'path': '/',
        'headers': [],
        'query_string': b'',
    }
    mock_receive = AsyncMock()
    mock_receive.side_effect = [
        {'body': b'name=john&age=30', 'more_body': False},
    ]
    request = Request(scope, mock_receive)

    form_data = await request.form()
    assert form_data == {'name': ['john'], 'age': ['30']}


# Test for client property
@pytest.mark.asyncio
async def test_request_client():
    scope = {
        'method': 'GET',
        'path': '/',
        'headers': [],
        'query_string': b'',
        'client': ('127.0.0.1', 8000),
    }
    request = Request(scope, AsyncMock())

    assert request.client == ('127.0.0.1', 8000)


# Test for scheme property
@pytest.mark.asyncio
async def test_request_scheme():
    scope = {
        'method': 'GET',
        'path': '/',
        'headers': [],
        'query_string': b'',
        'scheme': 'https',
    }
    request = Request(scope, AsyncMock())

    assert request.scheme == 'https'


# Test for cookies property
@pytest.mark.asyncio
async def test_request_cookies():
    scope = {
        'method': 'GET',
        'path': '/',
        'headers': [(b'cookie', b'name=john; age=30')],
        'query_string': b'',
    }
    request = Request(scope, AsyncMock())

    assert request.cookies == {'name': 'john', 'age': '30'}
