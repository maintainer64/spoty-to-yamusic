import logging

from telegram import Update
from telegram.ext import CommandHandler, CallbackContext, ApplicationBuilder

import logic
import queries
from config import TG_BOT

# Логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


# Команда /set_yandex_token
async def set_yandex_token(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    token = context.args[0] if context.args else None

    if not token:
        await update.message.reply_text("Пожалуйста, укажите токен. Пример: /set_yandex_token <токен>")
        return

    with queries.get_db() as db:
        user = queries.get_or_create_user_model(user_id=str(user_id), db=db)
        user.yandex_access_token = token
        db.add(user)
        db.commit()
    await update.message.reply_text("Токен успешно установлен.")


# Команда /list
async def list_tasks(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    with queries.get_db() as db:
        user = queries.get_or_create_user_model(user_id=str(user_id), db=db)

    if not user.yandex_access_token:
        await update.message.reply_text("Токен не установлен. Используйте /set_yandex_token <токен>")
        return

    with queries.get_db() as db:
        relations = queries.get_list_relations_tracks(user_id=str(user_id), db=db)
    await update.message.reply_text(relations or "Ещё ничего нет")


# Команда /help
async def help(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "/add добавляет новую задачу\n/list показывает 5 последних задач\n/set_yandex_token устанавливает токен"
    )


# Команда /add
async def add_album(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    with queries.get_db() as db:
        user = queries.get_or_create_user_model(user_id=str(user_id), db=db)
    token = user.yandex_access_token
    url = context.args[0] if context.args else None

    if not token:
        await update.message.reply_text("Токен не установлен. Используйте /set_yandex_token <токен>")
        return

    if not url:
        await update.message.reply_text("Пожалуйста, укажите URL. Пример: /add <url>")
        return

    try:
        logic.add_task_album(user_id=str(user_id), url=url)
        await update.message.reply_text("Создана задача на перенос треков")
    except Exception as err:
        await update.message.reply_text(f"Произошла ошибка задача {err}")
        raise


# Основная функция
def main():
    # Укажите ваш токен Telegram-бота
    app = ApplicationBuilder().token(TG_BOT).build()

    # Регистрация команд
    app.add_handler(CommandHandler("set_yandex_token", set_yandex_token))
    app.add_handler(CommandHandler("list", list_tasks))
    app.add_handler(CommandHandler("add", add_album))
    app.add_handler(CommandHandler("help", help))
    app.add_handler(CommandHandler("start", help))

    # Запуск бота
    app.run_polling()


if __name__ == '__main__':
    main()
