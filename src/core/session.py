import uuid


class Session:
    def __init__(self, session_id: str = None, data: dict = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.data = data or {}
        self._is_modified = False  # Track if session data has been modified

    def get(self, key: str, default=None):
        return self.data.get(key, default)

    def set(self, key: str, value: any):
        self.data[key] = value
        self._is_modified = True

    def delete(self, key: str):
        if key in self.data:
            del self.data[key]
            self._is_modified = True

    def is_modified(self) -> bool:
        return self._is_modified

    def clear(self):
        self.data.clear()
        self._is_modified = True
