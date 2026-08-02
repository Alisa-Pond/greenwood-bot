import os
import traceback
import logging
import telebot
from flask import Flask, request

# Імпортуємо конфіг з папки services
from services.config import BOT_TOKEN, bot

# 🔴 ОБОВ'ЯЗКОВО ІМПОРТУЄМО ВСІ 3 ФАЙЛИ З ПАПКИ handlers!
import handlers.main_quest
import handlers.my_quests
import handlers.profile

telebot.logger.setLevel(logging.DEBUG)

app = Flask(__name__)

WEBHOOK_URL = f"https://greenwood-bot-yw5w.onrender.com/{BOT_TOKEN}"

# ----------------------------------------------------
# 📌 МАРШРУТИ (ROUTES)
# ----------------------------------------------------

@app.route('/')
def home():
    return "🌲 Greenwood Chronicles працює і чекає на оновлення!", 200


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
        if request.headers.get('content-type', '').startswith('application/json'):
            json_string = request.get_data().decode('utf-8')
            update = telebot.types.Update.de_json(json_string)
            
            # Логування в консоль Render
            if update.message and update.message.text:
                print(f"📩 Текст від {update.message.from_user.id}: '{update.message.text}'")
            elif update.callback_query:
                print(f"🔘 Кнопка від {update.callback_query.from_user.id}: '{update.callback_query.data}'")
                
            bot.process_new_updates([update])
            return "!", 200
        else:
            return "Forbidden", 403
    except Exception as e:
        print("❌ КРИТИЧНА ПОМИЛКА:")
        print(traceback.format_exc())
        return "!", 200


if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
