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
    await message.answer("Отлично! Теперь введите ваш номер телефона, начиная с '+7':")
    await SupportForm.phone.set()


@dp.message_handler(state=SupportForm.phone)
async def process_phone(message: types.Message, state: FSMContext):
    phone_number = message.text
    if not phone_number.startswith('+7'):
        await message.answer("Пожалуйста, введите номер телефона, начиная с '+7'. Попробуйте еще раз:")
        return
    async with state.proxy() as data:
        data['phone'] = phone_number
    # Предложение выбрать одну из проблемных категорий
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    keyboard.add("Проблемы с сайтом", "Проблемы с регистрацией/авторизацией", "Проблемы с оплатой", "Другое")
    await message.answer("Пожалуйста, выберите одну из следующих категорий проблем:", reply_markup=keyboard)
    await SupportForm.next()  # Изменено состояние на next


@dp.message_handler(state=SupportForm.problem)
async def process_problem(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['problem'] = message.text
    if message.text == "Другое":
        # Запрос комментария у пользователя только при выборе категории "Другое"
        await message.answer("Опишите вашу проблему подробнее или оставьте комментарий:")
        await SupportForm.comment.set()
    else:
        # Сразу завершаем диалог при выборе других категорий
        await state.finish()
        name = data['name']
        phone = data['phone']
        problem = data['problem']
        username = "@" + message.from_user.username if message.from_user.username else ""
        # Отправка собранной информации в отдельный канал
        channel_id = os.getenv('SUPPORT_CHANNEL_ID')
        await bot.send_message(channel_id, f"Имя: {name}\nТелефон: +7{phone}\nПроблема: {problem}\nНикнейм пользователя: {username}")
        await message.answer("Спасибо за предоставленную информацию! Ваша заявка передана специалистам, которые займутся ей в ближайшее время!"
                             "\n\nЧтобы создать новую заявку, нажмите /start")


@dp.message_handler(state=SupportForm.comment)
async def process_comment(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['comment'] = message.text
        name = data['name']
        phone = data['phone']
        problem = data['problem']
        comment = data['comment']
        username = "@" + message.from_user.username if message.from_user.username else ""
        # Отправка собранной информации в отдельный канал
        channel_id = os.getenv('SUPPORT_CHANNEL_ID')
        await bot.send_message(channel_id, f"Имя: {name}\nТелефон: {phone}\nПроблема: {problem}\nКомментарий: {comment}\nНикнейм пользователя: {username}")
        await message.answer("Спасибо за предоставленную информацию и комментарий! "
                             "Ваша заявка передана специалистам, которые займутся ей в ближайшее время!"
                             "\n\nЧтобы создать новую заявку, нажмите /start")
    await state.finish()


@dp.message_handler(commands=['restart'])
async def restart(message: types.Message, state: FSMContext):
    # Сброс состояния пользователя и возврат к началу диалога
    await state.finish()
    await message.answer("Пожалуйста, введите ваше имя:")
    await SupportForm.name.set()


if __name__ == '__main__':
    # Запуск бота
    executor.start_polling(dp, skip_updates=True)
