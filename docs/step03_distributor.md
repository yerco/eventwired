# Step 03: Implementing the Distributor

## Overview

In this step, we implement the `Distributor` class, a crucial component of our event-driven microservices (EDM) 
framework. The `Distributor` is responsible for routing events to the appropriate services, ensuring 
that each event is handled efficiently. We also revisit the `Event` class, adding a hashing mechanism 
that includes a timestamp, ensuring the uniqueness of each event.

## Rationale

### The Need for a Distributor

In an event-driven architecture, multiple microservices may need to handle different types of events. 
The `Distributor` serves as a central component that routes incoming events to the appropriate service. 
This ensures that each service only processes events relevant to its responsibilities, promoting decoupling
and scalability.

### Ensuring Event Uniqueness

Events in an EDM framework can be similar but occur at different times or under different contexts. 
To avoid processing stale or redundant events, each event must be uniquely identifiable.
We achieve this by incorporating a timestamp into the event's hash, ensuring that even identical 
events (in terms of data) are treated as unique if they occur at different times.

## Implementation Details

### The Event Class

The `Event` class is the fundamental unit that represents an event in our system. 
Each `Event` instance is uniquely identifiable by its hash, which is derived from its name, 
data, and timestamp.

```python
import hashlib
import json
from datetime import datetime

class Event:
    def __init__(self, name: str, data: Dict = None):
        self.name = name
        self.data = data or {}
        self.timestamp = datetime.utcnow()

    def __hash__(self):
        # Convert the event's data to a JSON string and hash it with its name and timestamp
        event_data_str = json.dumps(self.data, sort_keys=True)
        event_id_str = f"{self.name}:{self.timestamp.isoformat()}:{event_data_str}"
        return int(hashlib.sha256(event_id_str.encode('utf-8')).hexdigest(), 16)
```

### The Distributor Class

- Event Handling: The Distributor checks if an event has already been handled using the event’s hash. 
  If so, it skips reprocessing.
- Round-Robin Distribution: The Distributor uses a round-robin approach to distribute events across services, 
  ensuring even load distribution.
- Need for Event Pruning: The current implementation does not include event pruning. We will need 
  to implement a mechanism to prune old events to prevent memory bloat.

