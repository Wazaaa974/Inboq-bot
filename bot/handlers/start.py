from telegram import Update
from telegram.ext import ContextTypes

from bot.config import WELCOME_MESSAGE


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Welcome message when a user starts the bot."""
    await update.message.reply_text(WELCOME_MESSAGE)
