# Step 09: Handling Routes with Parameters

## Overview

In this step, we extended the `RoutingService` to support dynamic routes with parameters. This allows developers
to define routes that include variable segments, such as user IDs or names, and extract these parameters for use
within their controllers.

## Key Changes

### 1. **Route Patterns with Parameters**
- We introduced the ability to define routes using parameterized patterns. For example:
    - `/users/<int:id>` will match paths like `/users/123` and extract the `id` as a parameter.
    - `/files/<str:filename>` will match paths like `/files/report.pdf` and extract the `filename` as a parameter.

### 2. **Regex-Based Matching**
- The `RoutingService` converts these parameterized routes into regular expressions that can match 
  incoming requests and extract the corresponding parameters.
- The parameters are defined using the following patterns:
    - `<int:name>`: Matches integers and extracts the value as `name`.
    - `<str:name>`: Matches any non-slash string and extracts it as `name`.
    - `<name>`: A general pattern that matches any non-slash string and extracts it as `name`.

### 3. **Parameter Extraction**
- When a route matches, the extracted parameters are made available in the `event.data['path_params']` dictionary,
  which controllers can access to use in their logic.

### Example

**Route Registration:**

```python
from demo_app.controllers.page_controller import page_detail_controller

def register_routes(routing_service):
    ...
    routing_service.add_route('/page/<int:id>', 'GET', page_detail_controller)
```

**Controller Accessing Parameters:**

```python
from src.controllers.base_controller import BaseController
from src.event_bus import Event

async def page_detail_controller(event: Event):
    controller = BaseController(event)
    page_id = event.data['path_params']['id']  # Extracted path parameter
    await controller.send_text(f"Page ID: {page_id}")
```
