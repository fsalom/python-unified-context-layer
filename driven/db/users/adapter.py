from typing import List, Optional

from application.ports.driven.db.users.repository_port import \
    UsersRepositoryPort
from domain.entities.users import User
from driven.db.users.mapper import UserDBOMapper
from driven.db.users.models import UserDBO

# Type ignores for Django async ORM methods - these exist at runtime but type checker doesn't know about them
# mypy: disable-error-code=attr-defined


class UsersDBRepositoryAdapter(UsersRepositoryPort):
    """Implementation of User repository using Django ORM async methods"""

    def __init__(self):
        self.mapper = UserDBOMapper()

    async def create(self, user: User) -> User:
        """Create a new user"""
        # Use Django's native async save method
        dbo = await self.mapper.entity_to_dbo(user)
        await dbo.asave()

        # Add any M2M field using async methods
        if user.departments:
            department_names = [dept.name for dept in user.departments]
            departments = []
            departments_qs = DepartmentDBO.objects.filter(name__in=department_names)
            if not await departments_qs.aexists():
                for dept_name in department_names:
                    dept, _ = await DepartmentDBO.objects.aget_or_create(name=dept_name)
                    departments.append(dept)
            else:
                async for dept in departments_qs:
                    departments.append(dept)
            await dbo.departments.aset(departments)

        # Refresh and return
        await dbo.arefresh_from_db()
        return await self.mapper.dbo_to_entity(dbo)

    async def get_all(self) -> List[User]:
        """Get all users"""
        users = []
        async for user in UserDBO.objects.prefetch_related('departments').all():  # type: ignore
            entity = self.mapper.dbo_to_entity(user)
            users.append(entity)
        return users

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        try:
            user = await UserDBO.objects.prefetch_related('departments').aget(
                id=user_id
            )
            return self.mapper.dbo_to_entity(user)
        except UserDBO.DoesNotExist:
            return None
