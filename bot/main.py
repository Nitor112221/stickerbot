# Импортируем необходимые классы.
import logging
import os

import aiohttp
import requests
from PIL import Image

from data import db_session
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import Application, MessageHandler, filters, CommandHandler, ConversationHandler, CallbackContext
from config import BOT_TOKEN
from telegram import ReplyKeyboardMarkup

from data.models.template import Template
from data.models.user import User

# Запускаем логгирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.ERROR
)

logger = logging.getLogger(__name__)


async def start(update: Update, context: CallbackContext):
    await update.message.reply_text(f'Здравствуйте, я умею создавать стикерпаки по шаблонам, чтобы узнать подробнее о '
                                    f'моих возможностях напишите команду /help', reply_markup=ReplyKeyboardRemove())
    user_id = update.message.from_user.id
    db_sess = db_session.create_session()
    if not db_sess.query(User).filter(User.id_telegramm == user_id).first():
        user = User()
        user.id_telegramm = user_id
        user.role = 'user'
        db_sess.add(user)
        db_sess.commit()


async def help_command(update, context):
    await update.message.reply_text(f'Список доступных команд и их описание:\n'
                                    f'/start - запускает бота и выводит краткое описание его функционала\n'
                                    f'/help - выводит данный список команд\n'
                                    f'/change - запускает диалог смены выбранного шаблона\n'
                                    f'/stop_change - останавливает диалог смены выбранного шаблона\n'
                                    f'/create_template - создаёт новый пользовательский шаблон\n'
                                    f'/add_photo - включает режим добавления фото в шаблоны, чтобы выйти из него '
                                    f'напишите команду /stop_add_photo\n'
                                    f'/stop_add_photo - выключает режим добавления фото в шаблоны\n'
                                    f'/support - активирует диалог с поддержкой\n'
                                    f'Чтобы сделать стикерпак просто отправьте фотографию с лицом, и подождите пока бот'
                                    f' его обработает и применит выбранный вами шаблон '
                                    f'(убедитесь что режим добавления фото в шаблоны выключен)\n'
                                    f'Приятного пользование ботом')


async def change(update, context):
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id_telegramm == update.message.from_user.id).first()
    if not db_sess.query(Template).filter(Template.id_creator == user.id).all():
        templates = db_sess.query(Template).filter(Template.is_public == True).all()
        reply_keybord = [list(map(lambda x: x.title, templates[i:i + 3])) for i in range(0, len(templates), 3)]
        markup2 = ReplyKeyboardMarkup(reply_keybord, one_time_keyboard=True)
        await update.message.reply_text(f'Выбирите шаблон из списка', reply_markup=markup2)
        return 'общий'
    reply_keyboard = [['общий', 'приватный']]
    markup1 = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
    await update.message.reply_text(f'Выбирите список шаблонов', reply_markup=markup1)
    return 'выбор'


async def check_type_templates(update: Update, context):
    text = update.message.text
    if text == 'общий':
        db_sess = db_session.create_session()
        templates = db_sess.query(Template).filter(Template.is_public == True).all()
        reply_keybord = [list(map(lambda x: x.title, templates[i:i + 3])) for i in range(0, len(templates), 3)]
        markup2 = ReplyKeyboardMarkup(reply_keybord, one_time_keyboard=True)
        await update.message.reply_text(f'Выбирите шаблон из списка', reply_markup=markup2)
        return 'общий'
    elif text == 'приватный':
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.id_telegramm == update.message.from_user.id).first()
        templates = db_sess.query(Template).filter(Template.id_creator == user.id).all()
        reply_keybord = [list(map(lambda x: x.title, templates[i:i + 3])) for i in range(0, len(templates), 3)]
        markup3 = ReplyKeyboardMarkup(reply_keybord, one_time_keyboard=True)
        await update.message.reply_text(f'Выбирите шаблон из списка', reply_markup=markup3)
        return 'приватный'
    else:
        await update.message.reply_text(f'Извините, но я не понял какой из списков вам выдать, выбирете 1 из списка: '
                                        f'общий или приватный')
        return 'выбор'


