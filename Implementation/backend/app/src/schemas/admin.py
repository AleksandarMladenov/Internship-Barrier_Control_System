from pydantic import BaseModel, EmailStr, Field
from ..models.admin import AdminRole, AdminStatus

class AdminBase(BaseModel):
    name: str = Field(max_length=120)
    email: EmailStr
    role: AdminRole = AdminRole.viewer
    is_active: bool = True
    status: AdminStatus = AdminStatus.active

class AdminCreate(AdminBase):
    password: str = Field(min_length=6)

class AdminUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=120)
    password: str | None = Field(default=None, min_length=6)
    role: AdminRole | None = None
    is_active: bool | None = None
    status: AdminStatus | None = None

class AdminRead(AdminBase):
    id: int

    class Config:
        from_attributes = True


# --- Invitation DTOs ---

class AdminInviteIn(BaseModel):
    email: EmailStr
    name: str | None = None
    role: AdminRole = AdminRole.admin   # default invite to admin

class AdminInviteOut(BaseModel):
    id: int
    email: EmailStr
    role: AdminRole
    status: AdminStatus
    invite_url: str | None = None
    email_sent: bool | None = None

class AcceptInviteIn(BaseModel):
    token: str
    password: str = Field(min_length=6)
    name: str | None = None
