# Step 22: WebSocket Connections

## Overview
In this step, we focused on the implementation and organization of WebSocket connections within our framework. 
The goal was to ensure consistency in naming, simplify the architecture, and align our WebSocket handling approach 
with our HTTP handling pattern.

### Key Components

#### `WebSocketHandler`
- **Purpose**: Manages the low-level WebSocket communication (send, receive, accept, close).
- **Role**: Acts as the core communication handler for WebSocket clients.
- **Rationale**: Provides a consistent interface for managing WebSocket communication across different clients.

#### `WebSocketController`
- **Purpose**: Thin wrapper around `WebSocketHandler` to maintain a consistent naming convention.
- **Role**: Used by users to interface with WebSocket events within their controllers.
- **Rationale for Naming "Controller"**:
    - We adopted the term "Controller" to align with similar concepts like `HTTPController`, making the user 
      experience more intuitive.
    - Although this is not a traditional controller in the MVC sense, it effectively abstracts and wraps 
      WebSocket-specific logic, offering simplicity akin to controllers in web frameworks.
    - The `WebSocketController` inherits from `WebSocketHandler`, ensuring that users can directly interface 
      with all WebSocket functionality while maintaining clarity in naming.

#### `HTTPController`
- **Purpose**: Handles HTTP requests and responses within the framework.
- **Role**: Represents the server-side logic for processing HTTP events.
- **Rationale**: Keeping the `HTTPController` aligned with the concept of a controller simplifies the framework's
   architecture and allows users to use consistent patterns across different communication protocols.

### Chat Room Example (`chat_room_controller`)
- The `chat_room_controller` is an example of how `WebSocketService` can be leveraged to manage WebSocket connections
  easily.
- **Key Flow**:
    1. A `WebSocketController` is created and registered with `WebSocketService`.
    2. The connection is accepted, and incoming messages are processed using a user-defined `on_message()` function.
    3. Messages are broadcasted to all connected clients.

### Summary
- **Naming Consistency**: We used "Controller" to keep the interface intuitive, similar to the `HTTPController`. This
  allows users to easily switch between different connection types (HTTP and WebSocket) without learning different
  conventions.
- **Wrapping `WebSocketHandler`**: `WebSocketController` wraps `WebSocketHandler` to offer a user-friendly interface 
  while retaining direct WebSocket functionalities.
- **Architecture Clarity**: Each connection type (HTTP or WebSocket) has a distinct handler (`HTTPController` 
  or `WebSocketController`), while the backbone handling communication (`WebSocketHandler`) remains consistent.

I'm trying to ensure a cleaner, consistent, and scalable architecture that balances simplicity for the end user
with effective underlying management.
