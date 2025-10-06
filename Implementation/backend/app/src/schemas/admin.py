from pydantic import BaseModel, EmailStr, Field

class AdminBase(BaseModel):
    name: str = Field(max_length=120)
    email: EmailStr
    verified: bool = False
    is_accountant: bool = False

class AdminCreate(AdminBase):
    password: str = Field(min_length=6)

class AdminUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=120)
    verified: bool | None = None
    is_accountant: bool | None = None
    password: str | None = Field(default=None, min_length=6)

class AdminRead(AdminBase):
    id: int
    class Config:
        from_attributes = True
