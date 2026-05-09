import asyncio
import sqlite3
import os
import random
import string
from datetime import datetime, timedelta

# المكتبات الأساسية
from telethon import TelegramClient, events
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- 1. الإعدادات ---
API_ID = 33595004  # استبدله بـ API ID الخاص بك
API_HASH = 'cbd1066ed026997f2f4a7c4323b7bda7'  # استبدله بـ API HASH الخاص بك
BOT_TOKEN = '8739665249:AAGtm3E_wVjS0LD4UDLz-4DolskfiLZiPW8'  # استبدله بـ Token البوت الخاص بك
ADMIN_ID = 8085768728  # استبدله بـ ID حسابك الشخصي

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# --- 2. قاعدة البيانات ---
db = sqlite3.connect("bot_database.db")
cur = db.cursor()
cur.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, is_premium INTEGER DEFAULT 0, sub_end TEXT, msg TEXT DEFAULT 'مرحباً بك')")
cur.execute("CREATE TABLE IF NOT EXISTS codes (code TEXT PRIMARY KEY, days INTEGER)")
cur.execute("CREATE TABLE IF NOT EXISTS accounts (phone TEXT PRIMARY KEY, user_id INTEGER)")
cur.execute("CREATE TABLE IF NOT EXISTS reports (phone TEXT PRIMARY KEY, user_id INTEGER, sent_count INTEGER DEFAULT 0)")
db.commit()

# --- 3. حالات الإدخال (FSM) ---
class Form(StatesGroup):
    wait_phone = State()
    wait_verify = State()
    wait_sub_code = State()
    wait_msg = State()
    wait_group = State()

# --- 4. الأزرار (Keyboards) ---
def get_main_menu(user_id):
    cur.execute("SELECT is_premium, sub_end FROM users WHERE id=?", (user_id,))
    res = cur.fetchone()
    kb = InlineKeyboardMarkup(row_width=2)
    
    if not res or res[0] == 0:
        kb.add(InlineKeyboardButton("💳 تفعيل الاشتراك", callback_data="activate"))
        return kb, "❌ اشتراكك غير مفعل."
    
    kb.add(
        InlineKeyboardButton("➕ إضافة حساب", callback_data="add_acc"),
        InlineKeyboardButton("📱 التحكم بالأرقام", callback_data="manage_accs"),
        InlineKeyboardButton("📝 نص الرسالة", callback_data="set_msg"),
        InlineKeyboardButton("📢 إضافة جروب", callback_data="add_group"),
        InlineKeyboardButton("📊 التقارير", callback_data="my_stats")
    )
    return kb, f"✅ اشتراكك فعال لغاية: {res[1]}"

def admin_kb():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("🎟️ توليد كود", callback_data="gen_code"),
        InlineKeyboardButton("📊 إحصائيات عامة", callback_data="admin_stats"),
        InlineKeyboardButton("📢 إذاعة", callback_data="broadcast")
    )
    return kb

# --- 5. الأوامر الأساسية ---
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    cur.execute("INSERT OR IGNORE INTO users (id) VALUES (?)", (user_id,))
    db.commit()
    kb, txt = get_main_menu(user_id)
    await message.answer(f"🛠️ **بوت التسويق الذكي (نسخة iPhone)**\n\n{txt}", reply_markup=kb, parse_mode="Markdown")

@dp.message_handler(commands=['admin'], user_id=ADMIN_ID)
async def cmd_admin(message: types.Message):
    await message.answer("👨‍🔧 أهلاً بك في لوحة الإدارة:", reply_markup=admin_kb())

# --- 6. نظام إضافة الحسابات (iPhone Identity) ---
@dp.callback_query_handler(text="add_acc")
async def start_add(call: types.CallbackQuery):
    cur.execute("SELECT COUNT(*) FROM accounts WHERE user_id=?", (call.from_user.id,))
    if cur.fetchone()[0] >= 50:
        return await call.answer("🛑 الحد الأقصى 50 حساب!", show_alert=True)
    await Form.wait_phone.set()
    await call.message.answer("📱 أرسل رقم الهاتف (مثال +2010...):")

@dp.message_handler(state=Form.wait_phone)
async def process_phone(message: types.Message, state: FSMContext):
    phone = message.text.strip()
    client = TelegramClient(f"sessions/{phone}", API_ID, API_HASH, 
                            device_model="iPhone 15 Pro Max", system_version="17.4.1")
    await client.connect()
    try:
        sent = await client.send_code_request(phone)
        await state.update_data(phone=phone, hash=sent.phone_code_hash, client=client)
        await Form.wait_verify.set()
        await message.answer("📩 أرسل كcode التحقق الآن:")
    except Exception as e:
        await message.answer(f"❌ خطأ: {e}")
        await state.finish()

