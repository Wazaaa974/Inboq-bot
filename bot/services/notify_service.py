"""Escalation notification service — sends qualified leads to admin."""

import logging

from telegram.ext import ContextTypes

from bot.config import ADMIN_CHAT_ID

logger = logging.getLogger(__name__)

_STAR_FILLED = "⭐"
_STAR_EMPTY = "☆"


def _star_rating(score: int, max_score: int = 5) -> str:
    filled = min(score, max_score)
    return _STAR_FILLED * filled + _STAR_EMPTY * (max_score - filled)


async def generate_lead_summary(history: list[dict]) -> str:
    """Generate a one-line lead summary via a short OpenAI call (max 50 tokens)."""
    from openai import AsyncOpenAI
    import os, json

    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        return ""

    recent = [m for m in history if m.get("role") == "user"][-4:]
    excerpt = " | ".join(m.get("content", "") for m in recent)

    client = AsyncOpenAI(api_key=api_key)
    try:
        resp = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": f"Résume en une phrase ce que veut ce client : {excerpt}",
                }
            ],
            max_tokens=50,
            temperature=0.3,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        logger.error("Failed to generate lead summary: %s", e)
        return ""


async def notify_admin(
    context: ContextTypes.DEFAULT_TYPE,
    user_id: int,
    username: str | None,
    full_name: str,
    score: int,
    reasons: list[str],
    history: list[dict],
) -> None:
    """Send a formatted lead notification to the admin chat."""
    if not ADMIN_CHAT_ID:
        logger.warning("ADMIN_CHAT_ID not set — skipping notification")
        return

    summary = await generate_lead_summary(history)
    contact = f"@{username}" if username else f"ID: {user_id}"
    stars = _star_rating(score)
    reasons_str = ", ".join(reasons) if reasons else "—"

    text = (
        f"🔔 <b>Nouveau lead — Score {score}/5</b>\n\n"
        f"<b>Contact :</b> {contact}\n"
        f"<b>Nom :</b> {full_name}\n"
        f"<b>Score :</b> {stars} ({score}/5)\n"
        f"<b>Raisons :</b> {reasons_str}\n\n"
        f"<b>Résumé :</b> {summary}"
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
