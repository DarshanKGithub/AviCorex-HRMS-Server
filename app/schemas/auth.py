from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    email: str = Field(min_length=3)
    password: str = Field(min_length=6)
    role: str | None = None


class TenantPublic(BaseModel):
    id: str
    name: str
    domain: str | None = None


class UserPublic(BaseModel):
    id: str
    full_name: str
    email: str
    role: str
    employee_id: str | None = None
    avatar_url: str | None = None
    tenant_id: str | None = None
    tenant: Optional[TenantPublic] = None
    entitlements: list[str] = []


class LoginResponse(BaseModel):
    access_token: str
    token_type: Literal['bearer'] = 'bearer'
    expires_in: int
    user: UserPublic


class ProfileUpdateRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=120)


class RoleUpdateRequest(BaseModel):
    role: str = Field(min_length=1)


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(min_length=6)
    new_password: str = Field(min_length=6)


class PasswordChangeResponse(BaseModel):
    message: str


class AvatarUploadResponse(BaseModel):
    avatar_url: str


class AvatarDeleteResponse(BaseModel):
    message: str


class PermissionsResponse(BaseModel):
    role: str
    permissions: list[str]


class TenantPublic(BaseModel):
    id: str
    name: str
    domain: str | None = None
