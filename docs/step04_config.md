# Step 04: Configuration and Event Handling Enhancements

## Overview

In this step, we introduced the `ConfigService` to manage configuration settings more efficiently 
and made several key updates to the `Event` and `Distributor` classes. These changes aim to enhance
the flexibility and clarity of the event-driven framework, while also providing a more robust 
configuration management system.

## Key Changes

### 1. Introduction of `ConfigService`

The `ConfigService` class was created to centralize the management of configuration values across
the application. It allows for easy retrieval of configuration settings from various sources such
as environment variables, default values, or external configuration files.

**Usage Example:**

```python
from src.services.config_service import ConfigService

config_service = ConfigService()
secret_key = config_service.get('SECRET_KEY')
prune_interval = config_service.get('PRUNE_INTERVAL')
database_url = config_service.get('DATABASE_URL')
```

## Additionally
### `handled` Attribute in Event Class
The `Event` class now includes a handled attribute to track whether an event has been processed.

### `Distributor` Class Enhancements
The `Distributor` class now uses the handled attribute to manage event state and stores
full `Event` objects in `handled_events`.
