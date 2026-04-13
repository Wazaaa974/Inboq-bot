import json
import logging
import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env if it exists (local dev), ignore if missing (Railway)
load_dotenv()

logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID", "")
PROFESSIONAL_PROFILE = os.environ.get(
    "PROFESSIONAL_PROFILE",
    "An independent professional offering high-quality services.",
)
WELCOME_MESSAGE = os.environ.get(
    "WELCOME_MESSAGE",
    "Bonjour ! Comment puis-je vous aider ?",
)

_FALLBACK_CONFIG_PATH = Path(__file__).parent.parent / "examples" / "marie_dupont_config.json"

_client_config: dict | None = None


def load_client_config() -> dict:
    """Load the client JSON config once and cache it.

    Reads CLIENT_CONFIG_PATH env var (Railway). Falls back to
    examples/marie_dupont_config.json for local dev.
    """
    global _client_config
    if _client_config is not None:
        return _client_config

    path_str = os.environ.get("CLIENT_CONFIG_PATH", "")
    config_path = Path(path_str) if path_str else _FALLBACK_CONFIG_PATH

    if not config_path.exists():
        logger.warning("Config file not found at %s — using fallback", config_path)
        config_path = _FALLBACK_CONFIG_PATH

    with config_path.open(encoding="utf-8") as f:
        _client_config = json.load(f)

    logger.info("Loaded client config from %s", config_path)
    return _client_config
