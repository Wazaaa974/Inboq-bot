"""Main message handler — filtering, AI analysis, and escalation."""

import asyncio
import logging
from datetime import datetime, timezone

from telegram import Update
from telegram.ext import ContextTypes

from bot.services.filter_service import check_message
from bot.services.openai_service import analyze_message
from bot.services.notify_service import notify_admin

logger = logging.getLogger(__name__)

# In-memory conversation history per user: {user_id: [{"role": ..., "content": ...}]}
conversations: dict[int, list[dict]] = {}

# Stats tracking
stats = {
    "total_messages": 0,
    "messages_today": 0,
    "last_reset_date": datetime.now(timezone.utc).date(),
    "qualified_leads": [],  # list of {"user_id", "name", "summary", "timestamp"}
}

MAX_HISTORY = 20  # keep last N messages per conversation


def _reset_daily_counter():
    """Reset the daily message counter if the date has changed."""
    today = datetime.now(timezone.utc).date()
    if stats["last_reset_date"] != today:
        stats["messages_today"] = 0
        stats["last_reset_date"] = today


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Route incoming messages through filtering and AI analysis."""
    if not update.message or not update.message.text:
        return

    user = update.effective_user
    user_id = user.id
    message_text = update.message.text

    _reset_daily_counter()
    stats["total_messages"] += 1
    stats["messages_today"] += 1

    # Step 1: Filter
    rejection = check_message(user_id, message_text)
    if rejection == "rate_limited":
        await update.message.reply_text(
            "You're sending messages too quickly. Please wait a moment."
        )
        return
    if rejection == "blocked_keyword":
        await update.message.reply_text("Sorry, I can't help with that.")
        return

    # Step 2: Get conversation history
    history = conversations.get(user_id, [])

    # Step 3: AI analysis
    result = await analyze_message(message_text, history)

    # Step 4: Update conversation history
    history.append({"role": "user", "content": message_text})
    history.append({"role": "assistant", "content": result["response_text"]})
    # Trim to keep memory bounded
    if len(history) > MAX_HISTORY:
        history = history[-MAX_HISTORY:]
    conversations[user_id] = history

    # Step 5: Respond
    if result["response_text"]:
        await update.message.reply_text(result["response_text"])

    # Step 6: Escalate if qualified
    if result["action"] == "escalate" and result["lead_qualified"]:
        full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
        stats["qualified_leads"].append({
            "user_id": user_id,
            "name": full_name or "Unknown",
            "username": user.username,
            "summary": result["lead_summary"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        asyncio.create_task(
            notify_admin(
                context,
                user_id=user_id,
                username=user.username,
                full_name=full_name or "Unknown",
                lead_summary=result["lead_summary"],
            )
        )
