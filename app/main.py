import base64
import secrets
from contextlib import asynccontextmanager

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.config import TRACKER_PASSWORD
from app.database import run_migrations
from app.routes import pages, api_log, api_heatmap, api_widget, api_sync


@asynccontextmanager
async def lifespan(app: FastAPI):
    run_migrations()
    yield


# ── HTTP Basic Auth middleware ─────────────────────────────────────────────────
# Only active when TRACKER_PASSWORD env var is set (skipped for local dev).

class BasicAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not TRACKER_PASSWORD:
            # No password configured — allow all traffic (local dev)
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Basic "):
            try:
                decoded = base64.b64decode(auth_header[6:]).decode("utf-8")
                _, _, password = decoded.partition(":")
                if secrets.compare_digest(password, TRACKER_PASSWORD):
                    return await call_next(request)
            except Exception:
                pass

        return Response(
            content="Unauthorized",
            status_code=401,
            headers={"WWW-Authenticate": 'Basic realm="Daily Tracker"'},
        )


# ── App factory ───────────────────────────────────────────────────────────────

app = FastAPI(title="Daily Progress Tracker", lifespan=lifespan)

app.add_middleware(BasicAuthMiddleware)

# Static files
_STATIC = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(_STATIC)), name="static")

# Routers
app.include_router(pages.router)
app.include_router(api_log.router, prefix="/api")
app.include_router(api_heatmap.router, prefix="/api")
app.include_router(api_widget.router, prefix="/api")
app.include_router(api_sync.router, prefix="/api")
