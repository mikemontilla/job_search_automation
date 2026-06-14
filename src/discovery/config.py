from pathlib import Path

import yaml

from src.agent.config import CONFIG_DIR, DATA_DIR

DISCOVERY_CONFIG = CONFIG_DIR / "discovery_config.yaml"
DB_PATH = DATA_DIR / "discovery.db"

WEB_DIR = Path(__file__).parent / "web"
TEMPLATES_DIR = WEB_DIR / "templates"
STATIC_DIR = WEB_DIR / "static"


def load_config() -> dict:
    if DISCOVERY_CONFIG.exists():
        return yaml.safe_load(DISCOVERY_CONFIG.read_text(encoding="utf-8")) or {}
    return {}


_config = load_config()

MODEL = _config.get("model", "claude-haiku-4-5")
MAX_TOKENS = _config.get("max_tokens", 2048)
PROFILE_LANGUAGE = _config.get("profile_language", "en")
SCORE_THRESHOLD = _config.get("score_threshold", 60)
FETCH_TIMEOUT = _config.get("fetch_timeout", 30)

_web = _config.get("web", {})
WEB_HOST = _web.get("host", "127.0.0.1")
WEB_PORT = _web.get("port", 8000)

SOURCES = _config.get("sources", [])
EMAIL = _config.get("email", {"enabled": False})
