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

# ================== НАСТРОЙКИ ==================
BOT_TOKEN  = os.environ["8737526387:AAFia77yGJI0eRzMq7_M9Hzm8aSy0Yl332g"]
WEBAPP_URL = os.environ["https://ben-sys-lab.github.io/tictactoe-bot/"]      # https://НИК.github.io/tictactoe-bot/

ADMIN_ID   = 6369347678                     # ← ТВОЙ Telegram ID

CARD_NUMBER = "0000 0000 0000 0000"         # ← ЗАМЕНИ на свой номер карты
CARD_HOLDER = "Карякин Егор"                 # ← ЗАМЕНИ на имя получателя
BANK_NAME   = "ВТБ"              # ← ЗАМЕНИ на название банка
PRICE       = 15                            # Цена в рублях
# ===============================================

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def play_keyboard(paid: bool = False):
    url = WEBAPP_URL + ("?paid=1" if paid else "")
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🎮 Играть", web_app=WebAppInfo(url=url))
    ]])


def reqs_text():
    return (
        f"💳 <b>Реквизиты для оплаты {PRICE}₽</b>\n\n"
        f"🏦 Банк: <b>{BANK_NAME}</b>\n"
        f"👤 Получатель: <b>{CARD_HOLDER}</b>\n"
        f"💳 Карта: <code>{CARD_NUMBER}</code>\n\n"
        f"Переведи <b>{PRICE}₽</b> и нажми кнопку ниже — админ проверит и откроет доступ."
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args or []
    user = update.effective_user

    # пользователь пришёл из Mini App по кнопке "Оплатить"
    if args and args[0] == "pay":
        # 1. Показываем реквизиты пользователю
        await update.message.reply_text(
            reqs_text(),
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("📤 Я оплатил", callback_data="user_paid")
            ]])
        )

        # 2. Уведомляем админа с теми же реквизитами
        admin_text = (
            f"💰 <b>Запрос на оплату</b>\n\n"
            f"👤 Имя: {user.full_name}\n"
            f"🔗 Username: @{user.username or '—'}\n"
            f"🆔 ID: <code>{user.id}</code>\n\n"
            f"<b>Что он должен был перевести:</b>\n"
            f"🏦 {BANK_NAME}\n"
            f"👤 {CARD_HOLDER}\n"
            f"💳 <code>{CARD_NUMBER}</code>\n"
            f"💵 Сумма: <b>{PRICE}₽</b>\n\n"
            f"Проверь поступление и подтверди:"
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
        f"🎁 Первая игра — бесплатно.\n"
        f"💸 Дальше — {PRICE}₽ за новую игру."
    )
    if paid:
        text = "✅ Оплата подтверждена! Жми кнопку и играй."
    await update.message.reply_text(text, reply_markup=play_keyboard(paid))


async def on_user_paid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пользователь нажал 'Я оплатил' — напоминаем админу."""
    query = update.callback_query
    await query.answer("Отправлено админу на проверку ✅")

    user = update.effective_user
    await context.bot.send_message(
        ADMIN_ID,
        f"🔔 <b>Пользователь нажал 'Я оплатил'</b>\n\n"
        f"👤 {user.full_name}\n"
        f"🆔 <code>{user.id}</code>\n\n"
        f"Проверь поступление <b>{PRICE}₽</b> на карту и нажми /start-сообщение выше.",
        parse_mode="HTML"
    )
    await query.edit_message_text(
        "⏳ Заявка отправлена на проверку.\nОжидай подтверждения — придёт уведомление.",
    )


async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # обрабатываем только нажатия от админа
    if update.effective_user.id != ADMIN_ID:
        return

    action, user_id_str = query.data.split(":")
    user_id = int(user_id_str)

    if action == "approve":
        await query.edit_message_text(
            query.message.text + "\n\n✅ <b>РАЗРЕШЕНО</b>",
            parse_mode="HTML"
        )
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
    app.add_handler(CallbackQueryHandler(on_user_paid, pattern="^user_paid$"))
    app.add_handler(CallbackQueryHandler(on_callback, pattern="^(approve|deny):"))
    app.run_polling()


if __name__ == "__main__":
    main()
