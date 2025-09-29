from fastapi import FastAPI
from sqlalchemy import text
from src.core.settings import settings
from src.db.database import engine

app = FastAPI(title="Parking API", version="0.0.1")

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
