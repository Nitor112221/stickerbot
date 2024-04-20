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


async def help_command(update, context):
    await update.message.reply_text(f'Список доступных команд и их описание:\n'
                                    f'/start - запускает бота и выводит краткое описание его функционала\n'
                                    f'/help - выводит данный список команд\n'
                                    f'/change - меняет выбранный шаблон\n'
                                    f'/create_sample - создаёт новый пользовательский шаблон\n'
                                    f'/add_photo - включает режим добавления фото в шаблоны, чтобы выйти из него '
                                    f'напишите команду /stop_add_photo\n'
                                    f'/stop_add_photo - выключает режим добавления фото в шаблоны\n'
                                    f'/support - активирует диалог с поддержкой\n'
                                    f'Чтобы сделать стикерпак просто отправьте фотографию с лицом, и подождите пока бот'
                                    f' его обработает и применит выбранный вами шаблон '
                                    f'(убедитесь что режим добавления фото в шаблоны выключен)\n'
                                    f'Приятного пользование ботом')


def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help_command))

    application.run_polling()


if __name__ == '__main__':
    main()
