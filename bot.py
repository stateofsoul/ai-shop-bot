import asyncio
import logging

from memory_db import get_user, save_user, clear_user
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from groq import Groq

# ---------------- LOGGING ----------------
logging.basicConfig(level=logging.INFO)

# ---------------- TOKENS ----------------
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# ---------------- INIT ----------------
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
client = Groq(api_key=GROQ_API_KEY)


# ---------------- SYSTEM PROMPT (FINAL CLEAN AI SHOP) ----------------
SYSTEM_PROMPT = """
Ты — живой консультант премиального интернет-магазина одежды.

ВАЖНО:
Ты НЕ бот. Ты реальный продавец-консультант.

---

🧠 СТИЛЬ
- говори естественно, по-человечески
- без шаблонных фраз
- 1–2 предложения максимум если не нужно подробнее

---

🧠 АДАПТАЦИЯ
- короткий текст клиента → короткий ответ
- эмоции → отвечай в том же тоне
- сомнения → помогай мягко
- торопится → максимально кратко

---

🧭 ЛОГИКА
1) понять запрос
2) при необходимости задать 1 уточнение
3) предложить 1–2 варианта

---

🛍️ ПРОДАЖИ
- не дави
- не перегружай
- не больше 2 вариантов
- объясняй очень кратко почему подходит

---

❌ ЗАПРЕТЫ
- не выдумывать товары
- не повторять вопросы
- не писать длинные тексты
"""

# ---------------- START ----------------
@dp.message(CommandStart())
async def start(message: Message):
    user_id = message.from_user.id

    # создаём пустую память если нет
    history = await get_user(user_id)
    if not history:
        await save_user(user_id, [])

    await message.answer(
        "Привет 🙂 Я помогу подобрать одежду.\n"
        "Напиши, что ищешь или какой стиль тебе нравится."
    )


# ---------------- CLEAR (ИСПРАВЛЕНО ПОЛНОСТЬЮ) ----------------
@dp.message(Command("clear"))
async def clear(message: Message):
    user_id = message.from_user.id

    try:
        await clear_user(user_id)
        await save_user(user_id, [])  # двойная защита

        await message.answer(
            "🧹 <b>Диалог очищен</b>\n"
            "Я забыл весь контекст. Можем начать заново 🙂",
            parse_mode="HTML"
        )

    except Exception as e:
        logging.error(f"Clear error: {e}")
        await message.answer("Ошибка очистки 😔 попробуй снова")


# ---------------- CHAT ----------------
@dp.message()
async def handle(message: Message):
    user_id = message.from_user.id
    text = message.text

    if not text:
        return

    try:
        # ---------------- LOAD MEMORY ----------------
        history = await get_user(user_id)

        if not history:
            history = []

        # ---------------- ADD USER MESSAGE ----------------
        history.append({
            "role": "user",
            "content": text.strip()
        })

        # ---------------- LIMIT MEMORY ----------------
        history = history[-12:]

        # ---------------- AI REQUEST ----------------
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                *history
            ],
            temperature=0.7
        )

        answer = response.choices[0].message.content.strip()

        # ---------------- SAVE ASSISTANT ----------------
        history.append({
            "role": "assistant",
            "content": answer
        })

        await save_user(user_id, history)

        # ---------------- RESPONSE ----------------
        await message.answer(answer)

    except Exception as e:
        logging.error(f"Chat error: {e}")
        await message.answer(
            "⚠️ Ошибка обработки запроса\n"
            "Попробуй ещё раз чуть позже"
        )


# ---------------- RUN ----------------
async def main():
    print("AI SHOP BOT READY 🚀")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
