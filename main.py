import os, time, threading, json, datetime
from telebot import TeleBot, types
from instagrapi import Client
from dotenv import load_dotenv

# --- إعدادات النظام ---
load_dotenv()
API_TOKEN = os.getenv('BOT_TOKEN')
MAIN_OWNER = int(os.getenv('ADMIN_ID', 0)) # أيديك من ريلواي
bot = TeleBot(API_TOKEN, parse_mode="HTML")

# --- إدارة قاعدة البيانات ---
DB_PATH = "bot_database.json"

def load_db():
    if os.path.exists(DB_PATH):
        try:
            with open(DB_PATH, 'r') as f: return json.load(f)
        except: pass
    return {
        "admins": [MAIN_OWNER],
        "users": {},
        "sessions": [], # تخزين السيشنات المربوطة
        "settings": {"delay": 1.0, "count_per_acc": 1},
        "locked": False,
        "stats": {"success": 0, "fail": 0}
    }

db = load_db()

def save_db():
    with open(DB_PATH, 'w') as f:
        json.dump(db, f, indent=4)

# --- محرك إضافة السيشنات (تسجيل دخول) ---
def add_sessions_worker(chat_id, account_list):
    added_count = 0
    for entry in account_list:
        if ":" not in entry: continue
        user, pw = entry.split(":", 1)
        try:
            cl = Client()
            # فحص وتسجيل دخول
            cl.login(user.strip(), pw.strip())
            session_settings = cl.get_settings()
            # حفظ اسم المستخدم مع السيشن للتمييز
            db["sessions"].append({"user": user.strip(), "data": session_settings})
            added_count += 1
            save_db()
        except Exception as e:
            bot.send_message(chat_id, f"❌ فشل الحساب {user.strip()}: {str(e)[:50]}")
    
    bot.send_message(chat_id, f"✅ اكتمل الفحص! تم إضافة <b>{added_count}</b> سيشن جديد.")

# --- محرك الهجوم المكثف ---
def attack_engine(target_url, reason_id, target_type):
    delay = db["settings"]["delay"]
    reps_count = db["settings"]["count_per_acc"]
    
    for session_item in db["sessions"]:
        for _ in range(reps_count):
            try:
                cl = Client()
                cl.set_settings(session_item["data"])
                
                if target_type == "1": # حساب
                    target_name = target_url.split('/')[-1] if '/' in target_url else target_url
                    target_id = cl.user_id_from_username(target_name)
                    cl.user_report(target_id, reason_tag=reason_id)
                elif target_type == "3": # بوست / ريل
                    media_id = cl.media_pk_from_url(target_url)
                    cl.media_report(media_id, reason_tag=reason_id)
                
                db["stats"]["success"] += 1
            except:
                db["stats"]["fail"] += 1
            
            time.sleep(delay) # الفرق الزمني المطلوب
    save_db()

# --- لوحات التحكم (Keyboards) ---
def get_main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("🚀 شن هجوم", "🔑 إدارة السيشنات")
    markup.add("⚙️ إعدادات السرعة", "📊 الإحصائيات")
    markup.add("🛠 لوحة الأدمن")
    return markup

def get_admin_inline():
    markup = types.InlineKeyboardMarkup(row_width=2)
    l_text = "🔓 فتح البوت" if db["locked"] else "🔒 قفل البوت"
    markup.add(
        types.InlineKeyboardButton(l_text, callback_data="toggle_lock"),
        types.InlineKeyboardButton("➕ رفع أدمن", callback_data="prom_adm"),
        types.InlineKeyboardButton("➖ تنزيل أدمن", callback_data="dem_adm")
    )
    return markup

# --- معالجة الأوامر ---
@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id
    if db["locked"] and uid not in db["admins"]:
        return bot.reply_to(message, "⚠️ البوت مغلق حالياً للصيانة من قبل الإدارة.")
    
    bot.send_message(message.chat.id, "🔥 <b>مرحباً بك في نظام البلاغات الفائق (برو ماكس)</b>\n\nالبوت جاهز لإرسال بلاغات مكثفة بفرق ثواني دقيق.", reply_markup=get_main_menu())

@bot.message_handler(func=lambda m: m.text == "🛠 لوحة الأدمن")
def admin_panel(message):
    if message.from_user.id not in db["admins"]: return
    bot.send_message(message.chat.id, "⚙️ <b>لوحة التحكم والإدارة:</b>", reply_markup=get_admin_inline())

