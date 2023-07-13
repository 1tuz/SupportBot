import logging
from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from dotenv import load_dotenv
import os

# Загрузка переменных окружения из файла .env
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=os.getenv('TELEGRAM_TOKEN'))
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


class SupportForm(StatesGroup):
    name = State()
    phone = State()
    problem = State()
    comment = State()


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    # Запрос имени у пользователя
    await message.answer("Добро пожаловать в бота технической поддержки! Пожалуйста, введите ваше имя:")
    await SupportForm.name.set()


@dp.message_handler(state=SupportForm.name)
async def process_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text
    # Запрос номера телефона у пользователя
    await message.answer("Отлично! Теперь введите ваш номер телефона:")
    await SupportForm.phone.set()


@dp.message_handler(state=SupportForm.phone)
async def process_phone(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['phone'] = message.text
    # Предложение выбрать одну из проблемных категорий
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    keyboard.add("Проблемы с сайтом", "Проблемы с регистрацией/авторизацией", "Проблемы с оплатой", "Другое")
    await message.answer("Пожалуйста, выберите одну из следующих категорий проблем:", reply_markup=keyboard)
    await SupportForm.problem.set()


@dp.message_handler(state=SupportForm.problem)
async def process_problem(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['problem'] = message.text
    # Запрос комментария у пользователя
    await message.answer("Опишите вашу проблему подробнее или оставьте комментарий:")
    await SupportForm.comment.set()


@dp.message_handler(state=SupportForm.comment)
async def process_comment(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['comment'] = message.text
        name = data['name']
        phone = data['phone']
        problem = data['problem']
        comment = data['comment']
        # Отправка собранной информации в отдельный канал
        channel_id = os.getenv('SUPPORT_CHANNEL_ID')
        await bot.send_message(channel_id, f"Имя: {name}\nТелефон: {phone}\nПроблема: {problem}\nКомментарий: {comment}")
    await state.finish()
    # Благодарность пользователю и возврат к началу диалога
    await message.answer("Спасибо за предоставленную информацию и комментарий! "
                         "Начнем новую сессию. Пожалуйста, введите ваше имя:")
    await SupportForm.name.set()


@dp.message_handler(commands=['restart'])
async def restart(message: types.Message, state: FSMContext):
    # Сброс состояния пользователя и возврат к началу диалога
    await state.finish()
    await message.answer("Начнем новую сессию. Пожалуйста, введите ваше имя:")
    await SupportForm.name.set()


if __name__ == '__main__':
    # Запуск бота
    executor.start_polling(dp, skip_updates=True)