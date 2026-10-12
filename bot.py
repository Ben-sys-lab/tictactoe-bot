import os
import logging
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup,
    WebAppInfo
)
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes
)

BOT_TOKEN  = os.environ["8737526387:AAFia77yGJI0eRzMq7_M9Hzm8aSy0Yl332g"]
WEBAPP_URL = os.environ["https://ben-sys-lab.github.io/tictactoe-bot/"]   # https://user.github.io/repo/
ADMIN_ID   = 6369347678                  # твой Telegram ID

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def play_keyboard(paid: bool = False):
    url = WEBAPP_URL + ("?paid=1" if paid else "")
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🎮 Играть", web_app=WebAppInfo(url=url))
    ]])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args or []
    user = update.effective_user

    # пришли по кнопке "Оплатить"
    if args and args[0] == "pay":
        text_user = (
            "💳 Чтобы сыграть ещё раз, переведи 15₽ и напиши об этом админу.\n\n"
            "После проверки ты получишь уведомление."
        )
        await update.message.reply_text(text_user)

        # шлём уведомление тебе (админу)
        admin_text = (
            f"💰 <b>Запрос на оплату</b>\n\n"
            f"👤 {user.full_name}\n"
            f"🔗 @{user.username or '—'}\n"
            f"🆔 <code>{user.id}</code>\n\n"
            f"Подтверди оплату 15₽:"
        )
        kb = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ Разрешить", callback_data=f"approve:{user.id}"),
            InlineKeyboardButton("❌ Отказано",  callback_data=f"deny:{user.id}")
        ]])
        await context.bot.send_message(ADMIN_ID, admin_text, parse_mode="HTML", reply_markup=kb)
        return

    # обычный /start
    paid = bool(args and args[0] == "paid")
    text = (
        "Привет! Это крестики-нолики против бота 🤖\n\n"
        "🎁 Первая игра — бесплатно.\n"
        "💸 Дальше — 15₽ за новую игру."
    )
    if paid:
        text = "✅ Оплата подтверждена! Жми кнопку и играй."
    await update.message.reply_text(text, reply_markup=play_keyboard(paid))


async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if update.effective_user.id != ADMIN_ID:
        return  # игнорируем чужие нажатия

    action, user_id_str = query.data.split(":")
    user_id = int(user_id_str)

    if action == "approve":
        # уведомляем админа
        await query.edit_message_text(
            query.message.text + "\n\n✅ <b>РАЗРЕШЕНО</b>",
            parse_mode="HTML"
        )
        # уведомляем пользователя + кнопка с оплаченной игрой
        try:
            await context.bot.send_message(
                user_id,
                "✅ Оплата подтверждена! Нажми кнопку ниже и играй.",
                reply_markup=play_keyboard(paid=True),
            )
        except Exception as e:
            logging.error(f"Не смог уведомить {user_id}: {e}")

    elif action == "deny":
        await query.edit_message_text(
            query.message.text + "\n\n❌ <b>ОТКАЗАНО</b>",
            parse_mode="HTML"
        )
        try:
            await context.bot.send_message(
                user_id,
                "❌ Платёж не подтверждён. Если это ошибка — свяжись с админом.",
            )
        except Exception as e:
            logging.error(f"Не смог уведомить {user_id}: {e}")


def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.run_polling()


if __name__ == "__main__":
    main()
