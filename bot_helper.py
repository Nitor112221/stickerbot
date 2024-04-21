from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, filters, CallbackContext, Application
import logging

# Настройте логгирование
logging.basicConfig(level=logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler())

# Токен бота и админа
BOT_TOKEN = "6970880601:AAFrg2Rc8oOrzaFM4yedFObk0D67JqGJZmw"
ADMIN_ID = 5685707883


# Функция обработки команды /support
async def support(update: Update, context: CallbackContext) -> None:
    # Отключаем режим поддержки для бота
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Режим поддержки включен. Ваше сообщение будет передано админу.")

    # Отправляем сообщение админу
    await context.bot.send_message(chat_id=ADMIN_ID, text=f"Новое сообщение от {update.effective_user.first_name}:\n{update.effective_message.text}")


# Обработчик команд
async def start(update: Update, context: CallbackContext) -> None:
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Привет! Я бот для обработки запросов. Чтобы вызвать режим поддержки, отправьте команду /support.")


# Обработчик текстовых сообщений
async def handle_text(update: Update, context: CallbackContext) -> None:
    if update.effective_chat.id == ADMIN_ID:
        message = update.message.reply_to_message

        if message:
            text = message.text
            await context.bot.send_message(chat_id=int(text.split()[0]),
                                           text=f"Ответ от админа: {update.effective_user.first_name}:\n{update.effective_message.text}")
    # Проверяем, была ли отправлена команда /support
    if update.effective_message.text.startswith("/support"):
        await support(update, context)
    else:
        # Если нет, просто отправляем сообщение админу
        if update.effective_user.id != ADMIN_ID:
            await context.bot.send_message(chat_id=ADMIN_ID, text=f"{update.effective_user.id} Новое сообщение от {update.effective_user.first_name}:\n{update.effective_message.text}")


# Инициализация бота
def main() -> None:
    application = Application.builder().token(BOT_TOKEN).build()

    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT, handle_text))
    application.run_polling()


if __name__ == "__main__":
    main()
