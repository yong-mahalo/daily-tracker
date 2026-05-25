from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import datetime

from app.config import CONFIG
from app.services import heatmap as heatmap_svc

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))


@router.get("/", response_class=HTMLResponse)
def index(request: Request):
    today = datetime.date.today()
    cells = heatmap_svc.get_month_cells(today.year, today.month)
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "cells": cells,
            "year": today.year,
            "month": today.month,
            "month_name": today.strftime("%B %Y"),
            "today": str(today),
            "config": CONFIG,
        },
    )


@router.get("/calendar", response_class=HTMLResponse)
def calendar_partial(request: Request, year: int, month: int):
    cells = heatmap_svc.get_month_cells(year, month)
    import calendar as cal_mod
    month_name = datetime.date(year, month, 1).strftime("%B %Y")
    return templates.TemplateResponse(
        "partials/heatmap_grid.html",
        {
            "request": request,
            "cells": cells,
            "year": year,
            "month": month,
            "month_name": month_name,
            "today": str(datetime.date.today()),
            "config": CONFIG,
        },
    )


@router.get("/day/{date}", response_class=HTMLResponse)
def day_detail(request: Request, date: str):
    from app import database as db
    from app.config import CONFIG

    summaries = db.fetchall(
        "SELECT goal, summary_text, task_count FROM daily_summaries WHERE summary_date = ?",
        (date,),
    )
    tasks = db.fetchall(
        "SELECT goal, task_text, category, status, effort_minutes FROM tasks t "
        "JOIN log_entries l ON t.log_entry_id = l.id WHERE l.entry_date = ? ORDER BY goal, t.id",
        (date,),
    )

    # Group by goal
    goals = ["phd", "nl_jobs", "china_jobs"]
    summaries_by_goal = {s["goal"]: s for s in summaries}
    tasks_by_goal = {g: [t for t in tasks if t["goal"] == g] for g in goals}

    return templates.TemplateResponse(
        "partials/day_detail.html",
        {
            "request": request,
            "date": date,
            "goals": goals,
            "summaries_by_goal": summaries_by_goal,
            "tasks_by_goal": tasks_by_goal,
            "config": CONFIG,
            "has_data": bool(summaries or tasks),
        },
    )
