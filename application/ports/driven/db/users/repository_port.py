from abc import ABC, abstractmethod
from typing import List, Optional

from domain.entities.users import User


class UsersRepositoryPort(ABC):
    """Port (interface) for User repository operations"""

    @abstractmethod
    async def create(self, user: User) -> User:
        """Creates a new user"""
        raise NotImplementedError

    @abstractmethod
    async def get_all(self) -> List[User]:
        """Get all users"""
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        raise NotImplementedError
