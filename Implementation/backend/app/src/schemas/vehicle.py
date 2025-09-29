from pydantic import BaseModel, Field

class VehicleBase(BaseModel):
    region_code: str = Field(max_length=10)
    plate_text: str = Field(max_length=16)

class VehicleCreate(VehicleBase):
    driver_id: int

class VehicleRead(VehicleBase):
    id: int
    driver_id: int
    class Config:
        from_attributes = True  # Pydantic v2: map directly from ORM objects
