# Step 19: `http.request.completed` Event and Subscribers

## Introduction

In this step, we introduced a new event, `http.request.completed`, which is fired when an HTTP request has been 
fully processed. This event allows us to hook into the request lifecycle and perform post-request actions like
logging and timing.

The event-driven model (EDM) in the ASGI async architecture provides a powerful way to handle asynchronous events.
By using the event bus, we can easily extend functionality with subscribers that respond to specific events.

## Event Subscription

In the `demo_app/di_setup.py` file, subscribers are registered to handle events when they are fired by the event bus.

```python
# Subscribers examples
from demo_app.subscribers.logging_subscriber import log_request_response
event_bus.subscribe("http.request.completed", log_request_response)

from demo_app.subscribers.timing_subscriber import request_received, request_completed
event_bus.subscribe('http.request.received', request_received)
event_bus.subscribe('http.request.completed', request_completed)
```

### `http.request.completed`
This event is triggered after an HTTP request has been processed and before the response is sent.
It is useful for logging request details or measuring how long it took to process a request.

### `http.request.received`
This event is triggered when an HTTP request is received, allowing us to capture the exact moment a request enters
the system.

## Subscribers

### Logging Subscriber
The logging subscriber listens for `http.request.completed` and logs details about the request and response.
```python
from demo_app.subscribers.logging_subscriber import log_request_response
event_bus.subscribe("http.request.completed", log_request_response)
```

### Timing Subscriber
The timing subscriber tracks when a request is received and completed. It calculates the time taken to process 
the request and logs it.
```python
from demo_app.subscribers.timing_subscriber import request_received, request_completed
event_bus.subscribe('http.request.received', request_received)
event_bus.subscribe('http.request.completed', request_completed)
```

## Timing Comparison

When comparing timing from the `TimingMiddleware` and Timing Subscriber, you may notice slight differences. 
This is due to:
1. Middleware vs. Event-Based Execution: The `TimingMiddleware` measures time within the request-response cycle, 
   while the Timing Subscriber measures after middleware execution, including event propagation overhead.
2. Event Bus Overhead: The event bus introduces a small delay when publishing events and notifying subscribers.
3. Order of Execution: The Timing Subscriber runs after the middleware chain has completed, resulting in slightly
   longer times being reported.

### Example Timing Output

- TimingMiddleware: `Request processing time: 0.005465 seconds`
- Timing Subscriber: `Request completed for /logout. Time taken: 0.011803 seconds`

The additional time in the subscriber is due to event handling and post-response activities.

By introducing these events and subscribers, we’ve made the framework more flexible and better suited for handling
asynchronous, event-driven tasks.

## Note on Framework-Level Subscribers

Currently, subscribers like logging and timing are not created at the framework level in src/subscribers because
they would come by default, which may not be desirable for all users. Instead, they are part of the demo app 
to keep the framework clean and customizable.
