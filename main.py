# Импортируем необходимые классы.
import io
import logging
import os
import pathlib
import random

import aiohttp
import requests
from PIL import Image

from FaceSwap import FaceSwapper
from data import db_session
from telegram import Update, ReplyKeyboardRemove, InputFile, InputMediaPhoto, InputMedia, InputSticker
from telegram.ext import Application, MessageHandler, filters, CommandHandler, ConversationHandler, CallbackContext
from config import BOT_TOKEN, ADMIN_ID
from telegram import ReplyKeyboardMarkup

from data.models.photo import Photo
from data.models.template import Template
from data.models.user import User

# Запускаем логгирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.WARNING
)

logger = logging.getLogger(__name__)


async def start(update: Update, context: CallbackContext):
    reply_keyboard = [['/help']]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)
    await update.message.reply_text(f'Здравствуйте, я умею создавать стикерпаки по шаблонам, чтобы узнать подробнее о '
                                    f'моих возможностях напишите команду /help', reply_markup=markup)
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
        await update.message.reply_text(f'Выберите шаблон из списка', reply_markup=markup2)
        return 'общий'
    reply_keyboard = [['общий', 'приватный']]
    markup1 = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)
    await update.message.reply_text(f'Выберите список шаблонов', reply_markup=markup1)
    return 'выбор'


async def check_type_templates(update: Update, context):
    text = update.message.text
    if text == 'общий':
        db_sess = db_session.create_session()
        templates = db_sess.query(Template).filter(Template.is_public == True).all()
        reply_keybord = [list(map(lambda x: x.title, templates[i:i + 3])) for i in range(0, len(templates), 3)]
        markup2 = ReplyKeyboardMarkup(reply_keybord, one_time_keyboard=True)
        await update.message.reply_text(f'Выберите шаблон из списка', reply_markup=markup2)
        return 'общий'
    elif text == 'приватный':
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.id_telegramm == update.message.from_user.id).first()
        templates = db_sess.query(Template).filter(Template.id_creator == user.id).all()
        reply_keybord = [list(map(lambda x: x.title, templates[i:i + 3])) for i in range(0, len(templates), 3)]
        markup3 = ReplyKeyboardMarkup(reply_keybord, one_time_keyboard=True)
        await update.message.reply_text(f'Выберите шаблон из списка', reply_markup=markup3)
        return 'приватный'
    else:
        await update.message.reply_text(f'Извините, но я не понял какой из списков вам выдать, выберите 1 из списка: '
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
        await update.message.reply_text(f'Вы выбрали несуществующий/недоступный шаблон, пожалуйста, выберите '
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
        await update.message.reply_text(f'Вы выбрали не существующий/недоступный шаблон, пожалуйста, выберите '
                                        f'правильный шаблон из списка')
        return 'приватный'
    user.selected_template = template.id
    db_sess.commit()
    await update.message.reply_text(
        f'Ваш выбранный шаблон изменён, теперь это {template.title}, можете попробовать сгенерировать стикерпак')
    await update.message.reply_text(
        'Для генерации стикеров отправьте ваше фото. На нем отчетливо должно быть видно ваше лицо.')
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
    user.selected_template = template.id
    db_sess.add(user)
    db_sess.commit()

    reply_markup = [['/add_photo']]
    markup = ReplyKeyboardMarkup(reply_markup, one_time_keyboard=True)

    await update.message.reply_text(f'Шаблон создан, не забудьте добавить в него фотографии', reply_markup=markup)
    return ConversationHandler.END


async def save_image(update, context):
    '''Save all img to the database and folder'''
    user = update.message.from_user.id
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id_telegramm == user).first()
    if user.is_add_photo:
        if db_sess.query(Template).filter(Template.id == user.selected_template).first().id_creator == user.id:
            # Create images record in database
            # if we don't know last id we won't create title for new file, but we don't know it before commit, so we have to
            # check current id with other ways like this
            img = Photo()
            img.id_template = user.selected_template
            db_sess.add(img)
            db_sess.commit()
            await get_photo(update, img.id)
            await update.message.reply_text(f'Ваше фото успешно загружено')
        else:
            await update.message.reply_text(f'У вас нет доступа редактировать данный шаблон')
            await stop_add_photo(update, context, send_message=False)
    else:
        await create_stickers_set(update, context)


async def get_photo(update, file_name):
    file_id = update.message.photo[-1].file_id
    async with aiohttp.ClientSession() as session:
        # Retrieve the file_path from Telegram's getFile API
        async with session.get(f'https://api.telegram.org/bot{BOT_TOKEN}/getFile?file_id={file_id}') as resp:
            data = await resp.json()
            file_path = data['result']['file_path']

        # Retrieve the actual file using the file_path provided by Telegram
        async with session.get(f'https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}') as resp:
            if resp.status == 200:
                file_data = await resp.read()

                # Use BytesIO to convert bytes data to a file-like object
                img = Image.open(io.BytesIO(file_data))
                img.save(f'photo/{file_name}.png')
            else:
                print(f"Error retrieving file: {resp.status}")


async def add_photo(updade: Update, context: CallbackContext):
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id_telegramm == updade.message.from_user.id).first()
    user.is_add_photo = True
    db_sess.commit()
    template = db_sess.query(Template).filter(Template.id == user.selected_template).first().title

    reply_keyboard = [['/stop_add_photo']]
    markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)

    await updade.message.reply_text(f'Теперь каждое отправленное вами фото будет попадать в шаблон {template}\n'
                                    f'Чтобы выйти из режима добавления фото в шаблон напишите команду /stop_add_photo',
                                    reply_markup=markup)


