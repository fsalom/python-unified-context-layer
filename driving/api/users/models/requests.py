from typing import List, Optional

from pydantic import BaseModel, EmailStr


class GetOrCreateUserRequest(BaseModel): ...


class UpdateUserRequest(BaseModel): ...
