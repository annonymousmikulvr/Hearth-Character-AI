from fastapi import APIRouter

from app.config import settings
from app.database import get_db

router = APIRouter()


@router.get("/health")
async def health():
    db_ok = False
    try:
        db = get_db()
        await db.execute("SELECT 1")
        db_ok = True
    except Exception:
        pass
    return {
        "status": "ok",
        "version": settings.app_version,
        "database": "connected" if db_ok else "not_connected",
    }
