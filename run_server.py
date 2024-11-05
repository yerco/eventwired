import argparse
import signal
from server_manager import ServerManager


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run ASGI server with WebSocket support.")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="The host to bind the server to (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="The port to bind the server to (default: 8000)")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload on code changes (default: False)")
    parser.add_argument("--reload_dir", type=str, nargs="*", default=["."], help="Directories to watch for file changes (default: current directory)")
    parser.add_argument("--log-level", type=str, default="info", choices=["critical", "error", "warning", "info", "debug", "trace"], help="Set the log level for the server (default: info)")
    parser.add_argument("--app", type=str, default="demo_app.app:app", help="The application to serve (default: demo_app.app:app)")

    args = parser.parse_args()
    manager = ServerManager()

    # Graceful shutdown handling
    def handle_exit(sig, frame):
        try:
            signal_name = signal.Signals(sig).name
            print(f"Received exit signal {signal_name}. Shutting down gracefully...")
        except ValueError:
            print(f"Received exit signal {sig}. Shutting down gracefully...")

        exit(0)

    # Bind signal handling for graceful shutdown
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)

    # Run the ASGI server with the specified options
    manager.run(
        app=args.app,
        host=args.host,
        port=args.port,
        reload=args.reload,
        reload_dirs=args.reload_dir,
        log_level=args.log_level
    )
