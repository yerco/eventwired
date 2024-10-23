import argparse
import asyncio
from server_manager import ServerManager


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run ASGI server with WebSocket support.")

    # Add arguments for host, port, reload, and log level
    parser.add_argument("--host", type=str, default="127.0.0.1", help="The host to bind the server to (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="The port to bind the server to (default: 8000)")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload on code changes (default: False)")
    parser.add_argument("--log-level", type=str, default="info", choices=["critical", "error", "warning", "info", "debug", "trace"], help="Set the log level for the server (default: info)")
    parser.add_argument("--app", type=str, default="demo_app.app:app", help="The application to serve (default: demo_app.app:app)")

    args = parser.parse_args()

    manager = ServerManager()

    # Run the ASGI server with the specified options
    asyncio.run(manager.run(
        app=args.app,
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level
    ))