async def stop_add_photo(updade: Update, context: CallbackContext, send_message=True):
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id_telegramm == updade.message.from_user.id).first()
    user.is_add_photo = False
    db_sess.commit()
    if send_message:
        await updade.message.reply_text(
            f'Вы выключили режим добавления фото в шаблон, теперь все далее отправленные фото '
            f'будут преобразованы в стикерпаки', reply_markup=ReplyKeyboardRemove())


async def support(update: Update, context: CallbackContext):
    # Отключаем режим поддержки для бота
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text="Режим поддержки включен. Следующее ваше сообщение отправиться администратору")
    return 1


# Обработчик текстовых сообщений
async def handle_text(update: Update, context: CallbackContext):
    if update.effective_chat.id == ADMIN_ID:
        message = update.message.reply_to_message

        if message:
            text = message.text
            await context.bot.send_message(chat_id=int(text.split()[0]),
                                           text=f"Ответ от админа: {update.effective_user.first_name}:\n{update.effective_message.text}")
    else:
        # Если нет, просто отправляем сообщение админу
        if update.effective_user.id != ADMIN_ID:
            await context.bot.send_message(chat_id=ADMIN_ID,
                                           text=f"{update.effective_user.id} Новое сообщение от {update.effective_user.first_name}:\n{update.effective_message.text}")
    return 1


async def support(update: Update, context: CallbackContext):
    # Отключаем режим поддержки для бота
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text="Режим поддержки включен. Следующее ваше сообщение отправиться администратору")
    return 1


async def download_photo(file_id, path):
    # Функция для скачивания фотографии по file_id
    async with aiohttp.ClientSession() as session:
        # Получаем путь к файлу фотографии
        async with session.get(f'https://api.telegram.org/bot{BOT_TOKEN}/getFile?file_id={file_id}') as response:
            response_data = await response.json()
            file_path = response_data['result']['file_path']

        # Скачиваем фотографию
        photo_url = f'https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}'
        async with session.get(photo_url) as photo_response:
            if photo_response.status == 200:
                # Сохраняем фотографию локально
                photo_data = await photo_response.read()
                with open(path, 'wb') as photo_file:
                    photo_file.write(photo_data)
                return path
            else:
                raise Exception('Не удалось скачать фотографию.')


