from domain.entities.users import User

from .models.responses import UserResponse


class UsersAPIMapper:
    def entity_to_response(self, entity: User) -> UserResponse:
        return UserResponse(**entity.model_dump())
