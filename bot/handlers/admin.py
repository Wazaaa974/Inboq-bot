"""Admin commands — stats and recent leads."""

from telegram import Update
from telegram.ext import ContextTypes

from bot.config import ADMIN_CHAT_ID
from bot.handlers.message import conversations, stats


def _is_admin(user_id: int) -> bool:
    """Check if the user is the admin."""
    if not ADMIN_CHAT_ID:
        return False
    return str(user_id) == str(ADMIN_CHAT_ID)


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/stats — conversation count, qualified leads, messages today."""
    if not _is_admin(update.effective_user.id):
        await update.message.reply_text("This command is for the admin only.")
        return

    text = (
        "📊 <b>Bot Statistics</b>\n\n"
        f"💬 Active conversations: {len(conversations)}\n"
        f"✅ Qualified leads (total): {len(stats['qualified_leads'])}\n"
        f"📨 Messages today: {stats['messages_today']}\n"
        f"📈 Total messages: {stats['total_messages']}"
    )
    await update.message.reply_text(text, parse_mode="HTML")


async def recent_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/recent — last 5 qualified leads."""
    if not _is_admin(update.effective_user.id):
        await update.message.reply_text("This command is for the admin only.")
        return

    leads = stats["qualified_leads"][-5:]
    if not leads:
        await update.message.reply_text("No qualified leads yet.")
        return

    lines = ["📋 <b>Recent Qualified Leads</b>\n"]
    for i, lead in enumerate(reversed(leads), 1):
        contact = f"@{lead['username']}" if lead.get("username") else f"ID: {lead['user_id']}"
        lines.append(
            f"{i}. <b>{lead['name']}</b> ({contact})\n"
            f"   {lead['summary']}\n"
            f"   🕐 {lead['timestamp'][:16]}"
        )

    await update.message.reply_text("\n".join(lines), parse_mode="HTML")