def optimize_image(image_path, max_size=(512, 512), quality=85):
    """
    Уменьшает размер изображения и сохраняет его с определенным качеством.
    """
    with Image.open(image_path) as img:
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        img.save(image_path, format='PNG', optimize=True, quality=quality)


async def create_stickers_set(update, context):
    bot = context.bot
    user = update.message.from_user
    db_sess = db_session.create_session()
    user = db_sess.query(User).filter(User.id_telegramm == update.message.from_user.id).first()
    photos_paths = db_sess.query(Photo.id).join(Template, Template.id == Photo.id_template).filter(
        Template.id == user.selected_template).all()

    user = update.message.from_user
    sticker_pack_name = f"{user.username + str(random.randint(1, 10 ** 20))}_by_{bot.username}"
    sticker_pack_title = f"{user.username}'s Sticker Pack"

    file_id = update.message.photo[-1].file_id
    user_photo_path = f'user_images/{user.username}_{file_id}.png'
    user_photo_path = await download_photo(file_id, user_photo_path)

    if not os.path.exists(user_photo_path):
        await update.message.reply_text('Не удалось скачать вашу фотографию.')
        return
    first_photo_path = 'photo/' + str(photos_paths[0][0]) + '.png' if photos_paths else None

    if not first_photo_path:
        await update.message.reply_text('Нет фотографий для создания стикерпака.')
        return

    i = 0
    try:
        # Create face swapped image and save it
        face_swapper = FaceSwapper(first_photo_path, user_photo_path)
        face_swapper.save_image(f'user_images/{user.id}_{i}.png')

        optimize_image(f'user_images/{user.id}_{i}.png')
        with open(f'user_images/{user.id}_{i}.png', 'rb') as sticker_file:
            # media = InputMedia('photo', f'user_images/{user.id}_{i}.png')
            await bot.create_new_sticker_set(
                user_id=user.id,
                name=sticker_pack_name,
                title=sticker_pack_title,
                stickers=[InputSticker(sticker_file, ['🍅'], 'static')],

            )
            await update.message.reply_text('Стикерпак успешно создан!')
            # await bot.send_sticker(chat_id=update.message.chat_id, sticker=file_id)

            i += 1
            for photo_id in photos_paths[1:]:
                photo_path = f'photo/{photo_id[0]}.png'
                face_swapper = FaceSwapper(photo_path, user_photo_path)
                face_swapper.save_image(f'user_images/{user.id}_{i}.png')
                optimize_image(f'user_images/{user.id}_{i}.png')

                with open(f'user_images/{user.id}_{i}.png', 'rb') as sticker_file:
                    await bot.add_sticker_to_set(
                        user_id=user.id,
                        name=sticker_pack_name,
                        sticker=InputSticker(sticker_file, ['🍅'], 'static')
                    )

                i += 1
            await update.message.reply_text('Все стикеры добавлены в стикерпак!')

            sticker_set = await bot.get_sticker_set(sticker_pack_name)
            stickers = sticker_set.stickers
            for sticker in stickers:
                sticker_id = sticker.file_id
                break

            await bot.send_sticker(chat_id=update.message.chat_id, sticker=sticker_id)

    except Exception as e:
        logger.error(e)
        await update.message.reply_text('Произошла ошибка при создании стикерпака.')
    finally:
        os.remove(user_photo_path)


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
    support_conversation = ConversationHandler(
        entry_points=[CommandHandler('support', support)],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text)]
        },
        fallbacks=[CommandHandler('back', back)]
    )
    application.add_handler(change_conversation)
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(MessageHandler(filters.PHOTO, save_image))
    application.add_handler(CommandHandler('add_photo', add_photo))
    application.add_handler(CommandHandler('stop_add_photo', stop_add_photo))
    application.add_handler(support_conversation)
    application.add_handler(create_template_conversation)

    application.run_polling()


if __name__ == '__main__':
    main()
