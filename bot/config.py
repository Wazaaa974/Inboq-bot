import os
from dotenv import load_dotenv

# Load .env if it exists (local dev), ignore if missing (Railway)
load_dotenv()

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
