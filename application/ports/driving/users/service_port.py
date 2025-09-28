from abc import ABC, abstractmethod
from typing import List, Optional

from domain.entities.users import User


class UsersServicePort(ABC):
    """Port interface for Users service operations"""

    @abstractmethod
    async def get_or_create_user(self, rudo_suid: str) -> User:
        """Create a new user with business logic validation"""
        raise NotImplementedError

    @abstractmethod
    async def get_all_users(self) -> List[User]:
        """Get all users"""
        raise NotImplementedError

    @abstractmethod
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        raise NotImplementedError
