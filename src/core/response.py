import json
from datetime import datetime
from typing import List, Tuple, Union
from http.cookies import SimpleCookie


class Response:
    def __init__(self, content: Union[str, dict, bytes], status_code: int = 200,
                 headers: List[Tuple[bytes, bytes]] = None, content_type: str = 'text/plain'):
        self.content = content
        self.status_code = status_code
        self.headers = headers or []
        self.content_type = content_type
        self.body = b''  # Will be set after encoding content

    def _encode_content(self):
        if isinstance(self.content, dict):
            self.content_type = 'application/json'
            self.body = json.dumps(self.content).encode()
        elif isinstance(self.content, str):
            self.body = self.content.encode('utf-8')
        elif isinstance(self.content, bytes):
            self.body = self.content
        else:
            raise TypeError(f"Unsupported content type: {type(self.content).__name__}")

        # Ensure content-type header is properly set
        self._set_content_type_header()

    def _set_content_type_header(self):
        # Convert all headers to byte tuples
        self.headers = [(key.encode() if isinstance(key, str) else key,
                         value.encode() if isinstance(value, str) else value)
                        for key, value in self.headers if key != b'content-type']
        # Add the correct content-type header
        self.headers.append((b'content-type', self.content_type.encode()))

    async def send(self, send):
        self._encode_content()  # Ensure the body is encoded before sending
        await send({
            'type': 'http.response.start',
            'status': self.status_code,
            'headers': self.headers  # Ensure headers are properly formatted
        })
        await send({
            'type': 'http.response.body',
            'body': self.body
        })

    def set_cookie(self, name: str, value: str, path: str = '/', http_only: bool = True,
                   expires: Union[str, int, datetime, None] = None, secure: bool = True, same_site: str = 'Lax'):
        cookie_value = f"{name}={value}; Path={path}"
        if http_only:
            cookie_value += "; HttpOnly"
        if secure:
            cookie_value += "; Secure"
        if expires is not None:
            cookie_value += f"; Expires={expires}"
        if same_site:
            cookie_value += f"; SameSite={same_site}"
        self.headers.append((b'set-cookie', cookie_value.encode()))

    @property
    def cookies(self):
        # Parse the 'Set-Cookie' headers into a SimpleCookie object
        cookie = SimpleCookie()
        for header_name, header_value in self.headers:
            if header_name.lower() == 'set-cookie':
                cookie.load(header_value)
        # Return a dictionary of cookie names and their values
        return {key: morsel.value for key, morsel in cookie.items()}

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
