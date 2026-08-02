import os
import traceback
import logging
import telebot
from flask import Flask, request

# 1. Завантажуємо конфігурацію та бота
from services.config import BOT_TOKEN, bot

# 2. РЕЄСТРУЄМО ХЕНДЛЕРИ (Імпортуємо їх, щоб декоратори @bot.message_handler спрацювали)
print("⏳ Завантажуємо обробники команд...")
import handlers.profile
import handlers.main_quest
import handlers.my_quests
print("✅ Усі обробники успішно підключені до бота!")

# Вмикаємо дебаг логер TeleBot
telebot.logger.setLevel(logging.DEBUG)

app = Flask(__name__)

WEBHOOK_URL = f"https://greenwood-bot-yw5w.onrender.com/{BOT_TOKEN}"

@app.route('/')
def home():
    return "🌲 Greenwood Chronicles працює!", 200

@app.route('/set_webhook', methods=['GET', 'POST'])
def set_webhook():
    bot.remove_webhook()
    s = bot.set_webhook(url=WEBHOOK_URL)
    if s:
        return f"✅ Вебхук встановлено на: {WEBHOOK_URL}", 200
    else:
        return "❌ Не вдалося встановити вебхук", 500

@app.route('/' + str(BOT_TOKEN), methods=['POST'])
def getMessage():
    try:
        if request.headers.get('content-type', '').startswith('application/json'):
            json_string = request.get_data().decode('utf-8')
            update = telebot.types.Update.de_json(json_string)
            
            # Обробляємо нове оновлення від Telegram
            bot.process_new_updates([update])
            return "!", 200
        else:
            return "Forbidden", 403
    except Exception as e:
        print("❌ КРИТИЧНА ПОМИЛКА ОБРОБКИ ВЕБХУКА:")
        print(traceback.format_exc())
        return "!", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
