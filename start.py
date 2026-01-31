from flask import Flask, request
import telegram
import os

TOKEN = os.environ.get("BOT_TOKEN")
BOT = telegram.Bot(token=TOKEN)

app = Flask(__name__)

@app.route(f"/{TOKEN}", methods=["POST"])
def respond():
    try:
        update = telegram.Update.de_json(request.get_json(force=True), BOT)
        chat_id = update.message.chat.id
        text = update.message.text

        if text == "/start":
            BOT.send_message(chat_id=chat_id, text="Hello! Your bot is working ✅")
    except Exception as e:
        print(e)
    return "ok"

@app.route("/")
def index():
    return "Bot is running ✅"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))