from pydantic import BaseModel, EmailStr, Field

class DriverBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr

class DriverCreate(DriverBase):
    pass

class DriverRead(DriverBase):
    id: int
    class Config:
        from_attributes = True
