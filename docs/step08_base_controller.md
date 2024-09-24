# Step 08: Introducing `BaseController`

## Overview

In this step, we introduced the `BaseController` class to simplify the process of defining controllers in the
framework. This class abstracts away the low-level details of constructing ASGI responses, allowing users to focus
on the core logic of their controllers.

## Key Features of `BaseController`

- **Simplified Response Handling**:
    - Provides utility methods like `send_text`, `send_json`, and `send_error` to easily send common types
      of responses without manually handling the ASGI protocol details.

- **Extensible for Future Protocols**:
    - The design of `BaseController` is extensible, making it easy to (eventually) support additional protocols 
      like WebSockets in the future.

## Example Usage

Previously, users had to manually construct and send responses:

```python
async def hello_controller(event: Event):
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
        'body': b'Hello from the demo app!',
    })
```
With `BaseController`, this is simplified:
```python
from src.controllers.base_controller import BaseController


async def hello_controller(event):
    controller = BaseController(event)
    await controller.send_text("Hello from the demo app!")
```
