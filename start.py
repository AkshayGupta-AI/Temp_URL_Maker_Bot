import os
import time
import secrets

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from database import init_db, create_link

BOT_TOKEN = os.environ.get("BOT_TOKEN")
BASE_URL = os.environ.get("RENDER_EXTERNAL_URL")

init_db()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "🔗 Expiring Link Bot\n\n"
        "Send me a URL to create a temporary link."
    )


async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    # basic URL check
    if not (text.startswith("http://") or text.startswith("https://")):
        await update.message.reply_text("❌ Please send a valid URL (http/https)")
        return

    context.user_data["url"] = text
    await update.message.reply_text("⏳ Enter expiry time in hours (2–24)")


async def handle_expiry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "url" not in context.user_data:
        return

    try:
        hours = int(update.message.text)
        if hours < 2 or hours > 24:
            raise ValueError
    except:
        await update.message.reply_text("❌ Enter hours between 2 and 24")
        return

    context.user_data["hours"] = hours
    await update.message.reply_text("🖱️ Enter click limit")


async def handle_clicks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "hours" not in context.user_data:
        return

    try:
        clicks = int(update.message.text)
        if clicks < 1:
            raise ValueError
    except:
        await update.message.reply_text("❌ Enter a valid click number")
        return

    url = context.user_data["url"]
    hours = context.user_data["hours"]

    code = secrets.token_urlsafe(6)
    expires_at = int(time.time() + hours * 3600)

    create_link(code, url, expires_at, clicks)

    final_url = f"{BASE_URL}/{code}"

    context.user_data.clear()

    await update.message.reply_text(
        f"✅ Temporary Link Created:\n{final_url}\n\n"
        f"⏳ Valid: {hours} hours\n"
        f"🖱️ Clicks: {clicks}"
    )


def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN not set")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    # ORDER IS IMPORTANT
    app.add_handler(MessageHandler(filters.Regex("^[0-9]+$"), handle_expiry))
    app.add_handler(MessageHandler(filters.Regex("^[0-9]+$"), handle_clicks))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))

    app.run_polling()


if __name__ == "__main__":
    main()