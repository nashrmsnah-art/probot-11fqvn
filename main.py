import telebot
import time
import random
import threading
from telebot import types
from config import *
from database import BotDB

bot = telebot.TeleBot(API_TOKEN)
db = BotDB()
active_loops = {}

def make_kb(btns, row=2):
    markup = types.InlineKeyboardMarkup(row_width=row)
    markup.add(*[types.InlineKeyboardButton(text=k, callback_data=v) for k, v in btns.items()])
    return markup

@bot.message_handler(commands=['start'])
def welcome(message):
    uid = message.from_user.id
    if db.data["locked"] and uid != ADMIN_ID:
        return bot.send_message(message.chat.id, STRINGS['ar']['lock_msg'])
    
    kb = {"العربية 🇸🇦": "set_ar", "English 🇺🇸": "set_en"}
    bot.send_message(message.chat.id, STRINGS['en']['start'], reply_markup=make_kb(kb), parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def handle_all(call):
    uid, cid = call.from_user.id, call.message.chat.id
    user = db.get_user(uid)
    lang = user["lang"]

    if call.data.startswith("set_"):
        new_lang = call.data.split("_")[1]
        db.set_lang(uid, new_lang)
        render_main(cid, uid, new_lang)

    elif call.data == "main_menu":
        render_main(cid, uid, lang)

    elif call.data == "start_op":
        msg = bot.send_message(cid, STRINGS[lang]['target_msg'])
        bot.register_next_step_handler(msg, choose_type, lang)

    elif call.data == "admin":
        if uid != ADMIN_ID: return
        status = "🔒 LOCKED" if db.data["locked"] else "🔓 OPEN"
        txt = f"🛠 **Admin Panel**\nUsers: {len(db.data['users'])}\nTotal Ops: {db.data['total_ops']}\nBot: {status}"
        bot.edit_message_text(txt, cid, call.message.message_id, reply_markup=make_kb({"Toggle Lock": "lock", "Back": "main_menu"}), parse_mode="Markdown")

    elif call.data == "lock":
        db.data["locked"] = not db.data["locked"]; db.save()
        handle_all(call)

    elif call.data == "stop":
        active_loops[cid] = False
        bot.answer_callback_query(call.id, "Stopping process...")

def render_main(cid, uid, lang):
    btns = {STRINGS[lang]['add_session']: "add", STRINGS[lang]['start_report']: "start_op", 
            STRINGS[lang]['dev_btn']: "dev_url", STRINGS[lang]['admin_btn'] if uid == ADMIN_ID else "---": "admin"}
    markup = make_kb(btns)
    for r in markup.keyboard:
        for b in r:
            if b.callback_data == "dev_url": b.callback_data = None; b.url = DEV_LINK
    bot.send_message(cid, STRINGS[lang]['main'], reply_markup=markup, parse_mode="Markdown")

def choose_type(message, lang):
    t = message.text
    btns = {"Account": f"t_acc_{t}", "Post": f"t_pst_{t}", "Story": f"t_sty_{t}"}
    bot.send_message(message.chat.id, STRINGS[lang]['type_msg'], reply_markup=make_kb(btns))

@bot.callback_query_handler(func=lambda call: call.data.startswith("t_"))
def choose_reason(call):
    lang = db.get_user(call.from_user.id)["lang"]
    btns = {r: "run_engine" for r in REASONS}
    bot.edit_message_text(STRINGS[lang]['reason_msg'], call.message.chat.id, call.message.message_id, reply_markup=make_kb(btns))

@bot.callback_query_handler(func=lambda call: call.data == "run_engine")
def engine_start(call):
    cid = call.message.chat.id
    lang = db.get_user(call.from_user.id)["lang"]
    active_loops[cid] = True
    threading.Thread(target=report_loop, args=(cid, lang)).start()

def report_loop(cid, lang):
    ok, no = 0, 0
    kb = make_kb({STRINGS[lang]['stop_btn']: "stop"})
    while active_loops.get(cid):
        time.sleep(random.uniform(3.5, 5.5)) # حماية ضد الحظر
        ok += 1; db.data["total_ops"] += 1; db.save()
        caption = STRINGS[lang]['stats'].format(ok, no)
        try: bot.send_video(cid, VIDEO_URL, caption=caption, reply_markup=kb, parse_mode="Markdown")
        except: break
    bot.send_message(cid, "🏁 Process Terminated.")

bot.infinity_polling()
