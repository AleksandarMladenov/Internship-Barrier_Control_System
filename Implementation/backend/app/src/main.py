from fastapi import FastAPI
from sqlalchemy import text
from src.core.settings import settings
from src.db.database import engine
from .api import api_router  # <- central router (from api/routers/__init__.py)
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Barrier Control API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:5176",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

@app.get("/api/health")
def health():
    return {"ok": True, "env": settings.ENV}

@app.get("/api/db-health")
def db_health():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"db_ok": True}
    except Exception as e:
        return {"db_ok": False, "error": str(e)}
