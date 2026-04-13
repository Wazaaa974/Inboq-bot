"""Admin commands — stats and recent leads."""

from datetime import datetime, timezone

from telegram import Update
from telegram.ext import ContextTypes

from bot.config import ADMIN_CHAT_ID
from bot.services import storage_service


def _is_admin(user_id: int) -> bool:
    """Check if the user is the admin."""
    if not ADMIN_CHAT_ID:
        return False
    return str(user_id) == str(ADMIN_CHAT_ID)


def _today_key() -> str:
    return f"messages_{datetime.now(timezone.utc).date()}"


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/stats — conversation count, qualified leads, messages today."""
    if not _is_admin(update.effective_user.id):
        await update.message.reply_text("This command is for the admin only.")
        return

    text = (
        "📊 <b>Bot Statistics</b>\n\n"
        f"💬 Active conversations: {storage_service.count_active_conversations()}\n"
        f"✅ Qualified leads (total): {storage_service.count_leads()}\n"
        f"📨 Messages today: {storage_service.get_stat(_today_key())}\n"
        f"📈 Total messages: {storage_service.get_stat('total_messages')}"
    )
    await update.message.reply_text(text, parse_mode="HTML")


async def recent_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/recent — last 5 qualified leads."""
    if not _is_admin(update.effective_user.id):
        await update.message.reply_text("This command is for the admin only.")
        return

    leads = storage_service.get_recent_leads(5)
    if not leads:
        await update.message.reply_text("No qualified leads yet.")
        return

    lines = ["📋 <b>Recent Qualified Leads</b>\n"]
    for i, lead in enumerate(leads, 1):
        contact = f"@{lead['username']}" if lead.get("username") else f"ID: {lead['user_id']}"
        lines.append(
            f"{i}. <b>{lead['name']}</b> ({contact})\n"
            f"   {lead['summary']}\n"
            f"   🕐 {lead['timestamp'][:16]}"
        )

    await update.message.reply_text("\n".join(lines), parse_mode="HTML")
