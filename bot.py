import os
import re
import requests
import urllib3
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# === CONFIG ===
BOT_TOKEN = os.getenv("BOT_TOKEN")  # stored in Render Environment Variables
API_URL = "https://demo-api-0upx.onrender.com/demo?term={num}"

# Flask app
flask_app = Flask(__name__)

# Telegram app
application = Application.builder().token(BOT_TOKEN).build()

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
    except Exception as e:
        print("[ERROR] API request failed:", e, flush=True)
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

# === Handlers ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Send me a mobile number to fetch details.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    number = update.message.text.strip()
    if not number.isdigit():
        await update.message.reply_text("❌ Please send a valid number.")
        return

    results = fetch_number_info(number)
    if results:
        await update.message.reply_text(format_results(results), parse_mode="Markdown")
    else:
        await update.message.reply_text("⚠️ No details found.")

# Register handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# === Flask Routes ===
@flask_app.route('/')
def home():
    return "✅ Bot is alive on Render"

@flask_app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    try:
        data = request.get_json(force=True)
        print("[DEBUG] Incoming update:", data, flush=True)
        update = Update.de_json(data, application.bot)
        application.update_queue.put_nowait(update)
    except Exception as e:
        print("[ERROR] Webhook processing failed:", e, flush=True)
    return "OK"

# === Run ===
if __name__ == "__main__":
    from threading import Thread

    # Run Telegram application in background
    def run_polling():
        print("🤖 Bot started with webhook mode...", flush=True)
        application.run_polling()

    Thread(target=run_polling).start()

    # Run Flask app (Render will serve this)
    flask_app.run(host="0.0.0.0", port=10000)
