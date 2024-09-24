import json
from datetime import datetime, timedelta
from typing import List, Tuple, Union


class Response:
    def __init__(self, content: Union[str, dict, bytes], status_code: int = 200,
                 headers: List[Tuple[bytes, bytes]] = None, content_type: str = 'text/plain'):
        self.content = content
        self.status_code = status_code
        self.headers = headers or []
        self.content_type = content_type
        self.body = b''

    def _encode_content(self):
        if isinstance(self.content, dict):
            self.content_type = 'application/json'
            self.body = json.dumps(self.content).encode()
        elif isinstance(self.content, str):
            self.body = self.content.encode()
        elif isinstance(self.content, bytes):
            self.body = self.content
        else:
            raise TypeError(f"Unsupported content type: {type(self.content).__name__}")

        # Ensure content-type header is properly set
        self._set_content_type_header()

    def _set_content_type_header(self):
        # Make sure the headers are stored as tuples
        self.headers = [(key, value) for key, value in self.headers if key != b'content-type']
        self.headers.append((b'content-type', self.content_type.encode()))

    async def send(self, send):
        self._encode_content()
        await send({
            'type': 'http.response.start',
            'status': self.status_code,
            'headers': self.headers  # Headers should now be tuples
        })
        await send({
            'type': 'http.response.body',
            'body': self.body
        })

    def set_cookie(self, name: str, value: str, path: str = '/', http_only: bool = True,
                   expires: Union[str, int, datetime, None] = None, secure: bool = True):
        cookie_value = f"{name}={value}; Path={path}"
        if http_only:
            cookie_value += "; HttpOnly"
        if secure:
            cookie_value += "; Secure"  # Ensure cookie is only sent over HTTPS
        if expires is not None:
            cookie_value += f"; Expires={expires}"  # Properly handle the expiration
        self.headers.append((b'set-cookie', cookie_value.encode()))  # Store as tuple

    @classmethod
    async def json(cls, send, data: dict, status_code: int = 200):
        response = cls(content=data, status_code=status_code, content_type='application/json')
        await response.send(send)

    @classmethod
    async def html(cls, send, html_content: str, status_code: int = 200):
        response = cls(content=html_content, status_code=status_code, content_type='text/html')
        await response.send(send)

    @classmethod
    async def plain_text(cls, send, text_content: str, status_code: int = 200):
        response = cls(content=text_content, status_code=status_code, content_type='text/plain')
        await response.send(send)
