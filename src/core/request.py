import json
from urllib.parse import parse_qs


class Request:
    def __init__(self, scope, receive):
        self.scope = scope
        self.receive = receive
        self._body = None
        self._json = None
        self._form = None
        self._query_params = None
        self._headers = None

    @property
    def method(self):
        connection_type = self.scope.get('type', 'http')  # Default to 'http' if 'type' is not provided
        if connection_type == 'websocket':
            return 'WEBSOCKET'
        return self.scope.get('method', 'GET').upper()

    @property
    def path(self):
        return self.scope.get('path', '/')

    @property
    def headers(self):
        if self._headers is None:
            self._headers = {k.decode(): v.decode() for k, v in self.scope['headers']}
        return self._headers

    @property
    def query_string(self):
        return self.scope.get('query_string', b'')

    @property
    def query_params(self):
        if self._query_params is None:
            self._query_params = parse_qs(self.scope['query_string'].decode())
        return self._query_params

    async def body(self):
        if self._body is None:
            self._body = b''
            more_body = True
            while more_body:
                message = await self.receive()
                self._body += message.get('body', b'')
                more_body = message.get('more_body', False)
        return self._body

    async def json(self):
        if self._json is None:
            body = await self.body()
            self._json = json.loads(body.decode())
        return self._json

    async def form(self):
        if self._form is None:
            body = await self.body()
            self._form = parse_qs(body.decode())
        return self._form

    @property
    def client(self):
        return self.scope.get('client')

    @property
    def scheme(self):
        return self.scope.get('scheme', 'http')

    @property
    def cookies(self):
        cookie_header = self.headers.get('cookie', '')
        return {item.split('=')[0]: item.split('=')[1] for item in cookie_header.split('; ') if '=' in item}
