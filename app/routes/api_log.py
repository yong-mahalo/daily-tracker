import datetime

from fastapi import APIRouter, BackgroundTasks, Form, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from app import database as db
from app.config import CONFIG
from app.services import llm as llm_svc
from app.services import notion_sync

router = APIRouter()


class LogRequest(BaseModel):
    raw_text: str
    entry_date: str | None = None


def _process_log(raw_text: str, entry_date: str, background_tasks: BackgroundTasks) -> dict:
    """Core log processing logic shared by both endpoints."""
    model = CONFIG["llm_model"]

    log_id = db.execute(
        "INSERT INTO log_entries (entry_date, raw_text, llm_model) VALUES (?, ?, ?)",
        (entry_date, raw_text, model),
    )

    try:
        parsed, tokens = llm_svc.parse_brain_dump(raw_text, entry_date, model)
        db.execute(
            "UPDATE log_entries SET llm_tokens = ?, parse_status = 'ok' WHERE id = ?",
            (tokens, log_id),
        )
    except Exception as e:
        db.execute(
            "UPDATE log_entries SET parse_status = 'failed' WHERE id = ?", (log_id,)
        )
        raise HTTPException(status_code=500, detail=f"LLM parse failed: {e}")

    tasks_by_goal: dict[str, int] = {"phd": 0, "nl_jobs": 0, "china_jobs": 0}
    for task in parsed.get("tasks", []):
        goal = task.get("goal")
        if goal not in tasks_by_goal:
            continue
        task_id = db.execute(
            "INSERT INTO tasks (log_entry_id, goal, task_text, category, status, effort_minutes) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                log_id,
                goal,
                task.get("task_text", ""),
                task.get("category"),
                task.get("status", "logged"),
                task.get("effort_minutes"),
            ),
        )
        tasks_by_goal[goal] += 1
        db.execute("INSERT OR IGNORE INTO notion_sync (task_id) VALUES (?)", (task_id,))

    summaries = parsed.get("summaries", {})
    for goal, text in summaries.items():
        if goal not in tasks_by_goal or not text:
            continue
        db.execute(
            "INSERT INTO daily_summaries (summary_date, goal, summary_text, task_count) "
            "VALUES (?, ?, ?, ?) ON CONFLICT(summary_date, goal) DO UPDATE SET "
            "summary_text = excluded.summary_text, task_count = excluded.task_count, "
            "updated_at = datetime('now')",
            (entry_date, goal, text, tasks_by_goal[goal]),
        )

    if CONFIG.get("notion_sync_enabled"):
        background_tasks.add_task(notion_sync.sync_all_pending)

    return {
        "log_entry_id": log_id,
        "entry_date": entry_date,
        "tasks_by_goal": tasks_by_goal,
        "summaries": summaries,
        "general_notes": parsed.get("general_notes"),
        "notion_sync_queued": CONFIG.get("notion_sync_enabled", False),
    }


# ── HTMX form submission (returns HTML fragment) ──────────────────────────────
@router.post("/log", response_class=HTMLResponse)
def create_log_form(
    background_tasks: BackgroundTasks,
    raw_text: str = Form(...),
    entry_date: str = Form(default=""),
):
    if not entry_date:
        entry_date = str(datetime.date.today())

    try:
        result = _process_log(raw_text, entry_date, background_tasks)
    except HTTPException as e:
        return HTMLResponse(
            f'<div class="log-result-card error" style="margin-top:0.75rem;font-size:0.82rem;">⚠ {e.detail}</div>',
            status_code=e.status_code,
        )

    tbg = result["tasks_by_goal"]
    total = sum(tbg.values())
    labels = CONFIG.get("goal_labels", {})
    colors = {"phd": "#60A5FA", "nl_jobs": "#FB923C", "china_jobs": "#F87171"}

    pills = ""
    for goal, count in tbg.items():
        if count:
            c = colors.get(goal, "#888")
            pills += (
                f'<span style="font-size:0.68rem;font-weight:600;color:{c};'
                f'background:rgba(255,255,255,0.06);border-radius:99px;'
                f'padding:0.15rem 0.55rem;margin-left:0.3rem;">'
                f'{labels.get(goal, goal)} {count}</span>'
            )

    rows = ""
    for goal, text in result.get("summaries", {}).items():
        if text:
            c = colors.get(goal, "#888")
            rows += (
                f'<div style="display:flex;gap:0.5rem;align-items:baseline;'
                f'padding:0.3rem 0;border-top:1px solid rgba(255,255,255,0.06);">'
                f'<span style="font-size:0.68rem;font-weight:600;color:{c};'
                f'white-space:nowrap;">{labels.get(goal, goal)}</span>'
                f'<span style="font-size:0.78rem;color:rgba(255,255,255,0.6);">{text}</span></div>'
            )

    return HTMLResponse(f"""
<div class="log-result-card" style="margin-top:0.75rem;">
  <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:{"0.5rem" if rows else "0"};">
    <span style="font-size:0.8rem;font-weight:600;color:rgba(255,255,255,0.85);">
      ✓ {total} task{'s' if total != 1 else ''} logged
    </span>
    <div>{pills}</div>
  </div>
  {rows}
</div>
""")


# ── JSON API endpoint ─────────────────────────────────────────────────────────
@router.post("/log/json")
def create_log_json(req: LogRequest, background_tasks: BackgroundTasks):
    entry_date = req.entry_date or str(datetime.date.today())
    return _process_log(req.raw_text, entry_date, background_tasks)


@router.get("/log/{log_id}")
def get_log(log_id: int):
    entry = db.fetchone("SELECT * FROM log_entries WHERE id = ?", (log_id,))
    if not entry:
        raise HTTPException(status_code=404, detail="Log entry not found")
    tasks = db.fetchall("SELECT * FROM tasks WHERE log_entry_id = ?", (log_id,))
    return {**entry, "tasks": tasks}
