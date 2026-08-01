import os
import traceback
import logging
import telebot
from flask import Flask, request

# Імпортуємо конфіг та бота
from config import BOT_TOKEN, bot

# Обов'язково імпортуємо обробники команд!
import handlers.my_quests

telebot.logger.setLevel(logging.DEBUG)

app = Flask(__name__)

WEBHOOK_URL = f"https://greenwood-bot-yw5w.onrender.com/{BOT_TOKEN}"


# ----------------------------------------------------
# 📌 МАРШРУТИ (ROUTES)
# ----------------------------------------------------

@app.route('/')
def home():
    return "🌲 Greenwood Chronicles працює і чекає на оновлення!", 200


# Спеціальний маршрут для швидкого встановлення вебхука через браузер
@app.route('/set_webhook', methods=['GET', 'POST'])
def set_webhook():
    bot.remove_webhook()
    s = bot.set_webhook(url=WEBHOOK_URL)
    if s:
        return f"✅ Вебхук успішно встановлено на: {WEBHOOK_URL}", 200
    else:
        return "❌ Не вдалося встановити вебхук", 500


@app.route('/' + str(BOT_TOKEN), methods=['POST'])
def getMessage():
    try:
        # Приймаємо будь-які варіанти JSON від Telegram
        if request.headers.get('content-type', '').startswith('application/json'):
            json_string = request.get_data().decode('utf-8')
            update = telebot.types.Update.de_json(json_string)
            
            # Логуємо вхідні повідомлення в консоль Render
            if update.message and update.message.text:
                print(f"📩 Отримано текст: '{update.message.text}' від ID: {update.message.from_user.id}")
            elif update.callback_query:
                print(f"🔘 Натиснуто Inline-кнопку: '{update.callback_query.data}'")
                
            bot.process_new_updates([update])
            return "!", 200
        else:
            print("⚠️ Запит без Content-Type application/json")
            return "Forbidden", 403
    except Exception as e:
        print("❌ КРИТИЧНА ПОМИЛКА ПРИ ОБРОБЦІ ПОВІДОМЛЕННЯ:")
        print(traceback.format_exc())
        return "!", 200


# Для локального запуску через python main.py
if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
