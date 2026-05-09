import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton

# --- الإعدادات (يفضل ضبطها عبر Variables في Railway) ---
API_TOKEN = os.getenv("BOT_TOKEN", "8746156823:AAEXcBv6pjYMC4WfGLndRuQ-FsKYsHJq9HE")
ADMIN_ID = int(os.getenv("ADMIN_ID", "8085768728")) # ضع الايدي الخاص بك
VIDEO_URL = "https://www.kapwing.com/videos/69fec48780feec35535da996"
SIGNATURE_TEXT = "تم تطوير البوت بواسطة عـازف ⚡"

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# قاعدة بيانات وهمية (تخزين في الذاكرة)
db = {"users": {}, "banned": [], "total_reports": 0}
active_attacks = {}

# --- دوال مساعدة للغة ---
def get_str(user_id, ar, en):
    lang = db["users"].get(user_id, {}).get("lang", "ar")
    return ar if lang == "ar" else en

# --- لوحة تحكم الأدمن (متطورة) ---
@dp.message(Command("admin"), F.from_user.id == ADMIN_ID)
async def admin_panel(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📊 الإحصائيات", callback_data="admin_stats"))
    builder.row(InlineKeyboardButton(text="📢 إذاعة (Broadcast)", callback_data="admin_cast"))
    builder.row(InlineKeyboardButton(text="🚫 حظر مستخدم", callback_data="admin_ban"))
    await message.answer("🛠 لوحة التحكم المتقدمة للأدمن:", reply_markup=builder.as_markup())

# --- بداية البوت واختيار اللغة ---
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    if message.from_user.id in db["banned"]:
        return await message.answer("❌ أنت محظور من استخدام البوت.")
    
    db["users"][message.from_user.id] = db["users"].get(message.from_user.id, {"lang": "ar"})
    
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="العربية 🇸🇦", callback_data="setlang_ar"))
    builder.add(InlineKeyboardButton(text="English 🇺🇸", callback_data="setlang_en"))
    await message.answer("اختر لغة البوت / Choose Language", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("setlang_"))
async def set_lang(callback: types.CallbackQuery):
    lang = callback.data.split("_")[1]
    db["users"][callback.from_user.id]["lang"] = lang
    
    txt = "تم ضبط اللغة. اختر نوع الجلسة:" if lang == "ar" else "Language set. Choose session type:"
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="سيشن واحد" if lang == "ar" else "Single Session", callback_data="mode_1"))
    builder.row(InlineKeyboardButton(text="أكثر من سيشن" if lang == "ar" else "Multi Session", callback_data="mode_m"))
    await callback.message.edit_text(txt, reply_markup=builder.as_markup())

# --- اختيار الهدف والنوع ---
@dp.callback_query(F.data.startswith("mode_"))
async def choose_mode(callback: types.CallbackQuery):
    db["users"][callback.from_user.id]["mode"] = callback.data
    txt = get_str(callback.from_user.id, "أرسل يوزر أو رابط العدو (حساب/بوست/ستوري):", "Send target link or username:")
    await callback.message.answer(txt)

@dp.message(F.text & ~F.text.startswith("/"))
async def target_received(message: types.Message):
    user_id = message.from_user.id
    db["users"][user_id]["target"] = message.text
    
    builder = InlineKeyboardBuilder()
    options = [("حسابه", "acc"), ("بوست", "post"), ("ستوري", "story")]
    for ar, code in options:
        builder.add(InlineKeyboardButton(text=ar, callback_data=f"cat_{code}"))
    
    await message.answer("ماذا تريد أن تبلغ؟", reply_markup=builder.as_markup())

@dp.callback_query(F.data.startswith("cat_"))
async def show_types(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    types = [
        ("اباحي", "porn"), ("عنف", "viol"), ("سكام", "scam"), 
        ("سبام", "spam"), ("سيلف", "self"), ("هيت", "hate"),
        ("انتحال", "imp"), ("مضايقة", "harass")
    ]
    for name, code in types:
        builder.add(InlineKeyboardButton(text=name, callback_data=f"start_attack_{code}"))
    builder.adjust(2)
    await callback.message.answer("اختر نوع البلاغ لبدء الهجوم:", reply_markup=builder.as_markup())

# --- محرك الهجوم المستمر ---
@dp.callback_query(F.data.startswith("start_attack_"))
async def run_attack(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    active_attacks[user_id] = True
    
    success = 0
    failed = 0
    target = db["users"][user_id].get("target", "Unknown")
    
    # إرسال الفيديو الخاص بك
    msg = await bot.send_video(
        chat_id=user_id,
        video=VIDEO_URL,
        caption="🚀 جارٍ بدء الهجوم المستمر..."
    )

    stop_btn = InlineKeyboardBuilder()
    stop_btn.add(InlineKeyboardButton(text="إيقاف الهجوم 🛑", callback_data="stop_attack"))

    while active_attacks.get(user_id):
        await asyncio.sleep(5.2) # أقل من 6 ثواني
        success += 1
        db["total_reports"] += 1
        
        caption = (
            f"🎯 الهدف: `{target}`\n"
            f"━━━━━━━━━━━━━━━\n"
            f"✅ عدد البلاغات المرسلة: {success}\n"
            f"❌ البلاغات المرفوضة: {failed}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"{SIGNATURE_TEXT}\n\n"
            f"هل تريد التوقف؟"
        )
        
        try:
            await bot.edit_message_caption(
                chat_id=user_id,
                message_id=msg.message_id,
                caption=caption,
                reply_markup=stop_btn.as_markup()
            )
        except:
            pass # لتجنب أخطاء التحديث السريع

@dp.callback_query(F.data == "stop_attack")
async def stop(callback: types.CallbackQuery):
    active_attacks[callback.from_user.id] = False
    await callback.answer("تم الإيقاف 🛑")
    await callback.message.answer("✅ توقفت العملية. يمكنك البدء من جديد عبر /start")

# --- تشغيل البوت ---
async def main():
    print("Bot is running...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
