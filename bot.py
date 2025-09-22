import requests
import re
import urllib3
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Disable SSL warning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# === CONFIG ===
API_URL = "https://demo-api-0upx.onrender.com/demo?term={num}"
BOT_TOKEN = os.getenv("BOT_TOKEN")   # Token from Render Environment Variables

# Multiple owners
OWNER_CHAT_IDS = [1362919387, 859230426]   # replace with your IDs
OWNER_USERNAMES = ["@XM5XUM", "@VOFAAMIR"]

# === User Data ===
user_credits = {}       # {chatid: credits}
banned_users = {}       # {chatid: "reason" or "Banned"}

# === Helper function ===
def is_owner(chat_id):
    return chat_id in OWNER_CHAT_IDS

# === API Request ===
def fetch_number_info(number):
    try:
        url = API_URL.format(num=number)
        res = requests.get(url, timeout=10, verify=False)

        if res.status_code != 200:
            return None

        data = res.json()

        if isinstance(data, dict):
            if "data" in data and isinstance(data["data"], list):
                return data["data"]
            return [data]
        if isinstance(data, list):
            return data

        return None
    except Exception:
        return None

# === Format Results ===
def format_results(data):
    results = []
    for idx, info in enumerate(data, 1):
        name = info.get('name') or "N/A"
        father = info.get('fname') or info.get('father_name') or "N/A"
        address = info.get('address') or "N/A"
        mobile = info.get('mobile') or "N/A"
        alt = info.get('alt') or info.get('alt_mobile') or "N/A"
        circle = info.get('circle') or "N/A"
        id_number = info.get('id_number') or "N/A"
        email = info.get('email') or "N/A"

        if father == "N/A" and address != "N/A":
            match = re.search(r"(S/O|W/O)\s+([A-Za-z ]+)", address, re.IGNORECASE)
            if match:
                father = match.group(2).strip()

        results.append(
            f"✅ *Result {idx}*\n\n"
            f"👤 *Name:* {name}\n"
            f"👨‍👦 *Father:* {father}\n"
            f"📍 *Address:* {address}\n"
            f"📱 *Mobile:* {mobile}\n"
            f"☎️ *Alternate:* {alt}\n"
            f"🌍 *Circle:* {circle}\n"
            f"🆔 *ID Number:* {id_number}\n"
            f"✉️ *Email:* {email}\n"
            f"{'='*30}"
        )
    return "\n\n".join(results)

# === Commands ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id

    if chat_id in banned_users and not is_owner(chat_id):
        await update.message.reply_text("⛔ You are banned. Contact the owner.")
        return

    if is_owner(chat_id):
        await update.message.reply_text("👑 Welcome back, Owner! Unlimited access.")
    else:
        if chat_id not in user_credits:
            user_credits[chat_id] = 0
        if user_credits[chat_id] <= 0:
            await update.message.reply_text(
                f"🚫 No credits.\n💳 Contact {', '.join(OWNER_USERNAMES)} to purchase credits."
            )
        else:
            await update.message.reply_text("👋 Welcome! Send me a mobile number to fetch details.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id

    if chat_id in banned_users and not is_owner(chat_id):
        await update.message.reply_text("⛔ You are banned. Contact the owner.")
        return

    number = update.message.text.strip()
    if not number.isdigit():
        await update.message.reply_text("❌ Please send a valid number.")
        return

    if not is_owner(chat_id):
        if user_credits.get(chat_id, 0) <= 0:
            await update.message.reply_text(
                f"🚫 You have 0 credits.\n💳 Contact {', '.join(OWNER_USERNAMES)} to purchase."
            )
            return

    results = fetch_number_info(number)
    if results:
        if not is_owner(chat_id):
            user_credits[chat_id] -= 1
        await update.message.reply_text(format_results(results), parse_mode="Markdown")
    else:
        await update.message.reply_text("⚠️ No details found. (Credits not deducted)")

# === Credit Management ===
async def add_credit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.message.chat_id):
        await update.message.reply_text("🚫 Only owners can add credits.")
        return
    if len(context.args) != 2:
        await update.message.reply_text("⚠️ Usage: /add {chatid} {amount}")
        return
    try:
        target_id = int(context.args[0])
        amount = int(context.args[1])
        user_credits[target_id] = user_credits.get(target_id, 0) + amount
        await update.message.reply_text(
            f"✅ Added {amount} credits to `{target_id}`.\nBalance: {user_credits[target_id]}",
            parse_mode="Markdown"
        )
    except:
        await update.message.reply_text("⚠️ Invalid arguments.")

