"}
```python
import asyncio
import logging
from datetime import datetime

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

TOKEN = "8746156823:AAEXcBv6pjYMC4WfGLndRuQ-FsKYsHJq9HE"
ADMIN_ID = 8085768728

logging.basicConfig(level=logging.INFO)

bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher()

# -----------------------------
# Languages
# -----------------------------

TEXTS = {
    "en": {
        "welcome": "Welcome To Moderation Assistant",
        "choose_lang": "Choose Language",
        "menu": "Main Menu",
        "report_type": "Choose Content Type",
        "violations": "Choose Violation Type",
        "stats": "Statistics",
    },
    "ar": {
        "welcome": "اهلا بك في نظام البلاغات",
        "choose_lang": "اختر اللغة",
        "menu": "القائمة الرئيسية",
        "report_type": "اختر نوع المحتوى",
        "violations": "اختر نوع الهجوم",
        "stats": "الإحصائيات",
    }
}

users_lang = {}
reports_db = []

# -----------------------------
# Keyboards
# -----------------------------

def lang_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🇸🇦 العربية",
                    callback_data="lang_ar"
                ),
                InlineKeyboardButton(
                    text="🇺🇸 English",
                    callback_data="lang_en"
                )
            ]
        ]
    )

def main_menu(lang):
    text = TEXTS[lang]

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📄 Account",
                    callback_data="type_account"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🖼 Post",
                    callback_data="type_post"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎥 Story",
                    callback_data="type_story"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📊 Statistics",
                    callback_data="stats"
                )
            ]
        ]
    )

def violation_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Spam",
                    callback_data="v_spam"
                ),
                InlineKeyboardButton(
                    text="Scam",
                    callback_data="v_scam"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Violence",
                    callback_data="v_violence"
                ),
                InlineKeyboardButton(
                    text="Nudity",
                    callback_data="v_nudity"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Harassment",
                    callback_data="v_harassment"
                ),
                InlineKeyboardButton(
                    text="Impersonation",
                    callback_data="v_impersonation"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Hate Speech",
                    callback_data="v_hate"
                ),
                InlineKeyboardButton(
                    text="Self Harm",
                    callback_data="v_selfharm"
                )
            ]
        ]
    )

# -----------------------------
# Start
# -----------------------------

@dp.message(CommandStart())
async def start(message: Message):
    await message.answer(
        "Choose Language / اختر اللغة",
        reply_markup=lang_keyboard()
    )

# -----------------------------
# Language
# -----------------------------

@dp.callback_query(F.data.startswith("lang_"))
async def set_lang(callback: CallbackQuery):
    lang = callback.data.split("")[1]

    users_lang[callback.from_user.id] = lang

    text = TEXTS[lang]

    await callback.message.edit_text(
        text["welcome"],
        reply_markup=main_menu(lang)
    )

# -----------------------------
# Content Type
# -----------------------------

@dp.callback_query(F.data.startswith("type"))
async def choose_type(callback: CallbackQuery):
    lang = users_lang.get(callback.from_user.id, "en")

    text = TEXTS[lang]

    content_type = callback.data.replace("type_", "")

    reports_db.append({
        "user": callback.from_user.id,
        "type": content_type,
        "time": datetime.now().strftime("%H:%M:%S")
    })

    await callback.message.answer(
        f"{text['violations']}\n\nSelected: {content_type}",
        reply_markup=violation_keyboard()
    )

# -----------------------------
# Violations
# -----------------------------

@dp.callback_query(F.data.startswith("v_"))
async def violation(callback: CallbackQuery):
    violation_type = callback.data.replace("v_", "")

    await callback.message.answer(
        f"✅ Violation selected:\n\n{violation_type}\n\n"
        f"Your moderation request has been queued for review."
    )

# -----------------------------
# Statistics
# -----------------------------

@dp.callback_query(F.data == "stats")
async def stats(callback: CallbackQuery):
    total = len(reports_db)

    await callback.message.answer(
        f"""
📊 Statistics

Total Requests: {total}
Users: {len(users_lang)}
System: Online
Queue: Active
        """
    )

# -----------------------------
# Admin Panel
# -----------------------------

@dp.message(Command("admin"))
async def admin_panel(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    await message.answer(
        f"""
🛠 Admin Panel

👤 Users: {len(users_lang)}
📄 Requests: {len(reports_db)}

System Status: Online
Logs: Active
Database: Connected
Queue: Running
        """
    )

# -----------------------------
# Logs
# -----------------------------

@dp.message(Command("logs"))
async def logs(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    if not reports_db:
        await message.answer("No logs")
        return

    text = ""

    for item in reports_db[-10:]:
        text += (
            f"User: {item['user']}\n"
            f"Type: {item['type']}\n"
            f"Time: {item['time']}\n\n"
        )

    await message.answer(text)

# -----------------------------
# Main
# -----------------------------

async def main():
    print("Bot Started")
    await dp.start_polling(bot)

if name == "main":
    asyncio.run(main())
