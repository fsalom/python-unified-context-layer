from typing import List, Optional

from pydantic import BaseModel, EmailStr


class BaseUserResponse(BaseModel): ...


class UserResponse(BaseUserResponse): ...
