"""Goal repository — CRUD over the `goals` table."""
import re

from app import database as db


KEY_PATTERN = re.compile(r"^[a-z0-9_]{1,32}$")


def list_goals() -> list[dict]:
    return db.fetchall(
        "SELECT key, label, color, description, sort_order, notion_db_id "
        "FROM goals ORDER BY sort_order, key"
    )


def list_goal_keys() -> list[str]:
    return [g["key"] for g in list_goals()]


def get_goal(key: str) -> dict | None:
    return db.fetchone(
        "SELECT key, label, color, description, sort_order, notion_db_id "
        "FROM goals WHERE key = ?",
        (key,),
    )


def create_goal(
    key: str,
    label: str,
    color: str,
    description: str | None = None,
    sort_order: int = 0,
    notion_db_id: str | None = None,
) -> dict:
    _validate_key(key)
    _validate_color(color)
    if not label.strip():
        raise ValueError("Label cannot be empty")
    db.execute(
        "INSERT INTO goals (key, label, color, description, sort_order, notion_db_id) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (key, label.strip(), color, description, sort_order, notion_db_id or None),
    )
    return get_goal(key)


def update_goal(key: str, **fields) -> dict:
    existing = get_goal(key)
    if not existing:
        raise ValueError(f"Goal not found: {key}")

    allowed = {"label", "color", "description", "sort_order", "notion_db_id"}
    updates = {k: v for k, v in fields.items() if k in allowed and v is not None}
    if "color" in updates:
        _validate_color(updates["color"])
    if "label" in updates and not str(updates["label"]).strip():
        raise ValueError("Label cannot be empty")
    if not updates:
        return existing

    set_clause = ", ".join(f"{k} = ?" for k in updates)
    params = tuple(updates.values()) + (key,)
    db.execute(f"UPDATE goals SET {set_clause} WHERE key = ?", params)
    return get_goal(key)


def delete_goal(key: str) -> None:
    if not get_goal(key):
        raise ValueError(f"Goal not found: {key}")
    task_count = db.fetchone(
        "SELECT COUNT(*) AS n FROM tasks WHERE goal = ?", (key,)
    )["n"]
    if task_count:
        raise ValueError(
            f"Cannot delete goal '{key}' — {task_count} task(s) still reference it. "
            "Reassign or delete those tasks first."
        )
    db.execute("DELETE FROM goals WHERE key = ?", (key,))


def _validate_key(key: str) -> None:
    if not KEY_PATTERN.match(key):
        raise ValueError(
            "Goal key must be 1–32 chars, lowercase letters, digits, or underscore"
        )


def _validate_color(color: str) -> None:
    if not re.match(r"^#[0-9A-Fa-f]{6}$", color):
        raise ValueError("Color must be a hex string like #RRGGBB")
