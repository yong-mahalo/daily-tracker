"""
Notion sync — mirrors phd_tracker.py pattern exactly:
plain requests.post(), NOTION_HEADERS constant, direct JSON property building.
"""
import requests

from app import database as db
from app.config import CONFIG, NOTION_TOKEN

NOTION_VERSION = "2022-06-28"
NOTION_HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": NOTION_VERSION,
}

# Map goal → config key for DB ID
_DB_ID_KEYS = {
    "phd": "notion_phd_db_id",
    "nl_jobs": "notion_nl_db_id",
    "china_jobs": "notion_china_db_id",
}


def sync_task(task_id: int) -> str:
    """Push one task to Notion. Returns notion_page_id on success. Raises on failure."""
    task = db.fetchone(
        "SELECT t.*, l.entry_date FROM tasks t JOIN log_entries l ON t.log_entry_id = l.id WHERE t.id = ?",
        (task_id,),
    )
    if not task:
        raise ValueError(f"Task {task_id} not found")

    goal = task["goal"]
    db_id = CONFIG.get(_DB_ID_KEYS.get(goal, ""), "")
    if not db_id:
        raise ValueError(f"Notion DB ID not configured for goal: {goal}")

    payload = {
        "parent": {"database_id": db_id},
        "properties": {
            "Name": {
                "title": [{"text": {"content": task["task_text"]}}]
            },
            "Status": {
                "status": {"name": _map_status(task["status"])}
            },
            "Category": {
                "select": {"name": task["category"] or "general"}
            },
            "Log Date": {
                "date": {"start": task["entry_date"]}
            },
            "Effort (min)": {
                "number": task["effort_minutes"]
            },
            "Source Entry ID": {
                "rich_text": [{"text": {"content": str(task["log_entry_id"])}}]
            },
        },
    }

    # Remove null number field (Notion rejects null for number)
    if task["effort_minutes"] is None:
        del payload["properties"]["Effort (min)"]

    resp = requests.post(
        "https://api.notion.com/v1/pages",
        headers=NOTION_HEADERS,
        json=payload,
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()["id"]


def sync_all_pending() -> tuple[int, int]:
    """Retry all pending/failed syncs. Returns (synced_count, failed_count)."""
    if not CONFIG.get("notion_sync_enabled"):
        return 0, 0

    pending = db.fetchall(
        "SELECT task_id FROM notion_sync WHERE sync_status IN ('pending', 'failed')"
    )
    synced, failed = 0, 0
    for row in pending:
        task_id = row["task_id"]
        try:
            page_id = sync_task(task_id)
            db.execute(
                "UPDATE notion_sync SET sync_status='synced', notion_page_id=?, synced_at=datetime('now'), error_message=NULL WHERE task_id=?",
                (page_id, task_id),
            )
            synced += 1
        except Exception as e:
            db.execute(
                "UPDATE notion_sync SET sync_status='failed', error_message=? WHERE task_id=?",
                (str(e), task_id),
            )
            failed += 1
    return synced, failed


def _map_status(status: str) -> str:
    return {"done": "Done", "in_progress": "In Progress", "logged": "Not started"}.get(status, "Not started")
