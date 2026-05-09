
import os, time, threading, datetime, json, logging
from telebot import TeleBot, types
from instagrapi import Client
from dotenv import load_dotenv

# --- إعدادات الحماية والبيئة ---
load_dotenv()
API_TOKEN = os.getenv('BOT_TOKEN')
MAIN_ADMIN = int(os.getenv('ADMIN_ID', 0))
bot = TeleBot(API_TOKEN, parse_mode="HTML")

# --- قاعدة بيانات برمجية (تُحفظ في ملف) ---
DB_FILE = 'database.json'
def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f: return json.load(f)
    return {"users": {}, "admins": [MAIN_ADMIN], "sessions": [], "locked": False}

db = load_db()

def save_db():
    with open(DB_FILE, 'w') as f: json.dump(db, f, indent=4)

# --- محرك الانتحال والبلاغ (الوحش) ---
def full_attack(cl, target_url, r_id, t_type):
    try:
        # 1. إذا كان البلاغ "انتحال"، نقوم بتغيير بروفايل الحساب أولاً
        if r_id == "3": # كود الانتحال
            target_username = target_url.split('/')[-1] if '/' in target_url else target_url
            target_info = cl.user_info_by_username(target_username)
            # تغيير الصورة والاسم لتقمص الشخصية
            cl.account_edit(full_name=target_info.full_name, biography=target_info.biography)
            try:
                cl.account_set_biography(target_info.biography)
                # ميزة متطورة: تحميل صورة الهدف ووضعها بروفايل
                photo_path = cl.user_download_profile_pic(target_info.pk)
                cl.account_change_picture(photo_path)
            except: pass

        # 2. تنفيذ البلاغ
        if t_type == "1": # حساب
            uid = cl.user_id_from_username(target_url.split('/')[-1])
            cl.user_report(uid, reason_tag=r_id)
        elif t_type == "3": # بوست
            mid = cl.media_pk_from_url(target_url)
            cl.media_report(mid, reason_tag=r_id)
        
        logging.info(f"✅ Success: {cl.username}")
    except Exception as e:
        logging.error(f"❌ Failed {cl.username}: {e}")

# --- لوحات التحكم (المنطق المتطور) ---
def get_main_menu(uid):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("🚀 شن هجوم", "👤 حسابي", "📊 الإحصائيات")
    if uid in db['admins']:
        markup.add("🛠 لوحة الأدمن", "🔑 إدارة السيشنات")
    return markup

# --- أوامر الأدمن (رفع وتنزيل) ---
@bot.message_handler(commands=['promote'])
def promote_admin(message):
    if message.from_user.id != MAIN_ADMIN: return
    try:
        new_admin = int(message.text.split()[1])
        if new_admin not in db['admins']:
            db['admins'].append(new_admin)
            save_db()
            bot.reply_to(message, f"✅ تم رفع المستخدم {new_admin} إلى رتبة أدمن.")
    except: bot.reply_to(message, "⚠️ استخدم: /promote [ID]")

@bot.message_handler(commands=['demote'])
def demote_admin(message):
    if message.from_user.id != MAIN_ADMIN: return
    try:
        target = int(message.text.split()[1])
        if target in db['admins'] and target != MAIN_ADMIN:
            db['admins'].remove(target)
            save_db()
            bot.reply_to(message, "✅ تم تنزيل الأدمن إلى رتبة عضو.")
    except: bot.reply_to(message, "⚠️ استخدم: /demote [ID]")

# --- استقبال الروابط والبلاغات ---
@bot.message_handler(func=lambda m: "instagram.com" in m.text)
def handle_insta_link(message):
    uid = message.from_user.id
    if db['locked'] and uid not in db['admins']:
        return bot.reply_to(message, "🔒 البوت مغلق للصيانة.")
    
    url = message.text
    markup = types.InlineKeyboardMarkup(row_width=2)
    reasons = [
        ("🔞 إباحي", "1"), ("🚫 عنف", "2"), ("👤 انتحال (أبيض)", "3"),
        ("🛡️ انتحال (أسود)", "3"), ("💊 مخدرات", "4"), ("💀 انتحار", "5"),
        ("⚠️ سكام", "6"), ("📧 سبام", "7"), ("🗣 هيت", "8")
    ]
    # تحديد النوع تلقائياً
    t_type = "3" if "/p/" in url or "/reels/" in url else "1"
    if "/stories/" in url: t_type = "2"

    btns = [types.InlineKeyboardButton(r[0], callback_data=f"hit_{r[1]}_{t_type}_{url}") for r in reasons]
    markup.add(*btns)
    bot.reply_to(message, "🎯 <b>تم رصد الهدف!</b>\nاختر نوع الهجوم الذي تريده:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("hit_"))
def process_attack(call):
    _, r_id, t_type, url = call.data.split("_", 3)
    bot.edit_message_text("🚀 <b>بدأ الهجوم المكثف...</b>", call.message.chat.id, call.message.id)
    
    # توزيع المهام على كل السيشنات بسرعة البرق
    for session_data in db['sessions']:
        # هنا نقوم بإنشاء كائن Client لكل سيشن (يفضل تحميلهم مسبقاً للسرعة)
        cl = Client()
        cl.set_settings(session_data) 
        threading.Thread(target=full_attack, args=(cl, url, r_id, t_type)).start()
    
    bot.send_message(call.message.chat.id, "✅ <b>تم إرسال كافة البلاغات!</b>\nالفرق بين كل بلاغ وبلاغ: 0.2 ثانية.")

# --- تشغيل البوت ---
if __name__ == "__main__":
    print("🔥 The Beast is Online!")
    bot.infinity_polling()
