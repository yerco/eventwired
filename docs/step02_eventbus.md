# Step 02: Implementing the EventBus

## Overview
In this step, we implement an `EventBus` class that serves as the foundation for our 
event-driven microservices architecture. The event bus is an implementation of the 
Observer pattern, which allows us to decouple the services in our application.

## Observer Pattern
The Observer pattern is a behavioral design pattern where an object (the subject) maintains a
list of dependents (observers) that are notified automatically of any state changes. 
In our case, the `EventBus` acts as the subject, and any services that subscribe to events act as observers.

## Implementation
### EventBus
The `EventBus` is a simple class that allows services to subscribe to specific events and 
publish events for other services to react to.

### Application Integration
The ASGI application (`app.py`) acts as a service that listens for incoming HTTP requests 
and publishes a corresponding event (`http.request.received`) to the event bus. 
This decouples the application logic from the request handling, allowing for a more modular 
and testable design.

## Tests
We have implemented a basic test to ensure that the event bus is functioning correctly. 
The test subscribes a mock listener to the event bus and verifies that it receives the correct 
events when an HTTP request is simulated.

## Next Steps
With the event bus in place, we can proceed to implement more services that listen to or 
publish events, such as a router service or logging service.
