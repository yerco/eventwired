# Step 07: Removing `ControllersService`

## Overview

In this step, we refactored our framework to remove the `ControllersService` and consolidate its responsibilities
into the `RoutingService`. This change simplifies the structure of the framework by reducing the number of service
layers and centralizing route registration and handling logic.

## Key Changes

- **Removed `ControllersService`**: The `ControllersService` was removed, and its role of registering routes
  and handling requests has been merged into the `RoutingService`.

- **Enhanced `RoutingService`**:
    - The `RoutingService` now directly handles the registration of routes and associates them with 
      the appropriate controllers (previously known as handlers).
    - It supports multiple HTTP methods (GET, POST, PUT, DELETE, etc.) for the same route.
    - The `start_routing` method now initializes the route registration process.

## Benefits

- **Simplified Architecture**: By consolidating the route management logic within the `RoutingService`, 
  the framework's architecture is streamlined, making it easier to understand and maintain.
- **Centralized Routing Logic**: All routing-related functionalities are now managed within a single service, 
  leading to more cohesive and maintainable code.

## Example

Previously, routes were registered in `ControllersService`. Now, the `RoutingService` handles this directly, 
reducing the complexity of managing multiple services:

```python
# Example of route registration in the new structure
from demo_app.controllers.hello_controller import hello_controller


def register_routes(routing_service):
    routing_service.add_route('/hello', 'GET', hello_controller)
```