@dp.message_handler(state=Form.wait_verify)
async def process_verify(message: types.Message, state: FSMContext):
    data = await state.get_data()
    try:
        await data['client'].sign_in(data['phone'], message.text, phone_code_hash=data['hash'])
        cur.execute("INSERT INTO accounts (phone, user_id) VALUES (?, ?)", (data['phone'], message.from_user.id))
        db.commit()
        await message.answer("✅ تم ربط الحساب بنجاح بنظام iPhone!")
    except Exception as e:
        await message.answer(f"❌ فشل: {e}")
    await state.finish()

# --- 7. التحكم بالأرقام المضافة ---
@dp.callback_query_handler(text="manage_accs")
async def manage_accs(call: types.CallbackQuery):
    cur.execute("SELECT phone FROM accounts WHERE user_id=?", (call.from_user.id,))
    accs = cur.fetchall()
    if not accs: return await call.answer("لا توجد حسابات.")
    
    kb = InlineKeyboardMarkup(row_width=1)
    for acc in accs:
        kb.add(InlineKeyboardButton(f"📱 {acc[0]}", callback_data=f"manage_{acc[0]}"))
    kb.add(InlineKeyboardButton("⬅️ رجوع", callback_data="back_home"))
    await call.message.edit_text("⚙️ اختر الحساب للتحكم به:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith('manage_'))
async def specific_acc(call: types.CallbackQuery):
    phone = call.data.split("_")[1]
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("🗑️ حذف الحساب", callback_data=f"del_{phone}"),
        InlineKeyboardButton("⬅️ رجوع", callback_data="manage_accs")
    )
    await call.message.edit_text(f"🛠️ إدارة الحساب: {phone}", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith('del_'))
async def delete_acc(call: types.CallbackQuery):
    phone = call.data.split("_")[1]
    cur.execute("DELETE FROM accounts WHERE phone=?", (phone,))
    db.commit()
    if os.path.exists(f"sessions/{phone}.session"): os.remove(f"sessions/{phone}.session")
    await call.answer("✅ تم الحذف.")
    await manage_accs(call)

# --- 8. نظام الأكواد والاشتراك ---
@dp.callback_query_handler(text="gen_code", user_id=ADMIN_ID)
async def gen_code(call: types.CallbackQuery):
    new_code = "PREM-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
    cur.execute("INSERT INTO codes (code, days) VALUES (?, ?)", (new_code, 30))
    db.commit()
    await call.message.answer(f"🎟️ كود جديد (30 يوم):\n`{new_code}`", parse_mode="Markdown")

@dp.callback_query_handler(text="activate")
async def ask_code(call: types.CallbackQuery):
    await Form.wait_sub_code.set()
    await call.message.answer("🔑 أرسل كود التفعيل الخاص بك:")

@dp.message_handler(state=Form.wait_sub_code)
async def process_sub(message: types.Message, state: FSMContext):
    cur.execute("SELECT days FROM codes WHERE code=?", (message.text,))
    res = cur.fetchone()
    if res:
        end_date = (datetime.now() + timedelta(days=res[0])).strftime('%Y-%m-%d')
        cur.execute("UPDATE users SET is_premium=1, sub_end=? WHERE id=?", (end_date, message.from_user.id))
        cur.execute("DELETE FROM codes WHERE code=?", (message.text,))
        db.commit()
        await message.answer(f"🎉 تم التفعيل بنجاح لغاية {end_date}")
    else:
        await message.answer("❌ الكود غير صحيح.")
    await state.finish()

# --- 9. الرجوع للقائمة الرئيسية ---
@dp.callback_query_handler(text="back_home")
async def back_home(call: types.CallbackQuery):
    kb, txt = get_main_menu(call.from_user.id)
    await call.message.edit_text(f"🛠️ **بوت التسويق الذكي**\n\n{txt}", reply_markup=kb, parse_mode="Markdown")

# --- 10. تشغيل البوت ---
if __name__ == '__main__':
    if not os.path.exists("sessions"): os.makedirs("sessions")
    from aiogram import executor
    print("🚀 البوت يعمل الآن بنظام iPhone...")
    executor.start_polling(dp, skip_updates=True)
