# Session Handling

## Overview
The session lifecycle, from creation to deletion (logout), is explained, along with the request processing flow.

## Request Flow

1. **Incoming Request**:
    - Every request starts by publishing the event `http.request.received`.
    - The `MiddlewareService` passes the request through all registered middlewares.

2. **Before Request (SessionMiddleware)**:
    - The `SessionMiddleware` extracts the `session_id` from the request cookies.
    - If the `session_id` exists, session data is loaded from the database using the `SessionService`.
    - If no `session_id` is found, a new session is created.

3. **Routing and Controller Handling**:
    - The request is routed to the appropriate controller by the `RoutingService`.
    - The controller processes the request, potentially updating session data.
    - The controller generates a response (e.g., HTML, JSON, text) and stores it in the event for further processing
      by middlewares.

4. **After Request (SessionMiddleware)**:
    - After the controller has processed the request, the `SessionMiddleware` checks if the session was modified.
    - If the session was modified, the session data is saved to the database.
    - If a new session was created or the session was updated, the `Set-Cookie` header is added to the response.

5. **Finalizing the Response**:
    - After passing through all middlewares, the response is sent back to the client.
    - The response includes any necessary headers, such as `Set-Cookie` to manage session data in the client browser.

## Session Management

### Session Creation
- A session is created after a successful login and stored in the database.
- The session ID is stored in a cookie (`session_id`), and the session data is serialized and stored in the 
  `SessionModel`.

### Session Expiration
- Sessions include an expiration time (`expires_at`). When the session is loaded, it checks if it has expired.
- Expired sessions are deleted, and a new session is created when needed.

### Logout
- When the user logs out, the session is deleted both from the server and the browser.
- The `Set-Cookie` header is sent with an expiration date in the past to remove the session cookie from the browser.

### Key Components
- **SessionMiddleware**: Handles session data before and after the request.
- **SessionService**: Manages loading, saving, and deleting sessions in the database.

## Example Logout Flow
1. User clicks logout.
2. `logout_controller` calls the `SessionService` to delete the session.
3. A `Set-Cookie` header is added with an expiration date in the past to clear the session cookie.
4. The response is sent back to the user, confirming the logout.

## Key Files
- `src/middleware/session_middleware.py`: Middleware to handle session management.
- `src/services/session_service.py`: Service to interact with the database for session management.
- `src/controllers/logout_controller.py`: Controller for handling user logout.

## Session Expiry Configuration

The session expiry duration can be configured via the `AppConfigService`. By default, sessions will expire after
1 hour (3600 seconds). This can be customized by modifying the `SESSION_EXPIRY_SECONDS` setting in `AppConfigService`.

Example:
```python
# Set session expiry to 2 hours
self.set('SESSION_EXPIRY_SECONDS', 7200)
```
