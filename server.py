import os
import logging
from flask import Flask, request, jsonify, abort
import telebot
from telebot import types

# -------------------
# Logging
# -------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
log = logging.getLogger("server")

# -------------------
# Config / ENV
# -------------------
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN env var missing!")

# Render पर अक्सर external URL env var नहीं होता,
# इसलिए तुम WEBHOOK_BASE_URL खुद सेट कर सकते हो (https://<your-app>.onrender.com)
WEBHOOK_BASE_URL = (
    os.environ.get("WEBHOOK_BASE_URL")
    or os.environ.get("RENDER_EXTERNAL_URL")  # अगर Render दे रहा हो
)
if not WEBHOOK_BASE_URL:
    log.warning("WEBHOOK_BASE_URL not set. Set it in Render -> Environment.")

PORT = int(os.environ.get("PORT", "8000"))
ADMIN_ID = os.environ.get("ADMIN_ID")  # optional (string), जैसे "123456789"

# -------------------
# Bot & App
# -------------------
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML", threaded=False)
app = Flask(__name__)

# -------------------
# Simple In-Memory Store (demo)
# NOTE: Production में DB यूज करो.
# -------------------
USERS = {}   # {user_id: {"coins": int, "premium": bool}}
WALLETS = {} # {user_id: {"usdt": float, "btc": float, "eth": float}}

def ensure_user(user_id: int):
    if user_id not in USERS:
        USERS[user_id] = {"coins": 100, "premium": False}
        WALLETS[user_id] = {"usdt": 5.0, "btc": 0.0001, "eth": 0.01}

# -------------------
# Keyboards
# -------------------
def main_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("💰 Wallet", "🪙 Balance")
    kb.row("⭐ Premium", "🎮 Play")
    kb.row("ℹ️ Help")
    return kb

def admin_menu():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("👥 Users Count", "➕ Add Coins")
    kb.row("⬅️ Back")
    return kb

# -------------------
# Commands
# -------------------
@bot.message_handler(commands=["start"])
def cmd_start(message: types.Message):
    user = message.from_user
    ensure_user(user.id)
    text = (
        f"नमस्ते <b>{user.first_name or 'User'}</b> 👋\n"
        f"आपका यूजर ID: <code>{user.id}</code>\n\n"
        "यहाँ से शुरू करें:\n"
        "• 💰 Wallet – आपके क्रिप्टो बैलेंस\n"
        "• 🪙 Balance – कॉइन बैलेंस\n"
        "• ⭐ Premium – प्रीमियम जानकारी\n"
        "• 🎮 Play – छोटा गेम\n"
        "• ℹ️ Help – कमांड सूची\n"
    )
    bot.reply_to(message, text, reply_markup=main_menu())

@bot.message_handler(commands=["help"])
def cmd_help(message: types.Message):
    text = (
        "कमांड सूची:\n"
        "/start – बॉट शुरू करें\n"
        "/help – मदद\n"
        "/wallet – क्रिप्टो बैलेंस\n"
        "/balance – कॉइन बैलेंस\n"
        "/premium – प्रीमियम स्टेटस\n"
        "/play – छोटा गेम\n"
        "/admin – (केवल एडमिन)\n"
    )
    bot.reply_to(message, text, reply_markup=main_menu())

@bot.message_handler(commands=["wallet"])
def cmd_wallet(message: types.Message):
    uid = message.from_user.id
    ensure_user(uid)
    w = WALLETS.get(uid, {})
    text = (
        "🧾 <b>Wallet</b>\n"
        f"USDT: <b>{w.get('usdt', 0):.2f}</b>\n"
        f"BTC: <b>{w.get('btc', 0):.8f}</b>\n"
        f"ETH: <b>{w.get('eth', 0):.6f}</b>\n"
    )
    bot.reply_to(message, text, reply_markup=main_menu())

@bot.message_handler(commands=["balance"])
def cmd_balance(message: types.Message):
    uid = message.from_user.id
    ensure_user(uid)
    coins = USERS[uid]["coins"]
    bot.reply_to(message, f"🪙 आपके कॉइन: <b>{coins}</b>", reply_markup=main_menu())

@bot.message_handler(commands=["premium"])
def cmd_premium(message: types.Message):
    uid = message.from_user.id
    ensure_user(uid)
    is_premium = USERS[uid]["premium"]
    status = "ON ✅" if is_premium else "OFF ❌"
    bot.reply_to(message, f"⭐ Premium: <b>{status}</b>", reply_markup=main_menu())

@bot.message_handler(commands=["play"])
def cmd_play(message: types.Message):
    uid = message.from_user.id
    ensure_user(uid)
    # Simple guess game
    import random
    secret = random.randint(1, 5)
    if secret in (1, 2):
        USERS[uid]["coins"] += 10
        bot.reply_to(message, "🎉 आपने 10 कॉइन जीते! (/balance देखें)", reply_markup=main_menu())
    else:
        lose = min(5, USERS[uid]["coins"])
        USERS[uid]["coins"] -= lose
        bot.reply_to(message, f"🙈 आप हार गए, {lose} कॉइन कटे. (/balance)", reply_markup=main_menu())

