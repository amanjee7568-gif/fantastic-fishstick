import os
from flask import Flask, request
import telebot

# Telegram Bot Token (Render dashboard -> Environment Variables -> BOT_TOKEN)
TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    raise ValueError("❌ BOT_TOKEN environment variable not set!")

bot = telebot.TeleBot(TOKEN)

app = Flask(__name__)

# Webhook URL (Render automatically provides external hostname)
WEBHOOK_PATH = f"/{TOKEN}"
WEBHOOK_URL = f"https://{os.environ.get('RENDER_EXTERNAL_HOSTNAME')}{WEBHOOK_PATH}"

# -----------------------
# Telegram Commands
# -----------------------

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "🚀 Bot successfully deployed on Render!\n\n✅ Start button is working.\n\nअब बाकी functions भी चलेंगे।")

@bot.message_handler(commands=['help'])
def help_command(message):
    bot.reply_to(message, "ℹ️ Help Section\n\n/start - Start the bot\n/help - Show help")

@bot.message_handler(func=lambda msg: True)
def echo_all(message):
    bot.reply_to(message, f"आपने कहा: {message.text}")

# -----------------------
# Flask Routes
# -----------------------

@app.route(WEBHOOK_PATH, methods=['POST'])
def webhook():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

@app.route('/', methods=['GET'])
def index():
    return "✅ Bot is running on Render!", 200

# -----------------------
# Main Entrypoint
# -----------------------

if __name__ == "__main__":
    # Remove old webhook, then set new one
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    print(f"🔗 Webhook set to: {WEBHOOK_URL}")

    # Start Flask app
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
