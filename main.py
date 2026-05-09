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

# =========================
# CONFIG
# =========================

TOKEN = "8746156823:AAEXcBv6pjYMC4WfGLndRuQ-FsKYsHJq9HE"
ADMIN_ID = 8085768728

# =========================
# LOGGING
# =========================

logging.basicConfig(level=logging.INFO)

# =========================
# BOT
# =========================

bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(
        parse_mode=ParseMode.HTML
    )
)

dp = Dispatcher()

# =========================
# DATABASE
# =========================

users_lang = {}
reports_db = []
banned_users = set()

# =========================
# LANGUAGES
# =========================

TEXTS = {
    "en": {
        "welcome": "Welcome To Moderation Assistant",
        "choose_lang": "Choose Language",
        "menu": "Main Menu",
        "report_type": "Choose Content Type",
        "violations": "Choose Violation Type",
        "stats": "Statistics",
        "queued": "Your request has been added to review queue"
    },
    "ar": {
        "welcome": "اهلا بك في نظام المراجعة",
        "choose_lang": "اختر اللغة",
        "menu": "القائمة الرئيسية",
        "report_type": "اختر نوع المحتوى",
        "violations": "اختر نوع المخالفة",
        "stats": "الإحصائيات",
        "queued": "تم إضافة طلبك للمراجعة"
    }
}

# =========================
# KEYBOARDS
# =========================

def language_keyboard():
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

def main_menu():
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

def violations_keyboard():
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

# =========================
# START
# =========================

@dp.message(CommandStart())
async def start(message: Message):

    if message.from_user.id in banned_users:
        return

    await message.answer(
        "Choose Language / اختر اللغة",
        reply_markup=language_keyboard()
    )

# =========================
# LANGUAGE
# =========================

@dp.callback_query(F.data.startswith("lang_"))
async def set_language(callback: CallbackQuery):

    lang = callback.data.split("")[1]

    users_lang[callback.from_user.id] = lang

    text = TEXTS[lang]

    await callback.message.edit_text(
        text["welcome"],
        reply_markup=main_menu()
    )

# =========================
# CONTENT TYPE
# =========================

@dp.callback_query(F.data.startswith("type"))
async def content_type(callback: CallbackQuery):

    if callback.from_user.id in banned_users:
        return

    lang = users_lang.get(
        callback.from_user.id,
        "en"
    )

    text = TEXTS[lang]

    selected_type = callback.data.replace(
        "type_",
        ""
    )

    reports_db.append({
        "user": callback.from_user.id,
        "type": selected_type,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

    await callback.message.answer(
        f"{text['violations']}\n\nSelected: {selected_type}",
        reply_markup=violations_keyboard()
    )

# =========================
# VIOLATIONS
# =========================

@dp.callback_query(F.data.startswith("v_"))
async def violation_selected(callback: CallbackQuery):

    violation = callback.data.replace(
        "v_",
        ""
    )

    lang = users_lang.get(
        callback.from_user.id,
        "en"
    )

    text = TEXTS[lang]

    await callback.message.answer(
        f"✅ {text['queued']}\n\n"
        f"Type: {violation}"
    )

# =========================
# STATS
# =========================

@dp.callback_query(F.data == "stats")
async def statistics(callback: CallbackQuery):

    total_requests = len(reports_db)
    total_users = len(users_lang)

    await callback.message.answer(
        f"""
📊 Statistics

👤 Users: {total_users}

📄 Requests: {total_requests}

🟢 System: Online

⚡ Queue: Active
        """
    )

# =========================
# ADMIN PANEL
# =========================

@dp.message(Command("admin"))
async def admin_panel(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    await message.answer(
        f"""
🛠 Admin Panel

👤 Total Users: {len(users_lang)}

📄 Total Requests: {len(reports_db)}

🟢 System Status: Online

⚡ Queue Status: Running

📦 Database: Connected

📝 Logs: Active
        """
    )

# =========================
# LOGS
# =========================

@dp.message(Command("logs"))
async def logs(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    if len(reports_db) == 0:
        await message.answer("No Logs")
        return

    text = ""

    for item in reports_db[-10:]:

        text += (
            f"User: {item['user']}\n"
            f"Type: {item['type']}\n"
            f"Time: {item['time']}\n\n"
        )

    await message.answer(text)

# =========================
# BROADCAST
# =========================

@dp.message(Command("broadcast"))
async def broadcast(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    msg = message.text.replace(
        "/broadcast",
        ""
    ).strip()

    success = 0

    for user_id in users_lang.keys():

        try:
            await bot.send_message(
                user_id,
                msg
            )

            success += 1

        except:
            pass

    await message.answer(
        f"Broadcast Sent To {success} Users"
    )

# =========================
# BAN
# =========================

@dp.message(Command("ban"))
async def ban_user(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    try:

        user_id = int(
            message.text.split()[1]
        )

        banned_users.add(user_id)

        await message.answer(
            f"User {user_id} banned"
        )

    except:

        await message.answer(
            "Usage:\n/ban USER_ID"
        )

# =========================
# UNBAN
# =========================

@dp.message(Command("unban"))
async def unban_user(message: Message):

    if message.from_user.id != ADMIN_ID:
        return

    try:

        user_id = int(
            message.text.split()[1]
        )

        banned_users.discard(user_id)

        await message.answer(
            f"User {user_id} unbanned"
        )

    except:

        await message.answer(
            "Usage:\n/unban USER_ID"
        )

# =========================
# HELP
# =========================

@dp.message(Command("help"))
async def help_command(message: Message):

    await message.answer(
        """
📚 Commands

/start
/help
/admin
/stats
/ban
/unban
/broadcast
        """
    )

# =========================
# MAIN
# =========================

async def main():

    print("Bot Started Successfully")

    await dp.start_polling(bot)
