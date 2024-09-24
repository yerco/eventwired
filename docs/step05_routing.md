# Step 05: Routing and Controllers

## Overview

In this step, we introduced a routing mechanism to the framework, allowing incoming requests to be
routed to specific handlers (controllers). We achieved this by implementing a `RoutingService` and
a `ControllersService`. These services work together to handle HTTP requests, making the 
application more modular and organized.

## Key Additions

### 1. `RoutingService`

The `RoutingService` is responsible for managing routes and dispatching events to the appropriate
handler based on the request path and method.

**Key Features:**
- **Route Management**: Allows routes to be added, removed, and matched against incoming requests.
- **404 Handling**: Returns a 404 response if no matching route is found.

**Implementation:**

```python
class RoutingService:
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.routes: Dict[str, Dict[str, Callable]] = {}

    def add_route(self, path: str, method: str, handler: Callable):
        if path not in self.routes:
            self.routes[path] = {}
        self.routes[path][method] = handler

    def remove_route(self, path: str, method: str):
        if path in self.routes and method in self.routes[path]:
            del self.routes[path][method]
            if not self.routes[path]:  # Remove path if no methods remain
                del self.routes[path]

    async def route_event(self, event: Event):
        # Access the path and method from the scope within event.data
        scope = event.data.get('scope', {})
        path = scope.get('path')
        method = scope.get('method')

        if path in self.routes and method in self.routes[path]:
            handler = self.routes[path][method]
            await handler(event)
        else:
            await self.handle_404(event)

    async def handle_404(self, event: Event):
        send = event.data.get('send')
        if send:
            await send({
                'type': 'http.response.start',
                'status': 404,
                'headers': [
                    [b'content-type', b'text/plain'],
                ],
            })
            await send({
                'type': 'http.response.body',
                'body': b'Not Found',
            })

    def start_routing(self):
        self.event_bus.subscribe("http.request.received", self.route_event)
```

### 2. `ControllersService`

The `ControllersService` contains the actual request handlers (controllers). 
These handlers process the requests routed by the RoutingService and generate responses.

**Key Features:**
- **Handler Registration**: Registers routes with their corresponding handlers.
- **Response Handling**: Each handler is responsible for generating and sending the response.
  **Implementation:**

```python
class ControllersService:
    def __init__(self, routing_service: RoutingService):
        self.routing_service = routing_service
        self.register_routes()

    def register_routes(self):
        self.routing_service.add_route('/hello', 'GET', self.hello_handler)
        # Add more routes here

    async def hello_handler(self, event: Event):
        send = event.data['send']
        await send({
            'type': 'http.response.start',
            'status': 200,
            'headers': [
                [b'content-type', b'text/plain'],
            ],
        })
        await send({
            'type': 'http.response.body',
            'body': b'Hello from the routed handler!',
        })
```

### 3. Updated `app.py`

The main application file (app.py) was updated to initialize and start the routing system. 
It now publishes events to the event bus, which are then handled by the routing system.

**Key Features:**
- **Event Publishing**: The `app` function now publishes an event containing the request details, which the 
  `RoutingService` uses to route to the correct handler.
- **Routing Initialization**: The `RoutingService` and `ControllersService` are initialized and started
  when the application starts.
