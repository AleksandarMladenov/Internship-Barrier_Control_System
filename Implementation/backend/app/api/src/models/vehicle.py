from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from src.db.database import Base

class Vehicle(Base):
    __tablename__ = "vehicles"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    plate: Mapped[str] = mapped_column(String(16), unique=True, index=True)
