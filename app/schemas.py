from typing import Any, Optional, Union

from pydantic import BaseModel


class LoginPayload(BaseModel):
    username: str
    password: str


class UserInfo(BaseModel):
    username: str
    nickname: str
    roleName: str


class LoginResponse(BaseModel):
    token: str
    user: UserInfo


class OverviewResponse(BaseModel):
    welcomeText: str
    quickActions: list[str]


class ApiResponse(BaseModel):
    code: int = 0
    message: str = "success"
    data: Optional[Union[dict, list, str, int, Any]] = None
