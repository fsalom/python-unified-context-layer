# Dependency Injection System

This module provides a centralized dependency injection system for the application using the ServiceManager pattern.

## Overview

The dependency injection system consists of:

- `ServiceManagerPort`: Abstract interface defining the contract for service management
- `ServiceManager`: Concrete implementation that handles service instantiation and caching
- `dependencies.py`: FastAPI dependency functions that use the ServiceManager

## Usage

### Using in FastAPI endpoints

```python
from fastapi import Depends
from application.di.dependencies import get_users_service
from application.services.users_service import UsersService


async def my_endpoint(
        users_service: UsersService = Depends(get_users_service)
):
    # Use the service
    users = await users_service.get_all_users()
    return users
```

### Getting services directly

```python
from application.di.service_manager import get_service_manager

service_manager = get_service_manager()
users_service = service_manager.get_users_service()

# Or using the generic method
users_service = service_manager.get_service(RudoUsersService)
```

## Adding New Services

To add a new service to the dependency injection system:

1. **Create your service class** (following the existing pattern)
2. **Update the ServiceManager** in `service_manager.py`:

```python
def _get_or_create_service(self, service_type: Type[T]) -> T:
    if service_type not in self._service_cache:
        if service_type == RudoUsersService:
            users_repo = self._get_or_create_repository(UsersRepositoryAdapter)
            self._service_cache[service_type] = RudoUsersService(users_repo)
        elif service_type == YourNewService:  # Add this
            # Inject dependencies as needed
            your_repo = self._get_or_create_repository(YourRepositoryAdapter)
            self._service_cache[service_type] = YourNewService(your_repo)
        else:
            raise ValueError(f"Unknown service type: {service_type}")
    
    return self._service_cache[service_type]
```

3. **Add a specific method** (optional but recommended):

```python
def get_your_service(self) -> YourNewService:
    """Get your service instance"""
    return self._get_or_create_service(YourNewService)
```

4. **Create a FastAPI dependency** in `dependencies.py`:

```python
def get_your_service() -> YourNewService:
    """FastAPI dependency for your service"""
    service_manager = get_service_manager()
    return service_manager.get_your_service()
```

## Benefits

- **Centralized service instantiation**: All service creation logic is in one place
- **Caching**: Services are instantiated once and reused (singleton pattern)
- **Clean separation**: API adapters don't need to know about repository details
- **Testability**: Easy to mock services by replacing the ServiceManager
- **Type safety**: Full type checking support
- **Extensible**: Easy to add new services following the established pattern

## Testing

For testing, you can reset the service manager:

```python
from application.di.service_manager import reset_service_manager

def test_something():
    # Reset before test to ensure clean state
    reset_service_manager()
    
    # Your test code
    service_manager = get_service_manager()
    # ... test logic
```

Or clear the cache:

```python
service_manager = get_service_manager()
service_manager.clear_cache()
``` 