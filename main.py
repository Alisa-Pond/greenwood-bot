import os
import traceback
import logging
import telebot
from flask import Flask, request

# 1. Імпортуємо налаштування та об'єкт бота
from config import BOT_TOKEN, bot

# 2. Імпортуємо обробники команд, щоб бот знав, як реагувати на повідомлення
import handlers.my_quests

# Увімкнення логування для відлагодження
telebot.logger.setLevel(logging.DEBUG)

app = Flask(__name__)


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


if __name__ == "__main__":
    # Видаляємо старий вебхук та ставимо новий
    bot.remove_webhook()
    bot.set_webhook(url="https://greenwood-bot-yw5w.onrender.com/" + str(BOT_TOKEN))
    
    # Отримуємо порт від Render
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
