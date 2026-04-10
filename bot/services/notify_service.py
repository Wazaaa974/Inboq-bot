"""Escalation notification service — sends qualified leads to admin."""

import logging

from telegram.ext import ContextTypes

from bot.config import ADMIN_CHAT_ID

logger = logging.getLogger(__name__)


async def notify_admin(
    context: ContextTypes.DEFAULT_TYPE,
    user_id: int,
    username: str | None,
    full_name: str,
    lead_summary: str,
) -> None:
    """Send a formatted lead notification to the admin chat."""
    if not ADMIN_CHAT_ID:
        logger.warning("ADMIN_CHAT_ID not set — skipping notification")
        return

    contact = f"@{username}" if username else f"ID: {user_id}"
    text = (
        "🔔 <b>New Qualified Lead</b>\n\n"
        f"<b>Contact:</b> {contact}\n"
        f"<b>Name:</b> {full_name}\n"
        f"<b>Summary:</b> {lead_summary}"
    )

    try:
        await context.bot.send_message(
            chat_id=int(ADMIN_CHAT_ID),
            text=text,
            parse_mode="HTML",
            disable_notification=True,
        )
    except Exception as e:
        logger.error("Failed to notify admin: %s", e)