@bot.message_handler(func=lambda m: m.text == "🔑 إدارة السيشنات")
def session_mgmt(message):
    if message.from_user.id not in db["admins"]: return
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("➕ إضافة سيشنات (متعدد)", callback_data="add_multi"))
    markup.add(types.InlineKeyboardButton("🗑 مسح كافة السيشنات", callback_data="clear_all"))
    bot.send_message(message.chat.id, f"🔑 <b>إدارة الحسابات المربوطة:</b>\n\nعدد السيشنات النشطة: {len(db['sessions'])}", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "⚙️ إعدادات السرعة")
def settings_mgmt(message):
    if message.from_user.id not in db["admins"]: return
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton(f"⏱ التايمر الحالي: {db['settings']['delay']} ثانية", callback_data="edit_delay"))
    markup.add(types.InlineKeyboardButton(f"🔢 عدد البلاغات لكل حساب: {db['settings']['count_per_acc']}", callback_data="edit_count"))
    bot.send_message(message.chat.id, "⚙️ <b>تعديل سرعة وكمية البلاغات:</b>", reply_markup=markup)

# --- معالجة روابط الهجوم ---
@bot.message_handler(func=lambda m: "instagram.com" in m.text or m.text == "🚀 شن هجوم")
def attack_init(message):
    if message.text == "🚀 شن هجوم":
        return bot.send_message(message.chat.id, "🎯 <b>ارسل رابط الهدف (حساب أو بوست):</b>")
    
    url = message.text
    t_type = "3" if "/p/" in url or "/reels/" in url else "1"
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    reasons = [
        ("🔞 إباحي", "1"), ("🚫 عنف", "2"), ("👤 انتحال", "3"),
        ("💊 مخدرات", "4"), ("💀 سيلف", "5"), ("⚠️ سكام", "6"),
        ("📧 سبام", "7"), ("🗣 خطاب كراهية", "8")
    ]
    btns = [types.InlineKeyboardButton(r[0], callback_data=f"fire_{r[1]}_{t_type}_{url}") for r in reasons]
    markup.add(*btns)
    bot.reply_to(message, "⚡ <b>تم رصد الهدف!</b> اختر نوع البلاغ المطلوب تنفيذه:", reply_markup=markup)

# --- معالجة الـ Callback Queries ---
@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    uid = call.from_user.id
    
    if call.data == "add_multi":
        msg = bot.send_message(call.message.chat.id, "ارسل الحسابات (حساب في كل سطر) كالتالي:\n<code>user:pass</code>")
        bot.register_next_step_handler(msg, process_multi_sessions)
    
    elif call.data == "edit_delay":
        msg = bot.send_message(call.message.chat.id, "ارسل الفرق الزمني الجديد بالثواني (مثلاً 0.5):")
        bot.register_next_step_handler(msg, lambda m: update_setting(m, "delay"))

    elif call.data == "edit_count":
        msg = bot.send_message(call.message.chat.id, "ارسل عدد البلاغات المطلوب من كل حساب:")
        bot.register_next_step_handler(msg, lambda m: update_setting(m, "count_per_acc"))

    elif call.data.startswith("fire_"):
        if not db["sessions"]:
            return bot.answer_callback_query(call.id, "❌ لا توجد سيشنات نشطة! اضف حسابات أولاً.", show_alert=True)
        
        _, r_id, t_type, url = call.data.split("_", 3)
        bot.edit_message_text("🚀 <b>جاري إطلاق الهجوم المكثف...</b>", call.message.chat.id, call.message.id)
        threading.Thread(target=attack_engine, args=(url, r_id, t_type)).start()

# --- وظائف التحديث والمدخلات ---
def process_multi_sessions(message):
    lines = message.text.split('\n')
    bot.reply_to(message, f"⏳ جاري فحص {len(lines)} حساب... قد يستغرق هذا وقتاً.")
    threading.Thread(target=add_sessions_worker, args=(message.chat.id, lines)).start()

def update_setting(message, key):
    try:
        val = float(message.text) if key == "delay" else int(message.text)
        db["settings"][key] = val
        save_db()
        bot.reply_to(message, f"✅ تم تحديث {key} إلى {val}")
    except:
        bot.reply_to(message, "❌ خطأ في المدخلات! ارسل أرقاماً فقط.")

# --- تشغيل البوت ---
print("🔥 البوت يعمل الآن.. اذهب للتليجرام واضغط /start")
bot.infinity_polling()
