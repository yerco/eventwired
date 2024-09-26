import signal
import uvicorn
import asyncio


class ServerManager:
    shutdown_event = None

    def __init__(self, server_type: str = 'uvicorn'):
        self.server_type = server_type.lower()
        self.server = None
        self.should_exit = asyncio.Event()

    async def run(self, app: str, host: str = '127.0.0.1', port: int = 8000, reload: bool = True, log_level: str = "info"):
        if self.server_type == 'uvicorn':
            await self.run_uvicorn(app, host, port, reload, log_level)
        else:
            raise ValueError(f"Unsupported server type: {self.server_type}")

    async def run_uvicorn(self, app: str, host: str, port: int, reload: bool, log_level: str):
        config = uvicorn.Config(app, host=host, port=port, reload=reload, log_level=log_level)
        self.server = uvicorn.Server(config)

        # Set up signal handlers
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, self.handle_exit)

        print(f"Starting Uvicorn with log level {log_level}")

        try:
            # Start the server in a separate task
            server_task = asyncio.create_task(self.server.serve())

            # Wait for either server completion or shutdown signal
            await asyncio.wait([server_task, self.should_exit.wait()], return_when=asyncio.FIRST_COMPLETED)

            if not server_task.done():
                self.server.should_exit = True
                await server_task

        except SystemExit as e:
            print(f"Server shutting down gracefully with exit code: {e.code}")
        except Exception as e:
            print(f"An unexpected error occurred during shutdown: {e}")

    def handle_exit(self):
        print(f"Received exit signal")
        self.should_exit.set()
