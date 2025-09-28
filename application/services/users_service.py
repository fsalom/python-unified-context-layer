import asyncio
import logging
from typing import List, Optional

from application.ports.driven.db.users.repository_port import \
    UsersRepositoryPort
from application.ports.driving.users.service_port import UsersServicePort
from domain.entities.users import BaseUser, User


class UsersService(UsersServicePort):
    """Application service for RudoUser business logic"""

    def __init__(
        self,
        users_repository: UsersRepositoryPort,
        dashboard_repository: "DashboardRepositoryPort",
    ):
        self.users_repository = users_repository
        self.dashboard_repository = dashboard_repository

    async def get_all_users(self) -> List[User]:
        """Get all users"""
        return await self.users_repository.get_all()

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return await self.users_repository.get_by_id(user_id)

    async def get_or_create_user(self, rudo_suid: str) -> User:
        """Create a new user with business logic validation"""
        # Check if user with rudo_suid already exists
        existing_user = await self.users_repository.get_by_rudo_suid(rudo_suid)
        if existing_user:
            logging.warning(f"User {rudo_suid} already exists")
            return existing_user
        user = await self.dashboard_repository.get_user(rudo_suid)
        return await self.users_repository.create(user)
