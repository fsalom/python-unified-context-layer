"""FastAPI dependencies using ServiceManager for dependency injection"""

from application.di.service_manager import get_service_manager
from application.services.users_service import UsersService


def get_users_service() -> UsersService:
    """FastAPI dependency for users service"""
    service_manager = get_service_manager()
    return service_manager.get_users_service()
