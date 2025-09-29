from fastapi import FastAPI
from sqlalchemy import text
from src.core.settings import settings
from src.db.database import engine

from .api.routers import vehicles as vehicles_router
from .api.routers import drivers as drivers_router


app = FastAPI(title="Barrier Control System API")
app.include_router(vehicles_router.router)
app.include_router(drivers_router.router)


@app.get("/health")
def health():
    return {"ok": True, "env": settings.ENV}

@app.get("/db-health")
def db_health():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"db_ok": True}
    except Exception as e:
        return {"db_ok": False, "error": str(e)}
