import os, time, threading, datetime, json
from telebot import TeleBot, types
from instagrapi import Client
from dotenv import load_dotenv

# --- إعدادات البيئة ---
load_dotenv()
API_TOKEN = os.getenv('BOT_TOKEN')
# تأكد من وضع الأيدي الصحيح في ريلواي، وإذا ما ضبط الكود بيتعرف عليك تلقائياً
ADMIN_ID = int(os.getenv('ADMIN_ID', 0))

bot = TeleBot(API_TOKEN, parse_mode="HTML")

# --- قاعدة بيانات داخلية ---
db = {
    "users": {},      # {user_id: expiry}
    "admins": [ADMIN_ID] if ADMIN_ID != 0 else [],
    "sessions": [],   # يتم إضافة الـ settings الخاصة بـ instagrapi هنا
    "is_locked": False,
    "stats": {"ok": 0, "fail": 0}
}

# --- وظائف الحماية ---
def check_access(uid):
    if uid in db["admins"]: return True
    if db["is_locked"]: return False
    if str(uid) in db["users"]:
        # يمكنك إضافة فحص تاريخ الانتهاء هنا
        return True
    return False

# --- محرك البلاغات السريع ---
def run_report(cl_settings, target, r_id, t_type):
    try:
        cl = Client()
        cl.set_settings(cl_settings)
        # سرعة البرق: تنفيذ بلاغ
        if t_type == "1": # حساب
            uid = cl.user_id_from_username(target.split('/')[-1])
            cl.user_report(uid, reason_tag=r_id)
        elif t_type == "3": # بوست
            mid = cl.media_pk_from_url(target)
            cl.media_report(mid, reason_tag=r_id)
        db["stats"]["ok"] += 1
    except:
        db["stats"]["fail"] += 1

# --- الكيبورد الرئيسي (أزرار أونلاين) ---
def main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("🚀 شن هجوم", "📊 الإحصائيات", "🔑 حساباتي")
    return markup

def admin_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    lock_text = "فتح البوت 🔓" if db["is_locked"] else "قفل البوت 🔒"
    markup.add(
        types.InlineKeyboardButton(lock_text, callback_data="toggle_lock"),
        types.InlineKeyboardButton("➕ إضافة أدمن", callback_data="add_adm"),
        types.InlineKeyboardButton("➕ إضافة سيشن", callback_data="add_sess"),
        types.InlineKeyboardButton("❌ طرد عضو", callback_data="kick_user")
    )
    return markup

# --- الأوامر الأساسية ---
@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id
    # إذا كانت قائمة الأدمنية فاضية، أول واحد يضغط ستارت يصير هو الأدمن
    if not db["admins"]:
        db["admins"].append(uid)
        bot.reply_to(message, "✅ تم التعرف عليك كأدمن رئيسي للنظام!")

    if not check_access(uid):
        bot.reply_to(message, f"❌ الوصول مرفوض.\nالأيدي الخاص بك: <code>{uid}</code>\nارسل الأيدي للمالك للتفعيل.")
        return

    bot.send_message(message.chat.id, "🔥 <b>أهلاً بك في بوت البلاغات المتطور</b>\nاستخدم الأزرار أدناه للتحكم:", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "🚀 شن هجوم")
def attack_init(message):
    if not check_access(message.from_user.id): return
    bot.reply_to(message, "📥 <b>ارسل رابط الهدف الآن (إنستا):</b>")

@bot.message_handler(func=lambda m: "instagram.com" in m.text)
def target_handle(message):
    if not check_access(message.from_user.id): return
    url = message.text
    t_type = "3" if "/p/" in url or "/reels/" in url else "1"
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    reasons = [
        ("🔞 إباحي", "1"), ("🚫 عنف", "2"), ("👤 انتحال", "3"),
        ("💊 مخدرات", "4"), ("💀 سيلف", "5"), ("⚠️ سكام", "6"),
        ("📧 سبام", "7"), ("🗣 هيت", "8")
    ]
    btns = [types.InlineKeyboardButton(r[0], callback_data=f"fire_{r[1]}_{t_type}_{url}") for r in reasons]
    markup.add(*btns)
    bot.reply_to(message, "⚡ <b>تم تحديد الهدف!</b>\nاختر نوع البلاغ المطلوب:", reply_markup=markup)

@bot.message_handler(commands=['admin'])
def show_admin(message):
    if message.from_user.id not in db["admins"]: return
    bot.send_message(message.chat.id, "🛠 <b>لوحة تحكم الإدارة:</b>", reply_markup=admin_keyboard())

# --- معالجة الأكشن ---
@bot.callback_query_handler(func=lambda call: True)
def query_handler(call):
    if call.data.startswith("fire_"):
        if not db["sessions"]:
            return bot.answer_callback_query(call.id, "❌ لا توجد حسابات (Sessions) مربوطة!", show_alert=True)
        
        _, r_id, t_type, url = call.data.split("_", 3)
        bot.edit_message_text("🚀 <b>جاري الهجوم من كافة الحسابات...</b>", call.message.chat.id, call.message.id)
        
        for sess in db["sessions"]:
            threading.Thread(target=run_report, args=(sess, url, r_id, t_type)).start()
        
        bot.send_message(call.message.chat.id, "✅ <b>اكتمل الإرسال!</b>\nتتم المعالجة الآن في أقل من 6 ثواني.")

    elif call.data == "toggle_lock":
        db["is_locked"] = not db["is_locked"]
        bot.answer_callback_query(call.id, "تم تغيير حالة البوت")
        bot.edit_message_reply_markup(call.message.chat.id, call.message.id, reply_markup=admin_keyboard())

# --- تشغيل ---
print("✅ البوت شغال الآن.. اضغط /start في التليجرام")
bot.infinity_polling()
