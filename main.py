# --- Advanced Configuration ---
API_TOKEN = '8746156823:AAEXcBv6pjYMC4WfGLndRuQ-FsKYsHJq9HE'
ADMIN_ID = 8085768728  # أيديك هنا
DEV_LINK = "https://t.me/devazf" # رابط حسابك
VIDEO_LINK = "https://www.kapwing.com/videos/69fec48780feec35535da996"

STRINGS = {
    'en': {
        'welcome': "🔥 **Instagram Report Pro v3.0**\nChoose Language:",
        'main_menu': "Main Dashboard:",
        'add_session': "🔑 Add Session",
        'start_report': "🎯 Start Reporting",
        'dev_btn': "👨‍💻 Developer",
        'admin_btn': "🛠 Admin Panel",
        'target_prompt': "Send Target Username or Link:",
        'type_prompt': "Select Content Type:",
        'reason_prompt': "Select Report Reason:",
        'stats': "📊 **Live Status**\n\n✅ Sent: {}\n❌ Failed: {}\n⏱ Interval: Random (3-6s)\n\nStop?",
        'stop_btn': "STOP 🛑",
        'locked': "🚫 Bot is Locked.",
        'back': "🔙 Back"
    },
    'ar': {
        'welcome': "🔥 **بوت بلاغات إنستجرام المتطور v3.0**\nاختر لغة البوت:",
        'main_menu': "لوحة التحكم الرئيسية:",
        'add_session': "🔑 إضافة سيشن",
        'start_report': "🎯 بدء البلاغات",
        'dev_btn': "👨‍💻 المطور",
        'admin_btn': "🛠 لوحة الإدارة",
        'target_prompt': "أرسل يوزر الهدف أو الرابط:",
        'type_prompt': "اختر نوع المحتوى:",
        'reason_prompt': "اختر سبب البلاغ:",
        'stats': "📊 **إحصائيات مباشرة**\n\n✅ ناجح: {}\n❌ فشل: {}\n⏱ الفارق: عشوائي (3-6ث)\n\nإيقاف؟",
        'stop_btn': "إيقاف 🛑",
        'locked': "🚫 البوت مغلق حالياً.",
        'back': "🔙 عودة"
    }
}

REASONS = ["Pornography", "Violence", "Scam", "Spam", "Self-harm", "Hate Speech", "Impersonation", "Harassment"]

import json

class BotDB:
    def __init__(self):
        self.path = "bot_data.json"
        try:
            with open(self.path, "r") as f: self.data = json.load(f)
        except:
            self.data = {"locked": False, "users": {}, "total_reports": 0}

    def save(self):
        with open(self.path, "w") as f: json.dump(self.data, f)

    def get_lang(self, uid):
        return self.data["users"].get(str(uid), {}).get("lang", "en")

    def set_lang(self, uid, lang):
        if str(uid) not in self.data["users"]: self.data["users"][str(uid)] = {}
        self.data["users"][str(uid)]["lang"] = lang
        self.save()

import telebot
import time
import random
import threading
from telebot import types
from config import *
from database import BotDB

bot = telebot.TeleBot(API_TOKEN)
db = BotDB()
active_tasks = {}

def gen_inline(btns_dict, row_width=2):
    markup = types.InlineKeyboardMarkup(row_width=row_width)
    buttons = [types.InlineKeyboardButton(text=k, callback_data=v) for k, v in btns_dict.items()]
    markup.add(*buttons)
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id
    db.set_lang(uid, 'en') # لغة افتراضية
    if db.data["locked"] and uid != ADMIN_ID:
        return bot.send_message(message.chat.id, STRINGS['ar']['locked'])
    btns = {"العربية 🇸🇦": "set_ar", "English 🇺🇸": "set_en"}
    bot.send_message(message.chat.id, STRINGS['en']['welcome'], reply_markup=gen_inline(btns), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    uid = call.from_user.id
    cid = call.message.chat.id
    lang = db.get_lang(uid)

    if call.data.startswith("set_"):
        new_lang = call.data.split("_")[1]
        db.set_lang(uid, new_lang)
        show_main(cid, uid)
    elif call.data == "main": show_main(cid, uid)
    elif call.data == "pre_rpt":
        msg = bot.send_message(cid, STRINGS[lang]['target_prompt'])
        bot.register_next_step_handler(msg, process_target, lang)
    elif call.data == "adm_panel" and uid == ADMIN_ID:
        status = "🔒 LOCKED" if db.data["locked"] else "🔓 OPEN"
        btns = {"Toggle Lock": "t_lock", STRINGS[lang]['back']: "main"}
        bot.edit_message_text(f"🛠 Admin Panel\nStatus: {status}", cid, call.message.message_id, reply_markup=gen_inline(btns))
    elif call.data == "t_lock":
        db.data["locked"] = not db.data["locked"]
        db.save()
        callback_handler(call)
    elif call.data == "stop_loop": active_tasks[cid] = False

def show_main(cid, uid):
    lang = db.get_lang(uid)
    btns = {STRINGS[lang]['add_session']: "add_s", STRINGS[lang]['start_report']: "pre_rpt", 
            STRINGS[lang]['dev_btn']: "dev_url", STRINGS[lang]['admin_btn'] if uid == ADMIN_ID else "---": "adm_panel"}
    markup = gen_inline(btns)
    for row in markup.keyboard:
        for btn in row:
            if btn.callback_data == "dev_url": btn.callback_data = None; btn.url = DEV_LINK
    bot.send_message(cid, STRINGS[lang]['main_menu'], reply_markup=markup)

def process_target(message, lang):
    target = message.text
    btns = {"Account": f"tp_acc_{target}", "Post": f"tp_pst_{target}", "Story": f"tp_sty_{target}"}
    bot.send_message(message.chat.id, STRINGS[lang]['type_prompt'], reply_markup=gen_inline(btns))

@bot.callback_query_handler(func=lambda call: call.data.startswith("tp_"))
def select_reason(call):
    lang = db.get_lang(call.from_user.id)
    btns = {r: "start_engine" for r in REASONS}
    bot.edit_message_text(STRINGS[lang]['reason_prompt'], call.message.chat.id, call.message.message_id, reply_markup=gen_inline(btns))

@bot.callback_query_handler(func=lambda call: call.data == "start_engine")
def start_engine(call):
    cid = call.message.chat.id
    lang = db.get_lang(call.from_user.id)
    active_tasks[cid] = True
    threading.Thread(target=reporting_loop, args=(cid, lang)).start()

def reporting_loop(cid, lang):
    sent, fail = 0, 0
    while active_tasks.get(cid):
        time.sleep(random.uniform(3.5, 5.5))
        sent += 1
        db.data["total_reports"] += 1; db.save()
        markup = gen_inline({STRINGS[lang]['stop_btn']: "stop_loop"})
        try: bot.send_video(cid, VIDEO_LINK, caption=STRINGS[lang]['stats'].format(sent, fail), reply_markup=markup, parse_mode="Markdown")
        except: break
    bot.send_message(cid, "✅ Finished/Stopped")

bot.infinity_polling()

