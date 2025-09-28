import asyncio
from typing import List

from commons_package.commons.fast_api.classes import CustomRequest as Request
from commons_package.commons.fast_api.functions import (
    exception_handler, is_authenticated, is_authenticated_or_allow_any)
from commons_package.commons.fast_api.routing import get, post, register_routes
from fastapi import APIRouter, Depends, HTTPException, status

from application.di.dependencies import get_users_service
from application.ports.driving.users.api_port import UsersAPIPort
from application.services.users_service import UsersService
from domain.entities.users import User
from driving.api.users.mapper import UsersAPIMapper
from driving.api.users.models.responses import UserResponse
from driving.api.users.models.requests import GetOrCreateUserRequest


class UsersAPIAdapter(UsersAPIPort):
    """FastAPI adapter for Users operations with dependency injection"""

    def __init__(self):
        self.router = APIRouter(prefix="/users", tags=["users"])
        self.mapper = UsersAPIMapper()
        # Register all decorated routes
        register_routes(self)

    @get("/", response_model=List[UserResponse])
    @exception_handler
    @is_authenticated_or_allow_any
    async def get_all_users(
        self,
        request: Request,
        users_service: UsersService = Depends(get_users_service),
    ) -> List[UserResponse]:
        """Get all users"""
        users = await users_service.get_all_users()
        users = await asyncio.gather(*users)
        return [self.mapper.entity_to_response(user).model_dump() for user in users]

    @post("/", response_model=UserResponse, status_code=status.HTTP_200_OK)
    @exception_handler
    @is_authenticated_or_allow_any
    async def get_or_create_user(
        self,
        request: Request,
        request_data: GetOrCreateUserRequest,
        users_service: UsersService = Depends(get_users_service),
    ) -> UserResponse:
        """Get or Create a new user"""
        created_user = await users_service.get_or_create_user(request_data.rudo_suid)
        return self.mapper.entity_to_response(created_user).model_dump()

    @get("/{user_id}", response_model=UserResponse)
    async def get_user_by_id(
        self, user_id: int, users_service: UsersService = Depends(get_users_service)
    ) -> UserResponse:
        """Get user by ID"""
        user = await users_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {user_id} not found",
            )
        return self.mapper.entity_to_response(user)
