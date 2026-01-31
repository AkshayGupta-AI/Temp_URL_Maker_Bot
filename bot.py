import time
import uuid
import threading
import os
import sqlite3
from flask import Flask, redirect
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# ================= CONFIG =================
ALLOWED_HOURS = [2, 4, 6, 8, 12, 24]
MAX_ALLOWED_CLICKS = 10
# =========================================

app = Flask(__name__)
DB_FILE = "links.db"


# ---------------- DATABASE ----------------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS links (
            token TEXT PRIMARY KEY,
            url TEXT,
            expiry INTEGER,
            clicks INTEGER,
            max_clicks INTEGER
        )
    """)
    conn.commit()
    conn.close()


def get_link(token):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT url, expiry, clicks, max_clicks FROM links WHERE token=?", (token,))
    row = cur.fetchone()
    conn.close()
    return row


def update_click(token, clicks):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("UPDATE links SET clicks=? WHERE token=?", (clicks, token))
    conn.commit()
    conn.close()


def delete_link(token):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("DELETE FROM links WHERE token=?", (token,))
    conn.commit()
    conn.close()


def save_link(token, url, expiry, max_clicks):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO links VALUES (?, ?, ?, ?, ?)",
        (token, url, expiry, 0, max_clicks)
    )
    conn.commit()
    conn.close()


# ---------------- FLASK ----------------
@app.route("/<token>")
def open_link(token):
    data = get_link(token)

    if not data:
        return "❌ Link Expired or Invalid"

    url, expiry, clicks, max_clicks = data

    if time.time() > expiry:
        delete_link(token)
        return "❌ Link Expired"

    if clicks >= max_clicks:
        delete_link(token)
        return "❌ Click limit exceeded"

    update_click(token, clicks + 1)
    return redirect(url)


# ---------------- TELEGRAM ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔗 Send your link"
    )


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text.strip()

    # Step 1: Link
    if msg.startswith("http"):
        context.user_data["url"] = msg
        await update.message.reply_text(
            "⏳ Enter expiry hours:\n2 / 4 / 6 / 8 / 12 / 24"
        )
        return

    # Step 2: Expiry
    if msg.isdigit() and "url" in context.user_data and "hours" not in context.user_data:
        hours = int(msg)

        if hours not in ALLOWED_HOURS:
            await update.message.reply_text("❌ Only 2,4,6,8,12,24 allowed")
            return

        context.user_data["hours"] = hours
        await update.message.reply_text(
            "👆 Enter click limit (1–10)"
        )
        return

    # Step 3: Click limit
    if msg.isdigit() and "hours" in context.user_data:
        max_clicks = int(msg)

        if max_clicks < 1 or max_clicks > MAX_ALLOWED_CLICKS:
            await update.message.reply_text("❌ Click limit must be 1–10")
            return

        token = uuid.uuid4().hex[:8]
        expiry = time.time() + context.user_data["hours"] * 3600

        save_link(
            token,
            context.user_data["url"],
            expiry,
            max_clicks
        )

        base_url = context.bot_data["BASE_URL"]
        temp_link = f"{base_url}/{token}"

        await update.message.reply_text(
            f"✅ Temporary Link Created\n\n"
            f"⏳ Valid: {context.user_data['hours']} hours\n"
            f"👆 Max clicks: {max_clicks}\n\n"
            f"{temp_link}"
        )

        context.user_data.clear()


# ---------------- RUN ----------------
def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)


def main():
    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    BASE_URL = os.environ.get("RENDER_EXTERNAL_URL")

    if not BOT_TOKEN or not BASE_URL:
        raise RuntimeError("BOT_TOKEN or BASE_URL missing")

    init_db()

    threading.Thread(target=run_flask).start()

    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.bot_data["BASE_URL"] = BASE_URL

    application.add_handler(CommandHandler("start", start))
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler)
    )

    application.run_polling()


if __name__ == "__main__":
    main()