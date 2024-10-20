# Step 17: Middleware Service

In this step, we introduce the `MiddlewareService` into the framework, which handles the execution of middleware
during the request lifecycle. Middleware is essential for managing cross-cutting concerns such as logging, 
authentication, and request validation.

## Middleware Overview

Middleware is designed to process incoming requests and outgoing responses. The `MiddlewareService` executes 
registered middleware in a defined order:

1. **Before Request**: Middleware can modify or inspect the request before passing it to the main handler.
2. **After Request**: Middleware can modify or inspect the response after the handler processes the request.

Middleware provides a clean, centralized way to handle pre-processing and post-processing of requests without 
cluttering the main application logic.

## MiddlewareService Implementation

The `MiddlewareService` is a core service that manages middleware execution in the request lifecycle.

### Structure

```python
# src/services/middleware_service.py
from typing import Callable, List
from src.core.event_bus import Event


class MiddlewareService:
    def __init__(self):
        self.middlewares: List[Callable] = []

    def register_middleware(self, middleware: Callable) -> None:
        self.middlewares.append(middleware)

    async def execute(self, event: Event, handler: Callable) -> None:
        # Before Request: Pass the event through the middlewares
        for middleware in self.middlewares:
            if hasattr(middleware, 'before_request'):
                event = await middleware.before_request(event)

        # Execute the main handler
        await handler(event)

        # After Request: Pass the event through the middlewares in reverse order
        for middleware in reversed(self.middlewares):
            if hasattr(middleware, 'after_request'):
                await middleware.after_request(event)
```

### Key Methods

- `register_middleware(self, middleware)`: Registers a middleware in the service.
- `execute(self, event, handler)`: Executes the middleware chain before and after the main handler.

## Middleware Lifecycle

The MiddlewareService processes the middlewares in two phases:

1. Before Request: This phase allows middlewares to modify or analyze the incoming request (represented by the Event).
    Example: Logging the incoming request path.
2. After Request: This phase allows middlewares to modify or analyze the outgoing response before it is sent back.
    Example: Logging the response status or processing time.

## Middleware Example

Here’s an example of a combined middleware that logs before and after the request:

```python
# src/middleware/logging_middleware.py
from src.core.event_bus import Event


class LoggingMiddleware:
    async def before_request(self, event: Event) -> Event:
        request = event.data['request']
        print(f"Logging before request: {request.path}")
        return event

    async def after_request(self, event: Event) -> None:
        request = event.data['request']
        print(f"Logging after request: {request.path}")
```

### Middleware Registration

Middleware is registered through the di_container and MiddlewareService in demo_app/di_setup.py:

```python
# demo_app/di_setup.py
from src.middleware.logging_middleware import LoggingMiddleware
from src.services.middleware_service import MiddlewareService

middleware_service = MiddlewareService()
middleware_service.register_middleware(LoggingMiddleware())
di_container.register_singleton(middleware_service, 'MiddlewareService')
```

## Execution in HTTP Request Lifecycle

The middleware is executed during the handling of HTTP requests in handle_http_requests, ensuring that all 
registered middlewares are called both before and after the request processing.
