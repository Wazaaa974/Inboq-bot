"""Main message handler — filtering, qualifying, AI analysis, and escalation."""

import logging
from datetime import datetime, timezone

from telegram import Update
from telegram.ext import ContextTypes

from bot.config import load_client_config
from bot.services.filter_service import check_message
from bot.services.openai_service import analyze_message
from bot.services.qualify_service import score_message
from bot.services.notify_service import notify_admin
from bot.services import storage_service

logger = logging.getLogger(__name__)

MAX_HISTORY = 20


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Route incoming messages through filtering, scoring, and AI analysis."""
    if not update.message or not update.message.text:
        return

    user = update.effective_user
    user_id = user.id
    message_text = update.message.text
    full_name = f"{user.first_name or ''} {user.last_name or ''}".strip() or "Unknown"

    storage_service.increment_stat("total_messages")
    storage_service.increment_stat(_today_key())

    # ------------------------------------------------------------------ #
    # Step 1 — Spam / blocklist filter                                    #
    # ------------------------------------------------------------------ #
    rejection = check_message(user_id, message_text)
    if rejection == "rate_limited":
        await update.message.reply_text(
            "Vous envoyez des messages trop rapidement. Merci de patienter un instant."
        )
        return
    if rejection == "blocked_keyword":
        await update.message.reply_text("Désolé, je ne peux pas vous aider avec ça.")
        storage_service.set_state(user_id, "rejected")
        return

    # ------------------------------------------------------------------ #
    # Step 2 — Load history + config                                      #
    # ------------------------------------------------------------------ #
    history = storage_service.get_history(user_id)
    config = load_client_config()

    # ------------------------------------------------------------------ #
    # Step 3 — Deterministic qualification scoring                        #
    # ------------------------------------------------------------------ #
    qual = score_message(message_text, history, config)

    if qual["disqualified"]:
        reason = qual["disqualify_reason"]
        if reason == "négociation de tarif":
            reply = "Les tarifs sont fixes, je ne fais pas de réduction."
        elif reason == "trop vague":
            questions = config.get("qualification", {}).get("qualifying_questions", [])
            reply = questions[0] if questions else "Pouvez-vous préciser votre demande ?"
        else:  # irrespectueux
            reply = "Je vous remercie de votre contact, mais je ne suis pas en mesure de continuer cette conversation."
            storage_service.set_state(user_id, "rejected")
            await update.message.reply_text(reply)
            _append_history(user_id, history, message_text, reply)
            return

        await update.message.reply_text(reply)
        _append_history(user_id, history, message_text, reply)
        return

    # ------------------------------------------------------------------ #
    # Step 4 — Qualified lead (score >= threshold AND no pending question) #
    # ------------------------------------------------------------------ #
    threshold = config.get("qualification", {}).get("score_threshold", 3)

    if qual["score"] >= threshold and qual["should_ask"] is None:
        # Generate warm confirmation via OpenAI
        result = await analyze_message(message_text, history)
        reply = result["response_text"]

        await update.message.reply_text(reply)
        _append_history(user_id, history, message_text, reply)
        storage_service.set_state(user_id, "qualified")

        # Persist lead
        storage_service.save_lead(
            user_id=user_id,
            name=full_name,
            username=user.username,
            summary=f"Score {qual['score']}/5 — {', '.join(qual['reasons'])}",
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        # Notify admin
        await notify_admin(
            context=context,
            user_id=user_id,
            username=user.username,
            full_name=full_name,
            score=qual["score"],
            reasons=qual["reasons"],
            history=history + [{"role": "user", "content": message_text}],
        )
        return

    # ------------------------------------------------------------------ #
    # Step 5 — Still qualifying                                           #
    # ------------------------------------------------------------------ #
    if qual["should_ask"]:
        reply = qual["should_ask"]
        await update.message.reply_text(reply)
    else:
        result = await analyze_message(message_text, history)
        reply = result["response_text"]
        await update.message.reply_text(reply)

    _append_history(user_id, history, message_text, reply)
    storage_service.set_state(user_id, "qualifying")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _append_history(user_id: int, history: list[dict], user_msg: str, bot_reply: str) -> None:
    history.append({"role": "user", "content": user_msg})
    history.append({"role": "assistant", "content": bot_reply})
    if len(history) > MAX_HISTORY:
        history = history[-MAX_HISTORY:]
    storage_service.save_history(user_id, history)


def _today_key() -> str:
    return f"messages_{datetime.now(timezone.utc).date()}"
