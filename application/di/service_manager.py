from typing import Any, Dict, List, Optional

from application.services.users_service import UsersService
from driven.db.users.adapter import UsersDBRepositoryAdapter


class ServiceManager:
    """Concrete implementation of service manager for dependency injection"""

    def __init__(self):
        self._service_cache: Dict[str, Any] = {}
        self._repository_cache: Dict[str, Any] = {}
        self.services = {
            "users": UsersService,
        }
        self.repositories = {
            "users": UsersDBRepositoryAdapter,
            "dashboard": DashboardRepositoryAdapter,
        }

    def _get_or_create_repository(self, repositories_type: List[str]) -> List[Any]:
        """Get or create a repository instance with caching"""
        repos = []
        for repository_type in repositories_type:
            if repository_type not in self._repository_cache:
                if repository_type not in self.repositories:
                    raise ValueError(f"Unknown repository type: {repository_type}")
                self._repository_cache[repository_type] = self.repositories[
                    repository_type
                ]()

            repos.append(self._repository_cache[repository_type])
        return repos

    def _get_or_create_service(
        self, service_type: str, repositories_type: List[str]
    ) -> Any:
        """Get or create a service instance with caching"""
        if service_type not in self._service_cache:
            if service_type not in self.services:
                raise ValueError(f"Unknown service type: {service_type}")

            repos = self._get_or_create_repository(repositories_type)
            self._service_cache[service_type] = self.services[service_type](*repos)
        return self._service_cache[service_type]

    def get_users_service(self) -> UsersService:
        """Get users service instance"""
        return self._get_or_create_service("users", ["users", "dashboard"])

    def get_service(self, service_type: str) -> Any:
        """Get service instance by type"""
        return self._get_or_create_service(service_type)

    def clear_cache(self) -> None:
        """Clear all cached instances (useful for testing)"""
        self._service_cache.clear()
        self._repository_cache.clear()


# Global service manager instance
_service_manager: Optional[ServiceManager] = None


def get_service_manager() -> ServiceManager:
    """Get global service manager instance (singleton pattern)"""
    global _service_manager
    if _service_manager is None:
        _service_manager = ServiceManager()
    return _service_manager


def reset_service_manager() -> None:
    """Reset global service manager (useful for testing)"""
    global _service_manager
    _service_manager = None