async def back(update, context):
    await update.message.reply_text(f'Действие отменено', reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


async def general(update: Update, context):
    text = update.message.text
    db_sess = db_session.create_session()
    template = db_sess.query(Template).filter(Template.title == text, Template.is_public == True).first()
    if not template:
        await update.message.reply_text(f'Вы выброли не существующий/недоступный шаблон, пожалуйста, выберите '
                                        f'правильный шаблон из списка')
        return 'общий'
    user = db_sess.query(User).filter(User.id_telegramm == update.message.from_user.id).first()
    user.selected_template = template.id
    db_sess.commit()
    await update.message.reply_text(
        f'Ваш выбранный шаблон изменён, теперь это {template.title}, можете попробовать сгенерировать стикерпак',
        reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


async def privat(update: Update, context):
    text = update.message.text
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id_telegramm == update.message.from_user.id).first()
    template = db_sess.query(Template).filter(Template.title == text, Template.id_creator == user.id).first()
    if not template:
        await update.message.reply_text(f'Вы выброли не существующий/недоступный шаблон, пожалуйста, выберите '
                                        f'правильный шаблон из списка')
        return 'приватный'
    user.selected_template = template.id
    db_sess.commit()
    await update.message.reply_text(
        f'Ваш выбранный шаблон изменён, теперь это {template.title}, можете попробовать сгенерировать стикерпак')
    return ConversationHandler.END


async def create_template(update: Update, context):
    await update.message.reply_text(f'Введите название для шаблона')
    return 'проверка'


async def check_template_name(update: Update, context):
    text = update.message.text
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id_telegramm == update.message.from_user.id).first()
    if db_sess.query(Template).filter(Template.title == text).first():
        await update.message.reply_text(f'Такое название для шаблонов уже занято, придумайте другое название')
        return 'проверка'
    template = Template()
    template.title = text
    template.id_creator = user.id
    db_sess.add(template)
    db_sess.commit()
    await update.message.reply_text(f'Шаблон создан, не забудьте добавить в него фотографии')
    return ConversationHandler.END


async def get_photo(update: Update, file_name):
    file_id = update.message.photo[-1]['file_id']
    async with aiohttp.ClientSession() as session:
        async with session.get(f'https://api.telegram.org/bot{BOT_TOKEN}/getFile?file_id={file_id}') as resp:
            file_path = resp.json()['result']['file_path']
    img = Image.open(requests.get(f'https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}', stream=True).raw)
    img.save(f'photo/{file_name}.png')


def main():
    if not os.path.exists('db'):
        os.makedirs('db')
    if not os.path.exists('photo'):
        os.makedirs('photo')
    db_session.global_init("db/bot.db")
    db_sess = db_session.create_session()
    if not db_sess.query(User).all():
        user = User()
        user.id_telegramm = '5685707883'
        user.role = 'admin'
        db_sess.add(user)
        db_sess.commit()
        template = Template()
        template.title = 'FirstTemplate'
        template.is_public = True
        template.id_creator = user.id
        db_sess.add(template)
        db_sess.commit()

    application = Application.builder().token(BOT_TOKEN).build()

    change_conversation = ConversationHandler(
        entry_points=[CommandHandler('change', change)],
        states={
            'выбор': [MessageHandler(filters.TEXT & ~filters.COMMAND, check_type_templates)],
            'общий': [MessageHandler(filters.TEXT & ~filters.COMMAND, general)],
            'приватный': [MessageHandler(filters.TEXT & ~filters.COMMAND, privat)]
        },
        fallbacks=[CommandHandler('back', back)]
    )

    create_template_conversation = ConversationHandler(
        entry_points=[CommandHandler('create_template', create_template)],
        states={'проверка': [MessageHandler(filters.TEXT & ~filters.COMMAND, check_template_name)]},
        fallbacks=[CommandHandler('back', back)]
    )
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(change_conversation)
    application.add_handler(create_template_conversation)

    application.run_polling()


if __name__ == '__main__':
    main()
