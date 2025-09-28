from abc import ABC, abstractmethod
from typing import List

from commons_package.commons.fast_api.classes import CustomRequest as Request

from application.services.users_service import UsersService
from driving.api.users.models.requests import GetOrCreateUserRequest
from driving.api.users.models.responses import UserResponse


class UsersAPIPort(ABC):
    """Port interface for Users API operations"""

    @abstractmethod
    async def get_all_users(
        self, request: Request, users_service: UsersService
    ) -> List[UserResponse]:
        """Get all users"""
        raise NotImplementedError

    @abstractmethod
    async def get_user_by_id(
        self, user_id: int, users_service: UsersService
    ) -> UserResponse:
        """Get user by ID"""
        raise NotImplementedError

    @abstractmethod
    async def get_or_create_user(
        self,
        request: Request,
        request_data: GetOrCreateUserRequest,
        users_service: UsersService,
    ) -> UserResponse:
        """Create a new user"""
        raise NotImplementedError
