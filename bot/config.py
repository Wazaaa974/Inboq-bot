import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
PROFESSIONAL_PROFILE = os.getenv(
    "PROFESSIONAL_PROFILE",
    "An independent professional offering high-quality services.",
)
