import os

from fastapi import APIRouter
from fastapi.responses import FileResponse

from app import database as db
from app.config import DATABASE_PATH
from app.services import notion_sync

router = APIRouter()


@router.get("/sync/status")
def sync_status():
    pending = db.fetchall(
        "SELECT ns.*, t.task_text, t.goal FROM notion_sync ns "
        "JOIN tasks t ON ns.task_id = t.id WHERE ns.sync_status IN ('pending', 'failed')"
    )
    return {"pending_count": len(pending), "items": pending}


@router.post("/sync/retry")
def sync_retry():
    synced, failed = notion_sync.sync_all_pending()
    return {"synced": synced, "failed": failed}


@router.get("/export")
def export_db():
    if not os.path.exists(DATABASE_PATH):
        return {"error": "Database not found"}
    return FileResponse(
        DATABASE_PATH,
        media_type="application/octet-stream",
        filename="tracker.db",
    )
