# backend/app/src/db/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from src.core.settings import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, future=True)

class Base(DeclarativeBase):
    pass

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)

# NEW: central FastAPI dependency for a per-request Session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
