import asyncio
import pytest
from typing import Callable

from src.core.event_bus import Event, EventBus


@pytest.mark.asyncio
async def test_event_bus():
    # Step 1: Create an event bus and subscribe to events
    event_bus = EventBus()
    events_received = []

    async def mock_listener(event: Event):
        events_received.append(event)
        await asyncio.sleep(0)  # No-op async checkpoint

    # Subscribe to the event
    event_bus.subscribe('http.request.received', mock_listener)

    # Step 2: Define a minimal ASGI app for testing
    async def app(scope: dict, receive: Callable, send: Callable) -> None:
        assert scope['type'] == 'http'

        event_data = {
            'scope': scope,
            'receive': receive,
            'send': send,
        }

        # Trigger the event bus to publish the event
        event = Event(name='http.request.received', data=event_data)
        await event_bus.publish(event)

    # Simulate a request
    scope = {'type': 'http', 'path': '/test', 'method': 'GET', 'headers': []}

    async def mock_receive():
        return {}

    async def mock_send(message):
        pass

    # Call the app
    await app(scope, mock_receive, mock_send)

    # Check if the event was received
    assert len(events_received) == 1
    received_event = events_received[0]

    # Ensure the event is of the correct type and contains the expected data
    assert isinstance(received_event, Event)
    assert received_event.name == 'http.request.received'
    assert received_event.data['scope']['path'] == '/test'
    assert received_event.data['scope']['method'] == 'GET'
    assert received_event.data['scope']['headers'] == []


def test_event_bus_subscription():
    event_bus = EventBus()

    def dummy_listener(event: Event):
        event.data['called'] = True

    event_bus.subscribe('test.event', dummy_listener)
    assert len(event_bus.listeners['test.event']) == 1


@pytest.mark.asyncio
async def test_event_bus_publish():
    event_bus = EventBus()
    event_data = {'called': False}

    async def dummy_listener(event: Event):
        event.data['called'] = True
        await asyncio.sleep(0)  # No-op async checkpoint

    event_bus.subscribe('test.event', dummy_listener)
    await event_bus.publish(Event(name='test.event', data=event_data))

    assert event_data['called'] is True


@pytest.mark.asyncio
async def test_event_bus_multiple_listeners():
    event_bus = EventBus()
    call_count = {'count': 0}

    async def listener_one(event: Event):
        call_count['count'] += 1
        await asyncio.sleep(0)  # No-op async checkpoint

    async def listener_two(event: Event):
        call_count['count'] += 1
        await asyncio.sleep(0)  # No-op async checkpoint

    event_bus.subscribe('test.event', listener_one)
    event_bus.subscribe('test.event', listener_two)
    await event_bus.publish(Event(name='test.event', data={}))

    assert call_count['count'] == 2


@pytest.mark.asyncio
async def test_event_bus_publish_no_listeners():
    event_bus = EventBus()
    event_data = {'called': False}

    # No listeners subscribed to 'test.event'
    await event_bus.publish(Event(name='test.event', data=event_data))

    # Since no listener is called, the 'called' flag should remain False
    assert event_data['called'] is False


@pytest.mark.asyncio
async def test_event_bus_dynamic_listener_management():
    event_bus = EventBus()
    event_data = {'called': False}

    async def dynamic_listener(event: Event):
        event.data['called'] = True
        await asyncio.sleep(0)  # No-op async checkpoint

    # Add listener
    event_bus.subscribe('test.event', dynamic_listener)
    await event_bus.publish(Event(name='test.event', data=event_data))
    assert event_data['called'] is True

    # Remove listener
    event_bus.listeners['test.event'].remove(dynamic_listener)
    event_data['called'] = False
    await event_bus.publish(Event(name='test.event', data=event_data))
    assert event_data['called'] is False


@pytest.mark.asyncio
async def test_event_bus_listener_exception_handling():
    event_bus = EventBus()
    call_count = {'count': 0}

    async def faulty_listener(event: Event):
        raise ValueError("An error occurred")

    async def safe_listener(event: Event):
        call_count['count'] += 1
        await asyncio.sleep(0)  # No-op async checkpoint

    event_bus.subscribe('test.event', faulty_listener)
    event_bus.subscribe('test.event', safe_listener)

    try:
        await event_bus.publish(Event(name='test.event', data={}))
    except Exception as e:
        pytest.fail(f"EventBus should handle exceptions in listeners, but failed with {e}")

    # Ensure the safe listener was still called despite the faulty listener
    assert call_count['count'] == 1
