import uvicorn
import asyncio


class ServerManager:
    shutdown_event = None

    def __init__(self, server_type: str = 'uvicorn'):
        self.server_type = server_type.lower()
        self.server = None
        self.should_exit = asyncio.Event()

    def run(self, app: str, host: str = '127.0.0.1', port: int = 8000, reload: bool = True, reload_dirs=None, log_level: str = "info"):
        if self.server_type == 'uvicorn':
            if reload_dirs is None:
                reload_dirs = ["."]
            print(f"Reload is set to {reload}, watching directories: {reload_dirs}")
            uvicorn.run(
                app,
                host=host,
                port=port,
                reload=reload,
                reload_dirs=reload_dirs,
                log_level=log_level
            )
        else:
            raise ValueError(f"Unsupported server type: {self.server_type}")
