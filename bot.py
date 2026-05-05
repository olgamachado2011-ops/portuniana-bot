import os
import json
import requests
import stripe
from flask import Flask, request, Response

app = Flask(__name__)

# ── Env vars ────────────────────────────────────────────────────
TOKEN                 = os.environ.get("BOT_TOKEN", "")
STRIPE_SECRET_KEY     = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
STRIPE_PRICE_ID       = os.environ.get("STRIPE_PRICE_ID", "")   # заполним ниже
PRO_CHANNEL_ID        = os.environ.get("PRO_CHANNEL_ID", "")    # numeric ID @portuniana_pro
RENDER_URL            = os.environ.get("RENDER_URL", "https://portuniana-bot.onrender.com")

API      = f"https://api.telegram.org/bot{TOKEN}"
CHANNEL  = "https://t.me/globalvillage_live"
PDF      = os.path.join(os.path.dirname(__file__), "ebook.pdf")

stripe.api_key = STRIPE_SECRET_KEY


# ── Helpers ─────────────────────────────────────────────────────
def send(chat_id, text, keyboard=None, parse_mode="Markdown"):
    payload = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}
    if keyboard:
        payload["reply_markup"] = keyboard
    requests.post(f"{API}/sendMessage", json=payload)


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
    keyboard = {"inline_keyboard": [[
        {"text": "🌍 Перейти в Global Village", "url": CHANNEL}
    ]]}
    send(chat_id,
         "Подписывайся на *Global Village* 🌍\n\n"
         "Жизнь, язык и Португалия — каждый день.",
         keyboard)


def create_pro_invite():
    """Создаёт одноразовую инвайт-ссылку в @portuniana_pro."""
    resp = requests.post(f"{API}/createChatInviteLink", json={
        "chat_id": PRO_CHANNEL_ID,
        "member_limit": 1,
        "creates_join_request": False
    })
    data = resp.json()
    return data.get("result", {}).get("invite_link")


def create_stripe_session(chat_id):
    """Создаёт Stripe Checkout Session и возвращает URL."""
    session = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": STRIPE_PRICE_ID, "quantity": 1}],
        client_reference_id=str(chat_id),
        success_url=f"{RENDER_URL}/payment-success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{RENDER_URL}/payment-cancel",
        metadata={"telegram_chat_id": str(chat_id)}
    )
    return session.url


# ── Telegram webhook ─────────────────────────────────────────────
@app.route(f"/webhook/{TOKEN}", methods=["POST"])
def webhook():
    update = request.get_json(silent=True) or {}
    message = update.get("message", {})
    text    = message.get("text", "")
    chat_id = message.get("chat", {}).get("id")

    if not chat_id:
        return Response("ok", status=200)

    if text.startswith("/start pro") or text.startswith("/pro"):
        handle_pro(chat_id)

    elif text.startswith("/start"):
        send_document(chat_id)
        send_channel_invite(chat_id)

    return Response("ok", status=200)


def handle_pro(chat_id):
    try:
        url = create_stripe_session(chat_id)
        keyboard = {"inline_keyboard": [[
            {"text": "💳 Оплатить €6/мес", "url": url}
        ]]}
        send(chat_id,
             "🇵🇹 *Portuniana Pro — €6/мес*\n\n"
             "Каждую неделю:\n"
             "• Полный урок с примерами из жизни\n"
             "• Упражнение + аудио-разбор\n"
             "• Личная обратная связь\n\n"
             "После оплаты получишь ссылку в закрытую группу 👇",
             keyboard)
    except Exception as e:
        send(chat_id, "Что-то пошло не так. Напиши @portuniana — разберёмся 🙏")
        print(f"Stripe error: {e}")


# ── Stripe webhook ───────────────────────────────────────────────
@app.route("/stripe-webhook", methods=["POST"])
def stripe_webhook():
    payload    = request.data
    sig_header = request.headers.get("Stripe-Signature", "")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except Exception as e:
        print(f"Webhook error: {e}")
        return Response("error", status=400)

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        chat_id = session.get("metadata", {}).get("telegram_chat_id")
        if chat_id:
            invite_link = create_pro_invite()
            if invite_link:
                keyboard = {"inline_keyboard": [[
                    {"text": "🔐 Войти в Portuniana Pro", "url": invite_link}
                ]]}
                send(int(chat_id),
                     "✅ *Оплата прошла!*\n\n"
                     "Добро пожаловать в Portuniana Pro 🇵🇹\n"
                     "Нажми кнопку ниже чтобы войти в группу:",
                     keyboard)

    return Response("ok", status=200)


# ── Страницы после оплаты ────────────────────────────────────────
@app.route("/payment-success")
def payment_success():
    return """
    <html><body style="font-family:sans-serif;text-align:center;padding:60px">
    <h2>✅ Оплата прошла!</h2>
    <p>Вернись в Telegram — там уже ждёт ссылка в группу.</p>
    </body></html>
    """


@app.route("/payment-cancel")
def payment_cancel():
    return """
    <html><body style="font-family:sans-serif;text-align:center;padding:60px">
    <h2>Оплата отменена</h2>
    <p>Если возникли вопросы — напиши <a href="https://t.me/portuniana">@portuniana</a></p>
    </body></html>
    """


@app.route("/")
def index():
    return "Portuniana bot is running 🇵🇹", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
