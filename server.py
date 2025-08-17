import os
import logging
from flask import Flask, request
import telebot

# Logging
logging.basicConfig(level=logging.INFO)

# Env Variables
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "PASTE_YOUR_TOKEN_HERE")
URL = os.getenv("RENDER_EXTERNAL_URL", "https://super-bot-render-4.onrender.com")

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# --- Handlers ---

@bot.message_handler(commands=['start'])
def start(message):
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row("🎮 Games", "💳 Wallet")
    keyboard.row("⭐ Premium", "ℹ Help")
    bot.send_message(message.chat.id, "Welcome! 👋\nChoose an option:", reply_markup=keyboard)

@bot.message_handler(func=lambda m: m.text == "ℹ Help")
def help_cmd(message):
    bot.send_message(message.chat.id,
        "🤖 Bot Help:\n"
        "- 🎮 Games → Play fun games\n"
        "- 💳 Wallet → Manage coins\n"
        "- ⭐ Premium → Get premium features\n"
        "- Admins can use /broadcast <msg>"
    )

@bot.message_handler(func=lambda m: m.text == "💳 Wallet")
def wallet(message):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("Check Balance", callback_data="check_balance"))
    markup.add(telebot.types.InlineKeyboardButton("Add Funds", callback_data="add_funds"))
    bot.send_message(message.chat.id, "💳 Wallet Menu:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "⭐ Premium")
def premium(message):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("Buy Premium", callback_data="buy_premium"))
    bot.send_message(message.chat.id, "⭐ Premium Options:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "🎮 Games")
def games(message):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("Mini Game", callback_data="game1"))
    bot.send_message(message.chat.id, "🎮 Choose a game:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callbacks(call):
    if call.data == "check_balance":
        bot.answer_callback_query(call.id, "Your balance: 100 coins")
    elif call.data == "add_funds":
        bot.answer_callback_query(call.id, "Funds added successfully ✅")
    elif call.data == "buy_premium":
        bot.answer_callback_query(call.id, "Premium activated 🎉")
    elif call.data == "game1":
        bot.answer_callback_query(call.id, "Mini game started! 🎮")

# --- Admin Broadcast ---
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "0").split(",") if x.isdigit()]

@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.from_user.id in ADMIN_IDS:
        text = message.text.replace("/broadcast", "").strip()
        if text:
            bot.send_message(message.chat.id, "📢 Broadcasting...")
            # Normally send to all users, here demo only:
            bot.send_message(message.chat.id, f"✅ Sent: {text}")
        else:
            bot.send_message(message.chat.id, "❌ Usage: /broadcast <msg>")
    else:
        bot.send_message(message.chat.id, "❌ You are not admin.")

# --- Flask Webhook ---
@app.route('/webhook', methods=['POST'])
def webhook():
    json_str = request.get_data().decode('UTF-8')
    update = telebot.types.Update.de_json(json_str)
    bot.process_new_updates([update])
    return "OK", 200

@app.route('/')
def index():
    return "🤖 Bot is running!"

if __name__ == "__main__":
    webhook_url = f"{URL}/webhook"
    bot.remove_webhook()
    bot.set_webhook(url=webhook_url)
    logging.info(f"Webhook set to {webhook_url}")
    app.run(host="0.0.0.0", port=8000)
