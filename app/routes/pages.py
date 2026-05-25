from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import datetime

from app import database as db
from app.config import CONFIG
from app.services import goals as goal_repo
from app.services import heatmap as heatmap_svc

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))


def _common_ctx(request: Request) -> dict:
    return {
        "request": request,
        "goals": goal_repo.list_goals(),
        "config": CONFIG,
    }


@router.get("/", response_class=HTMLResponse)
def index(request: Request):
    today = datetime.date.today()
    cells = heatmap_svc.get_month_cells(today.year, today.month)
    return templates.TemplateResponse(
        "index.html",
        {
            **_common_ctx(request),
            "cells": cells,
            "year": today.year,
            "month": today.month,
            "month_name": today.strftime("%B %Y"),
            "today": str(today),
        },
    )


@router.get("/calendar", response_class=HTMLResponse)
def calendar_partial(request: Request, year: int, month: int):
    cells = heatmap_svc.get_month_cells(year, month)
    month_name = datetime.date(year, month, 1).strftime("%B %Y")
    return templates.TemplateResponse(
        "partials/heatmap_grid.html",
        {
            **_common_ctx(request),
            "cells": cells,
            "year": year,
            "month": month,
            "month_name": month_name,
            "today": str(datetime.date.today()),
        },
    )


@router.get("/day/{date}", response_class=HTMLResponse)
def day_detail(request: Request, date: str):
    goals = goal_repo.list_goals()
    goal_keys = [g["key"] for g in goals]

    summaries = db.fetchall(
        "SELECT goal, summary_text, task_count FROM daily_summaries WHERE summary_date = ?",
        (date,),
    )
    tasks = db.fetchall(
        "SELECT t.goal, t.task_text, t.category, t.status, t.effort_minutes "
        "FROM tasks t JOIN log_entries l ON t.log_entry_id = l.id "
        "WHERE l.entry_date = ? ORDER BY t.goal, t.id",
        (date,),
    )

    summaries_by_goal = {s["goal"]: s for s in summaries}
    tasks_by_goal = {g: [t for t in tasks if t["goal"] == g] for g in goal_keys}

    return templates.TemplateResponse(
        "partials/day_detail.html",
        {
            **_common_ctx(request),
            "date": date,
            "summaries_by_goal": summaries_by_goal,
            "tasks_by_goal": tasks_by_goal,
            "has_data": bool(summaries or tasks),
        },
    )


@router.get("/settings", response_class=HTMLResponse)
def settings_page(request: Request):
    return templates.TemplateResponse(
        "settings.html",
        {
            **_common_ctx(request),
        },
    )
