# Step 20: Custom Events in Login and Logout Controllers

In this step, we introduced custom event handling in both the **login** and **logout** controllers. 
This allows us to trigger events based on successful or failed login and logout attempts, making it easier to
extend functionality and log important user actions for monitoring, auditing, or debugging purposes.

## Key Changes

### 1. **Events in Login and Logout Controllers**

We added event publishing in the `login_controller` and `logout_controller` to emit specific events based 
on user actions:

- `user.login.success`: Emitted when a user successfully logs in.
- `user.login.failure`: Emitted when a user fails to log in.
- `user.logout.success`: Emitted when a user successfully logs out.
- `user.logout.failure`: Emitted when a user attempts to log out but no session is found.

These events allow the system to be more flexible, as other components can subscribe to these events and act 
upon them (e.g., logging, notifications).

### 2. **Event Logging in Database**

We introduced the **EventLog** model, which records events in the database. This model keeps track of the 
following information:
- `event_name`: The name of the event (e.g., `user.login.success`).
- `timestamp`: The time the event occurred.
- `payload`: The data associated with the event (e.g., user ID).

This provides persistent logging for all published events, which can be useful for debugging or monitoring
user behavior.

### 3. **Moving Configuration to `subscriber_setup.py`**

We extracted the subscriber registration process from `di_setup.py` into a new file: `subscriber_setup.py`.
This file contains the configuration for subscribing to events like:

```python
# subscriber_setup.py

from demo_app.subscribers.logging_subscriber import log_request_response
from demo_app.subscribers.timing_subscriber import request_received, request_completed

def register_subscribers(event_bus):
    event_bus.subscribe("http.request.completed", log_request_response)

    event_bus.subscribe('http.request.received', request_received)
    event_bus.subscribe('http.request.completed', request_completed)

    event_bus.subscribe("user.logout.success", log_event_to_db)
    event_bus.subscribe("user.logout.failure", log_event_to_db)
    event_bus.subscribe("user.login.success", log_event_to_db)
    event_bus.subscribe("user.login.failure", log_event_to_db)
```
