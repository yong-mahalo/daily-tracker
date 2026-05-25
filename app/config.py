import json
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Locate config.json relative to this file's package root
_CONFIG_PATH = Path(__file__).parent.parent / "config.json"

_DEFAULT_CONFIG = {
    "notion_phd_db_id": "",
    "notion_nl_db_id": "",
    "notion_china_db_id": "",
    "notion_sync_enabled": False,
    "llm_model": "claude-sonnet-4-6",
    "goal_colors": {
        "phd": "#3B82F6",
        "nl_jobs": "#F97316",
        "china_jobs": "#EF4444",
    },
    "goal_labels": {
        "phd": "PhD Positions",
        "nl_jobs": "Netherlands Jobs",
        "china_jobs": "China Jobs",
    },
}


def load_config() -> dict:
    cfg = dict(_DEFAULT_CONFIG)
    if _CONFIG_PATH.exists():
        with open(_CONFIG_PATH) as f:
            overrides = json.load(f)
        cfg.update(overrides)
    return cfg


# Secrets — only from environment
ANTHROPIC_API_KEY: str = os.environ.get("ANTHROPIC_API_KEY", "")
NOTION_TOKEN: str = os.environ.get("NOTION_TOKEN", "")
DATABASE_PATH: str = os.environ.get("DATABASE_PATH", "./tracker.db")
TRACKER_PASSWORD: str = os.environ.get("TRACKER_PASSWORD", "")

CONFIG: dict = load_config()
