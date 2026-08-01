import os
import traceback
import logging
import telebot
from flask import Flask, request

from config import BOT_TOKEN, bot
import handlers.my_quests

telebot.logger.setLevel(logging.DEBUG)

app = Flask(__name__)

# Встановлюємо вебхук одразу під час ініціалізації додатка (для Render / Gunicorn)
WEBHOOK_URL = "https://greenwood-bot-yw5w.onrender.com/" + str(BOT_TOKEN)
try:
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    print("✅ Вебхук успішно встановлено на:", WEBHOOK_URL)
except Exception as e:
    print("❌ Помилка встановлення вебхука:", e)


# ----------------------------------------------------
# 📌 ВЕБХУКИ ТА СЕРВЕР (Flask)
# ----------------------------------------------------

@app.route('/')
def home():
    return "🌲 Greenwood Chronicles працює і чекає на оновлення!", 200


@app.route('/' + str(BOT_TOKEN), methods=['POST'])
def getMessage():
    try:
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "!", 200
    except Exception as e:
        print("❌ КРИТИЧНА ПОМИЛКА В ЛОГІЦІ БОТА:")
        print(traceback.format_exc())
        return "!", 200


# Цей блок спрацює тільки при локальному запуску `python main.py`
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
