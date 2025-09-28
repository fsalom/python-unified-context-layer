# FastAPI Users Microservice

A FastAPI-based microservice built with hexagonal architecture for managing users and departments. This implementation provides async endpoints with dependency injection and integrates seamlessly with the existing Django infrastructure.

## Architecture Overview

This implementation follows **hexagonal architecture** principles:

- **Domain Layer**: Contains business entities (`RudoUser`, `Department`)
- **Application Layer**: Contains business logic services and port interfaces
- **Driving Side**: FastAPI adapters that handle HTTP requests
- **Driven Side**: Repository implementations using Django ORM

## Features

### Users API
- `GET /api/v1/users/` - Get all users
- `GET /api/v1/users/{user_id}` - Get user by ID
- `GET /api/v1/users/email/{email}` - Get user by email
- `GET /api/v1/users/rudo-suid/{rudo_suid}` - Get user by rudo_suid
- `POST /api/v1/users/` - Create new user
- `PUT /api/v1/users/{user_id}` - Update user
- `DELETE /api/v1/users/{user_id}` - Delete user
- `GET /api/v1/users/department/{department_id}` - Get users by department
- `PATCH /api/v1/users/{user_id}/activate` - Activate user
- `PATCH /api/v1/users/{user_id}/deactivate` - Deactivate user

### Departments API
- `GET /api/v1/departments/` - Get all departments
- `GET /api/v1/departments/{department_id}` - Get department by ID
- `GET /api/v1/departments/name/{name}` - Get department by name
- `POST /api/v1/departments/` - Create new department
- `PUT /api/v1/departments/{department_id}` - Update department
- `DELETE /api/v1/departments/{department_id}` - Delete department

## Key Implementation Details

### Dependency Injection
Each adapter uses FastAPI's dependency injection system:

```python
async def get_all_users(
    self,
    users_service: RudoUsersService = Depends(get_users_service)
) -> List[UserResponse]:
    """Get all users"""
    users = await users_service.get_all_users()
    return [self._entity_to_response(user) for user in users]
```

### Async Support
All endpoints are fully async, using Djangos native async ORM operations:

```python
async def get_all(self) -> List[RudoUser]:
    """Get all users"""
    users = []
    async for user in RudoUserDBO.objects.prefetch_related('departments').all():  # type: ignore
        entity = self.mapper.dbo_to_entity(user)
        users.append(entity)
    return users
```

### Business Logic Validation
Application services contain business rules and validation:

```python
async def create_user(self, user: RudoUser) -> RudoUser:
    """Create a new user with business logic validation"""
    # Check if user with email already exists
    existing_user = await self._users_repository.get_by_email(user.email)
    if existing_user:
        raise ValueError(f"User with email {user.email} already exists")
    
    return await self._users_repository.create(user)
```

## Installation and Setup

1. **Install Dependencies**:
   ```bash
   poetry install
   ```

2. **Run Database Migrations**:
   ```bash
   python manage.py migrate
   ```

3. **Start the Application**:
   ```bash
   # Option 1: Using the provided script
   ./scripts/run_fastapi.sh
   
   # Option 2: Direct uvicorn command
   uvicorn config.asgi:application --host 0.0.0.0 --port 8000 --reload
   ```

4. **Access the API**:
   - FastAPI Docs: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc
   - Health Check: http://localhost:8000/health
   - Django Admin: http://localhost:8000/admin/

## Project Structure

```
├── application/
│   ├── ports/                     # Repository interfaces
│   │   ├── rudo_users_repository.py
│   │   └── departments_repository.py
│   └── services/                  # Business logic services
│       ├── rudo_users_service.py
│       └── departments_service.py
├── domain/
│   └── entities/                  # Domain models
│       ├── rudo_users.py
│       └── departments.py
├── driven/
│   └── db/                        # Repository implementations
│       ├── rudo_users/
│       │   └── repository.py
│       └── departments/
│           └── repository.py
├── driving/
│   └── api/
│       ├── fastapi_app.py         # Main FastAPI application
│       └── v1/
│           ├── rudo_users/
│           │   └── adapter.py     # Users FastAPI adapter
│           └── departments/
│               └── adapter.py     # Departments FastAPI adapter
├── config/
│   └── asgi.py                    # Combined Django + FastAPI ASGI
└── scripts/
    └── run_fastapi.sh             # Run script
```

## Request/Response Examples

### Create User
```json
POST /api/v1/users/
{
    "first_name": "John",
    "last_name": "Doe",
    "rudo_suid": "JD001",
    "email": "john.doe@example.com",
    "slack_channel_id": "slack123",
    "bitbucket_channel_id": "bb123",
    "sesame_id": "sesame123",
    "department_ids": [1, 2]
}
```

### Response
```json
{
    "id": 1,
    "first_name": "John",
    "last_name": "Doe",
    "rudo_suid": "JD001",
    "email": "john.doe@example.com",
    "slack_channel_id": "slack123",
    "bitbucket_channel_id": "bb123",
    "sesame_id": "sesame123",
    "is_active": true,
    "departments": [
        {"id": 1, "name": "Engineering"},
        {"id": 2, "name": "Product"}
    ]
}
```

## Error Handling

The API provides comprehensive error handling with appropriate HTTP status codes:

- `400 Bad Request` - Validation errors, business rule violations
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server errors

Example error response:
```json
{
    "detail": "User with email john.doe@example.com already exists"
}
```

## Integration with Django

The FastAPI application integrates seamlessly with the existing Django infrastructure:

- Uses Django ORM models through repository pattern
- Shares the same database and settings
- Django admin interface remains available
- Both applications served through single ASGI server

## Testing

The architecture supports easy testing through dependency injection:

```python
# Test with mock repositories
mock_repo = Mock(spec=RudoUsersRepositoryPort)
service = RudoUsersService(mock_repo, mock_dept_repo)
```

## Production Considerations

1. **Environment Variables**: Configure CORS origins appropriately
2. **Database Connections**: Consider connection pooling for high load
3. **Authentication**: Integrate with OAuth2 system
4. **Monitoring**: Add logging and health checks
5. **Documentation**: API documentation auto-generated by FastAPI

## Benefits of This Implementation

1. **Clean Architecture**: Separation of concerns through hexagonal architecture
2. **Testability**: Easy to test through dependency injection
3. **Async Performance**: Full async support for better performance
4. **Type Safety**: Full type hints and Pydantic validation
5. **Auto-Documentation**: Swagger/OpenAPI docs generated automatically
6. **Flexibility**: Easy to swap out implementations through ports/adapters
7. **Integration**: Seamless integration with existing Django infrastructure 