async def remove_credit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.message.chat_id):
        await update.message.reply_text("🚫 Only owners can remove credits.")
        return
    if len(context.args) != 2:
        await update.message.reply_text("⚠️ Usage: /remove {chatid} {amount}")
        return
    try:
        target_id = int(context.args[0])
        amount = int(context.args[1])
        user_credits[target_id] = max(0, user_credits.get(target_id, 0) - amount)
        await update.message.reply_text(
            f"❌ Removed {amount} credits from `{target_id}`.\nBalance: {user_credits[target_id]}",
            parse_mode="Markdown"
        )
    except:
        await update.message.reply_text("⚠️ Invalid arguments.")

async def check_credit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.message.chat_id):
        await update.message.reply_text("🚫 Only owners can check credits.")
        return
    if len(context.args) != 1:
        await update.message.reply_text("⚠️ Usage: /check {chatid}")
        return
    try:
        target_id = int(context.args[0])
        balance = user_credits.get(target_id, 0)
        await update.message.reply_text(f"📊 User `{target_id}` has {balance} credits.", parse_mode="Markdown")
    except:
        await update.message.reply_text("⚠️ Invalid chatid.")

async def my_credits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    balance = user_credits.get(chat_id, 0) if not is_owner(chat_id) else "Unlimited"
    await update.message.reply_text(f"📊 Your balance: {balance} credits", parse_mode="Markdown")

# === Ban/Unban ===
async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.message.chat_id):
        await update.message.reply_text("🚫 Only owners can ban.")
        return
    if len(context.args) != 1:
        await update.message.reply_text("⚠️ Usage: /ban {chatid}")
        return
    try:
        target_id = int(context.args[0])
        user_credits[target_id] = 0
        banned_users[target_id] = "Banned"
        await update.message.reply_text(f"⛔ User `{target_id}` banned.", parse_mode="Markdown")
    except:
        await update.message.reply_text("⚠️ Invalid chatid.")

async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.message.chat_id):
        await update.message.reply_text("🚫 Only owners can unban.")
        return
    if len(context.args) != 1:
        await update.message.reply_text("⚠️ Usage: /unban {chatid}")
        return
    try:
        target_id = int(context.args[0])
        if target_id in banned_users:
            del banned_users[target_id]
            await update.message.reply_text(f"✅ User `{target_id}` unbanned.", parse_mode="Markdown")
        else:
            await update.message.reply_text(f"ℹ️ User `{target_id}` not banned.", parse_mode="Markdown")
    except:
        await update.message.reply_text("⚠️ Invalid chatid.")

# === User & Banned Lists ===
async def user_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.message.chat_id):
        await update.message.reply_text("🚫 Only owners can view user list.")
        return
    if not user_credits:
        await update.message.reply_text("📭 No users found.")
        return
    lines = ["📋 *User List:*"]
    for uid, credits in user_credits.items():
        status = "⛔ Banned" if uid in banned_users else "✅ Active"
        lines.append(f"👤 `{uid}` → *{credits} credits* ({status})")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

async def banned_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.message.chat_id):
        await update.message.reply_text("🚫 Only owners can view banned list.")
        return
    if not banned_users:
        await update.message.reply_text("📭 No banned users.")
        return
    lines = ["⛔ *Banned Users:*"]
    for uid in banned_users.keys():
        lines.append(f"👤 `{uid}`")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

# === Help ===
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if is_owner(update.message.chat_id):
        commands = (
            "📖 *Owner Commands:*\n\n"
            "/add {chatid} {amount}\n"
            "/remove {chatid} {amount}\n"
            "/check {chatid}\n"
            "/ban {chatid}\n"
            "/unban {chatid}\n"
            "/ulist → Show all users\n"
            "/blist → Show banned users\n"
            "/credits → Check your balance\n"
            "Send a number → Lookup details"
        )
    else:
        commands = (
            "📖 *User Commands:*\n\n"
            "/credits → Check your balance\n"
            "Send a number → Lookup details"
        )
    await update.message.reply_text(commands, parse_mode="Markdown")

# === Run Bot ===
def main():
    if not BOT_TOKEN:
        print("❌ BOT_TOKEN not set. Please add it in Render Environment Variables.")
        return
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add_credit))
    app.add_handler(CommandHandler("remove", remove_credit))
    app.add_handler(CommandHandler("check", check_credit))
    app.add_handler(CommandHandler("credits", my_credits))
    app.add_handler(CommandHandler("ban", ban_user))
    app.add_handler(CommandHandler("unban", unban_user))
    app.add_handler(CommandHandler("ulist", user_list))
    app.add_handler(CommandHandler("blist", banned_list))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()