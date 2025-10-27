from pydantic import BaseModel, EmailStr, Field
from ..models.admin import AdminRole

class AdminBase(BaseModel):
    name: str = Field(max_length=120)
    email: EmailStr
    verified: bool = False
    is_accountant: bool = False
    role: AdminRole = AdminRole.viewer
    is_active: bool = True


class AdminCreate(AdminBase):
    password: str = Field(min_length=6)

class AdminUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=120)
    verified: bool | None = None
    is_accountant: bool | None = None
    password: str | None = Field(default=None, min_length=6)
    role: AdminRole | None = None
    is_active: bool | None = None

class AdminRead(AdminBase):
    id: int
    class Config:
        from_attributes = True
