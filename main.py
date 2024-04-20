# Импортируем необходимые классы.
import logging

from telegram import Update, ReplyKeyboardRemove
from telegram.ext import Application, MessageHandler, filters, CommandHandler, ConversationHandler
from config import BOT_TOKEN
from telegram import ReplyKeyboardMarkup

# Запускаем логгирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

logger = logging.getLogger(__name__)


async def start(update, context):
    await update.message.reply_text(f'Здравствуйте, я умею создавать стикерпаки по шаблонам, чтобы узнать подробнее о '
                                    f'моих возможностях напишите команду /help')


def main():
    application = Application.builder().token(BOT_TOKEN).build()
    text_handler = CommandHandler('start', start)

    application.add_handler(text_handler)

    application.run_polling()


if __name__ == '__main__':
    main()
