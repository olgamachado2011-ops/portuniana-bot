import os
import json
import requests
from flask import Flask, request, Response

app = Flask(__name__)

TOKEN   = os.environ.get("BOT_TOKEN", "ВСТАВЬ_ТОКЕН_СЮДА")
API     = f"https://api.telegram.org/bot{TOKEN}"
CHANNEL = "https://t.me/portuniana"
PDF     = os.path.join(os.path.dirname(__file__), "ebook.pdf")


def send_document(chat_id):
    caption = (
        "🎁 *60 фраз на каждый день*\n\n"
        "Транскрипция, живые примеры и мини-тесты. "
        "Приятного изучения! 🇵🇹"
    )
    with open(PDF, "rb") as f:
        requests.post(
            f"{API}/sendDocument",
            data={"chat_id": chat_id, "caption": caption, "parse_mode": "Markdown"},
            files={"document": ("60_фраз_на_каждый_день.pdf", f, "application/pdf")}
        )


def send_channel_invite(chat_id):
    keyboard = {
        "inline_keyboard": [[
            {"text": "📢 Перейти в канал Portuniana", "url": CHANNEL}
        ]]
    }
    requests.post(f"{API}/sendMessage", json={
        "chat_id": chat_id,
        "text": (
            "А ещё — подписывайся на канал *Portuniana* 🇵🇹\n\n"
            "Каждый день живой португальский: слова, фразы, "
            "разговорные ситуации — без скуки и сухой грамматики."
        ),
        "parse_mode": "Markdown",
        "reply_markup": keyboard
    })


@app.route(f"/webhook/{TOKEN}", methods=["POST"])
def webhook():
    update = request.get_json(silent=True) or {}
    message = update.get("message", {})
    text    = message.get("text", "")
    chat_id = message.get("chat", {}).get("id")

    if chat_id and text.startswith("/start"):
        send_document(chat_id)
        send_channel_invite(chat_id)

    return Response("ok", status=200)


@app.route("/")
def index():
    return "Portuniana bot is running 🇵🇹", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
