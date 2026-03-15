import re
import requests
from telegram import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

TOKEN = "8599434749:AAHVuIi0h5jAc0RzXxN7lHhbarUN32LQUGU"

ADMIN_ID = 6770328841
ADMIN_USERNAME = "@IH_Maruf"

API_URL = "https://member.daraz.com.bd/user/api/getOtp"
API_KEY = "getotp"

users = {}
logs = []
banned_users = set()


# ---------- KEYBOARD ----------

def user_keyboard():
    return ReplyKeyboardMarkup(
        [
            ["📩 Send SMS", "❓ Help"],
            ["📊 My Stats", "📜 My Messages"],
            ["👨‍💻 Developer"]
        ],
        resize_keyboard=True
    )


def admin_keyboard():
    return ReplyKeyboardMarkup(
        [
            ["📩 Send SMS", "❓ Help"],
            ["📊 View", "👥 Users"],
            ["🚫 Ban User", "✅ Unban User"],
            ["👨‍💻 Developer"]
        ],
        resize_keyboard=True
    )


# ---------- START ----------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    if user.id in banned_users:
        await update.message.reply_text("🚫 You are banned")
        return

    users[user.id] = user.first_name

    text = f"✨ Welcome To Custom SMS Bot\n\nContact Admin\n{ADMIN_USERNAME}"

    if user.id == ADMIN_ID:
        await update.message.reply_text(text, reply_markup=admin_keyboard())
    else:
        await update.message.reply_text(text, reply_markup=user_keyboard())


# ---------- HELP ----------

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "📩 HOW TO SEND SMS\n\n1 Click Send SMS\n2 Enter Number\n3 Write Message\n4 Click Send"
    )


# ---------- DEVELOPER ----------

async def developer(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "👨‍💻 Developer\n\nName: IH MARUF\nTelegram: @IH_Maruf\nTeam: @IH_official"
    )


# ---------- NUMBER VALID ----------

def valid_number(n):
    return bool(re.fullmatch(r"01\d{9}", n))


# ---------- SMS API ----------

def send_sms(number, message):

    url = f"{API_URL}?key={API_KEY}&number={number}&msg={message}"

    try:
        r = requests.get(url, timeout=10)
        print(r.text)
        return r.status_code == 200
    except:
        return False


# ---------- SEND SMS BUTTON ----------

async def send_sms_btn(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id in banned_users:
        await update.message.reply_text("🚫 You are banned")
        return

    context.user_data.clear()
    context.user_data["await_number"] = True

    await update.message.reply_text("📱 Send phone number\nExample: 017xxxxxxxx")


# ---------- TEXT ROUTER ----------

async def router(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    if user.id in banned_users:
        await update.message.reply_text("🚫 You are banned")
        return

    text = update.message.text

    # ADMIN INPUT
    if user.id == ADMIN_ID:

        if context.user_data.get("ban_mode"):

            uid = int(text)
            banned_users.add(uid)

            await update.message.reply_text("🚫 User banned")

            try:
                await context.bot.send_message(uid, "🚫 You have been banned")
            except:
                pass

            context.user_data["ban_mode"] = False
            return

        if context.user_data.get("unban_mode"):

            uid = int(text)
            banned_users.discard(uid)

            await update.message.reply_text("✅ User unbanned")

            context.user_data["unban_mode"] = False
            return

    # NUMBER STEP
    if context.user_data.get("await_number"):

        if not valid_number(text):
            await update.message.reply_text("❌ Invalid number\nSend again")
            return

        context.user_data["number"] = text
        context.user_data["await_number"] = False
        context.user_data["await_msg"] = True

        await update.message.reply_text("✉️ Now send your message")
        return

    # MESSAGE STEP
    if context.user_data.get("await_msg"):

        context.user_data["msg"] = text
        context.user_data["await_msg"] = False

        num = context.user_data["number"]

        kb = [[InlineKeyboardButton("Send SMS", callback_data="send")]]

        await update.message.reply_text(
            f"📱 Number: {num}\n\n💬 Message:\n{text}",
            reply_markup=InlineKeyboardMarkup(kb)
        )


# ---------- SEND FINAL ----------

async def send(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    user = q.from_user

    num = context.user_data.get("number")
    msg = context.user_data.get("msg")

    ok = send_sms(num, msg)

    if ok:
        status = "success"
        await q.message.reply_text("✅ SMS Sent Successfully")
    else:
        status = "failed"
        await q.message.reply_text("❌ SMS Failed")

    logs.append({
        "user": user.id,
        "number": num,
        "msg": msg,
        "status": status
    })


# ---------- USER STATS ----------

async def my_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        f"📊 Bot Stats\n\n👥 Users: {len(users)}\n📩 SMS Sent: {len(logs)}"
    )


# ---------- MY MESSAGES ----------

async def my_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.effective_user.id

    text = "📜 Your SMS History\n\n"

    for l in logs:
        if l["user"] == uid:
            text += f"📱 {l['number']}\n💬 {l['msg']}\n📊 {l['status']}\n\n"

    if text == "📜 Your SMS History\n\n":
        text = "No SMS history"

    await update.message.reply_text(text)


# ---------- USERS ----------

async def users_btn(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    text = "👥 Users List\n\n"

    for u in users:
        text += f"{users[u]} | {u}\n"

    await update.message.reply_text(text)


# ---------- BAN / UNBAN BUTTON ----------

async def ban_btn(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    context.user_data["ban_mode"] = True
    await update.message.reply_text("Send user TG ID to ban")


async def unban_btn(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    context.user_data["unban_mode"] = True
    await update.message.reply_text("Send user TG ID to unban")


# ---------- VIEW LOGS ----------

async def view_btn(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    text = "📊 SMS Logs\n\n"

    for i, l in enumerate(logs, 1):
        text += f"{i}. User:{l['user']}\nNumber:{l['number']}\nMsg:{l['msg']}\nStatus:{l['status']}\n\n"

    await update.message.reply_text(text or "No logs")


# ---------- MAIN ----------

app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_cmd))

app.add_handler(MessageHandler(filters.Regex("^📩 Send SMS$"), send_sms_btn))
app.add_handler(MessageHandler(filters.Regex("^❓ Help$"), help_cmd))
app.add_handler(MessageHandler(filters.Regex("^👨‍💻 Developer$"), developer))

app.add_handler(MessageHandler(filters.Regex("^📊 My Stats$"), my_stats))
app.add_handler(MessageHandler(filters.Regex("^📜 My Messages$"), my_messages))

app.add_handler(MessageHandler(filters.Regex("^📊 View$"), view_btn))
app.add_handler(MessageHandler(filters.Regex("^👥 Users$"), users_btn))

app.add_handler(MessageHandler(filters.Regex("^🚫 Ban User$"), ban_btn))
app.add_handler(MessageHandler(filters.Regex("^✅ Unban User$"), unban_btn))

app.add_handler(CallbackQueryHandler(send, pattern="send"))

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, router))

app.run_polling()
