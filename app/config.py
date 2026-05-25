import json
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

_CONFIG_PATH = Path(__file__).parent.parent / "config.json"

_DEFAULT_CONFIG = {
    "llm_model": "claude-sonnet-4-6",
    "notion_sync_enabled": False,
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