@bot.message_handler(commands=["admin"])
def cmd_admin(message: types.Message):
    if not ADMIN_ID or str(message.from_user.id) != str(ADMIN_ID):
        bot.reply_to(message, "⛔ यह कमांड केवल एडमिन के लिए है.", reply_markup=main_menu())
        return
    bot.reply_to(message, "🛠 Admin Panel", reply_markup=admin_menu())

# -------------------
# Text Buttons Handling
# -------------------
@bot.message_handler(func=lambda m: m.text in ["💰 Wallet", "🪙 Balance", "⭐ Premium", "🎮 Play", "ℹ️ Help"])
def button_router(message: types.Message):
    txt = message.text
    if txt == "💰 Wallet":
        return cmd_wallet(message)
    if txt == "🪙 Balance":
        return cmd_balance(message)
    if txt == "⭐ Premium":
        return cmd_premium(message)
    if txt == "🎮 Play":
        return cmd_play(message)
    if txt == "ℹ️ Help":
        return cmd_help(message)

# Admin buttons
@bot.message_handler(func=lambda m: m.text in ["👥 Users Count", "➕ Add Coins", "⬅️ Back"])
def admin_buttons(message: types.Message):
    if not ADMIN_ID or str(message.from_user.id) != str(ADMIN_ID):
        return bot.reply_to(message, "⛔ केवल एडमिन.", reply_markup=main_menu())
    if message.text == "👥 Users Count":
        bot.reply_to(message, f"कुल यूज़र्स: <b>{len(USERS)}</b>", reply_markup=admin_menu())
    elif message.text == "➕ Add Coins":
        bot.reply_to(message, "किस यूज़र ID को कितने कॉइन? Format: <code>/give user_id coins</code>\nउदा: <code>/give 123456789 50</code>", reply_markup=admin_menu())
    elif message.text == "⬅️ Back":
        bot.reply_to(message, "मुख्य मेन्यू", reply_markup=main_menu())

@bot.message_handler(commands=["give"])
def cmd_give(message: types.Message):
    # Only admin
    if not ADMIN_ID or str(message.from_user.id) != str(ADMIN_ID):
        return bot.reply_to(message, "⛔ केवल एडमिन.", reply_markup=main_menu())
    try:
        parts = message.text.strip().split()
        # /give <user_id> <coins>
        if len(parts) != 3:
            return bot.reply_to(message, "Format: <code>/give user_id coins</code>")
        uid = int(parts[1])
        amt = int(parts[2])
        ensure_user(uid)
        USERS[uid]["coins"] += amt
        bot.reply_to(message, f"✅ {uid} को {amt} कॉइन दे दिये गए.", reply_markup=admin_menu())
    except Exception as e:
        log.exception("give error")
        bot.reply_to(message, f"❌ Error: {e}")

# -------------------
# Default text (अब echo नहीं करेगा)
# -------------------
@bot.message_handler(func=lambda m: True, content_types=["text"])
def fallback_text(message: types.Message):
    bot.reply_to(
        message,
        "मैंने समझा नहीं। नीचे दिए बटनों/कमांड्स का उपयोग करें:\n"
        "• /start • /help • /wallet • /balance • /premium • /play",
        reply_markup=main_menu(),
    )

# -------------------
# Webhook setup & Flask
# -------------------
@app.route("/", methods=["GET", "HEAD"])
def health():
    return "OK", 200

@app.route("/webhook/<token>", methods=["POST"])
def webhook(token):
    # Basic security: path token must match the bot token
    if token != BOT_TOKEN:
        abort(403)
    if request.headers.get("content-type") == "application/json":
        json_update = request.get_json(force=True)
        update = telebot.types.Update.de_json(json_update)
        bot.process_new_updates([update])
        return jsonify(ok=True)
    abort(400)

def set_webhook():
    if not WEBHOOK_BASE_URL:
        log.error("WEBHOOK_BASE_URL missing. Set it in env and redeploy.")
        return False
    url = f"{WEBHOOK_BASE_URL.rstrip('/')}/webhook/{BOT_TOKEN}"
    # Drop pending updates so पुराने संदेश न आएँ
    ok = bot.set_webhook(url=url, drop_pending_updates=True)
    if ok:
        log.info(f"🔗 Webhook set to: {url}")
    else:
        log.error("Failed to set webhook (Telegram returned False).")
    return ok

if __name__ == "__main__":
    # Reset & set webhook safely
    try:
        bot.remove_webhook()
    except Exception:
        pass
    set_webhook()
    app.run(host="0.0.0.0", port=PORT)
