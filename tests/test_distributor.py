import pytest

from datetime import datetime, timedelta

from src.core.distributor import Distributor
from src.core.event_bus import Event


@pytest.mark.asyncio
async def test_distributor_routes_to_correct_service():
    async def service_a(event: Event):
        if event.data['path'] == "/a":
            return True
        return False

    async def service_b(event: Event):
        if event.data['path'] == "/b":
            return True
        return False

    distributor = Distributor(services=[service_a, service_b])

    event_a = Event(name='http.request.received', data={'path': '/a'})
    handled_a = await distributor.distribute(event_a)
    assert handled_a is True

    event_b = Event(name='http.request.received', data={'path': '/b'})
    handled_b = await distributor.distribute(event_b)
    assert handled_b is True


@pytest.mark.asyncio
async def test_distributor_handles_unhandled_request():
    async def service_a(event: Event):
        if event.data['path'] == "/a":
            return True
        return False

    async def service_b(event: Event):
        if event.data['path'] == "/b":
            return True
        return False

    distributor = Distributor(services=[service_a, service_b])

    event_c = Event(name='http.request.received', data={'path': '/c'})
    handled_c = await distributor.distribute(event_c)
    assert handled_c is False


@pytest.mark.asyncio
async def test_distributor_round_robin_distribution():
    # Mock services with counters
    call_count = {'service_a': 0, 'service_b': 0}

    async def service_a(event: Event):
        if event.data['path'] == "/a":
            call_count['service_a'] += 1
            return True
        return False

    async def service_b(event: Event):
        if event.data['path'] == "/b":
            call_count['service_b'] += 1
            return True
        return False

    distributor = Distributor(services=[service_a, service_b])

    # Test the round-robin distribution
    event_a = Event(name='http.request.received', data={'path': '/a', 'body': 'a'})
    event_b = Event(name='http.request.received', data={'path': '/b', 'body': 'b'})
    event_unhandled = Event(name='http.request.received', data={'path': '/unhandled', 'body': 'unhandled'})

    await distributor.distribute(event_a)
    await distributor.distribute(event_b)
    await distributor.distribute(event_unhandled)

    # Check that each service was called once
    assert call_count['service_a'] == 1
    assert call_count['service_b'] == 1


@pytest.mark.asyncio
async def test_distributor_skips_handled_event(monkeypatch):
    call_count = {'service_a': 0, 'service_b': 0}

    async def service_a(event: Event):
        call_count['service_a'] += 1
        if event.data['path'] == "/a":
            return True
        return False

    async def service_b(event: Event):
        call_count['service_b'] += 1
        if event.data['path'] == "/b":
            return True
        return False

    distributor = Distributor(services=[service_a, service_b])
    monkeypatch.setattr(distributor, 'event_lifetime', timedelta(seconds=1))

    # First, distribute the event to ensure it's handled
    event_a = Event(name='http.request.received', data={'path': '/a'})
    handled_a = await distributor.distribute(event_a)
    assert handled_a is True  # The event should be handled by service_a

    # Try to distribute the same event again
    handled_a_again = await distributor.distribute(event_a)
    assert handled_a_again is True  # The event should be considered as already handled

    # Ensure that service_a was only called once
    assert call_count['service_a'] == 1
    assert call_count['service_b'] == 0


@pytest.mark.asyncio
async def test_prune_old_events(monkeypatch):
    # Step 1: Create a mock event class with a timestamp attribute
    class MockEvent:
        def __init__(self, timestamp):
            self.timestamp = timestamp

    # Step 2: Initialize the Distributor with a mocked event_lifetime
    distributor = Distributor(services=[])
    monkeypatch.setattr(distributor, 'event_lifetime', timedelta(seconds=5))

    # Step 3: Add events to the handled_events dictionary
    old_event = MockEvent(timestamp=datetime.utcnow() - timedelta(seconds=10))
    new_event = MockEvent(timestamp=datetime.utcnow())

    distributor.handled_events = {
        "old_event_id": old_event,
        "new_event_id": new_event,
    }

    # Step 4: Invoke prune_old_events
    distributor.prune_old_events()

    # Step 5: Assert that the old event was pruned and the new event remains
    assert "old_event_id" not in distributor.handled_events
    assert "new_event_id" in distributor.handled_events
