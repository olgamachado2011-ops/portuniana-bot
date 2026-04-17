import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler

# ─── НАСТРОЙКИ ───────────────────────────────────────────────
TOKEN   = os.environ.get("BOT_TOKEN", "ВСТАВЬ_ТОКЕН_СЮДА")
PDF     = "ebook.pdf"          # имя PDF-файла в этой же папке
CHANNEL = "https://t.me/portuniana"
# ─────────────────────────────────────────────────────────────

def start(update, context):
    chat_id = update.effective_chat.id

    # 1. Отправляем PDF
    try:
        with open(PDF, "rb") as f:
            context.bot.send_document(
                chat_id=chat_id,
                document=f,
                filename="60_фраз_на_каждый_день.pdf",
                caption=(
                    "🎁 *60 фраз на каждый день*\n\n"
                    "Транскрипция, живые примеры и мини-тесты. "
                    "Приятного изучения! 🇵🇹"
                ),
                parse_mode="Markdown"
            )
    except FileNotFoundError:
        context.bot.send_message(
            chat_id=chat_id,
            text="⚠️ PDF-файл не найден. Напишите @portuniana — пришлю вручную."
        )
        return

    # 2. Следующее сообщение — приглашение в канал
    keyboard = [[InlineKeyboardButton("📢 Перейти в канал Portuniana", url=CHANNEL)]]
    context.bot.send_message(
        chat_id=chat_id,
        text=(
            "А ещё — подписывайся на канал *Portuniana* 🇵🇹\n\n"
            "Каждый день живой португальский: слова, фразы, "
            "разговорные ситуации — без скуки и сухой грамматики."
        ),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


def main():
    updater = Updater(TOKEN)
    updater.dispatcher.add_handler(CommandHandler("start", start))
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
