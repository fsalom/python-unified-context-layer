from typing import List

from domain.entities.users import BaseUser, User
from driven.db.users.models import UserDBO


class UserDBOMapper:
    async def entity_to_dbo(self, entity: User) -> UserDBO:
        return UserDBO(
            first_name=entity.first_name,
            last_name=entity.last_name,
            rudo_suid=entity.rudo_suid,
            email=entity.email,
            slack_channel_id=entity.slack_channel_id,
            bitbucket_account_id=entity.bitbucket_account_id,
            sesame_id=entity.sesame_id,
        )

    async def dbo_to_entity(self, dbo: UserDBO) -> User:
        departments = []
        async for dept in dbo.departments.all():
            departments.append(Department(id=dept.id, name=dept.name))

        return User(
            id=dbo.id,
            first_name=dbo.first_name,
            last_name=dbo.last_name,
            rudo_suid=dbo.rudo_suid,
            email=dbo.email,
            slack_channel_id=dbo.slack_channel_id,
            bitbucket_account_id=dbo.bitbucket_account_id,
            sesame_id=dbo.sesame_id,
            is_active=dbo.is_active,
            departments=departments,
        )
