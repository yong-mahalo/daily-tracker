from fastapi import APIRouter, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel

from app.services import goals as goal_repo

router = APIRouter()


class GoalIn(BaseModel):
    key: str
    label: str
    color: str
    description: str | None = None
    sort_order: int = 0
    notion_db_id: str | None = None


class GoalUpdate(BaseModel):
    label: str | None = None
    color: str | None = None
    description: str | None = None
    sort_order: int | None = None
    notion_db_id: str | None = None


@router.get("/goals")
def list_goals():
    return {"goals": goal_repo.list_goals()}


@router.post("/goals")
def create_goal_json(goal: GoalIn):
    try:
        return goal_repo.create_goal(
            key=goal.key,
            label=goal.label,
            color=goal.color,
            description=goal.description,
            sort_order=goal.sort_order,
            notion_db_id=goal.notion_db_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/goals/{key}")
def update_goal_json(key: str, patch: GoalUpdate):
    try:
        return goal_repo.update_goal(key, **patch.model_dump(exclude_none=True))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/goals/{key}")
def delete_goal_json(key: str):
    try:
        goal_repo.delete_goal(key)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"deleted": key}


# ── HTML form endpoints (settings page) ───────────────────────────────────────

@router.post("/goals/form", response_class=HTMLResponse)
def create_goal_form(
    key: str = Form(...),
    label: str = Form(...),
    color: str = Form(...),
    description: str = Form(default=""),
    sort_order: int = Form(default=0),
    notion_db_id: str = Form(default=""),
):
    try:
        goal_repo.create_goal(
            key=key.strip().lower(),
            label=label,
            color=color,
            description=description or None,
            sort_order=sort_order,
            notion_db_id=notion_db_id or None,
        )
    except ValueError as e:
        return HTMLResponse(
            f'<div class="settings-error">⚠ {e}</div>',
            status_code=400,
        )
    return RedirectResponse(url="/settings", status_code=303)


@router.post("/goals/{key}/update", response_class=HTMLResponse)
def update_goal_form(
    key: str,
    label: str = Form(...),
    color: str = Form(...),
    description: str = Form(default=""),
    sort_order: int = Form(default=0),
    notion_db_id: str = Form(default=""),
):
    try:
        goal_repo.update_goal(
            key,
            label=label,
            color=color,
            description=description or None,
            sort_order=sort_order,
            notion_db_id=notion_db_id or None,
        )
    except ValueError as e:
        return HTMLResponse(
            f'<div class="settings-error">⚠ {e}</div>',
            status_code=400,
        )
    return RedirectResponse(url="/settings", status_code=303)


@router.post("/goals/{key}/delete", response_class=HTMLResponse)
def delete_goal_form(key: str):
    try:
        goal_repo.delete_goal(key)
    except ValueError as e:
        return HTMLResponse(
            f'<div class="settings-error">⚠ {e}</div>',
            status_code=400,
        )
    return RedirectResponse(url="/settings", status_code=303)
