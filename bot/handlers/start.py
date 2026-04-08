from telegram import Update
from telegram.ext import ContextTypes

from bot.config import PROFESSIONAL_PROFILE


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome message when a user starts the bot."""
    await update.message.reply_text(
        f"Hi! I'm an assistant for a professional ({PROFESSIONAL_PROFILE}). "
        "How can I help you today?"
    )
