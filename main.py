import os
import logging
import telebot
from flask import Flask
from threading import Thread


# ==========================
# 1. Flask сервер для Render
# ==========================

app = Flask(__name__)


@app.route('/')
def home():
    return "Greenwood Chronicles is alive! 🌲", 200


def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
        use_reloader=False
    )


# ==========================
# 2. Імпорт бота
# ==========================

from services.config import bot

telebot.logger.setLevel(logging.INFO)


# ==========================
# 3. Завантаження хендлерів
# ==========================

print("⏳ Завантажуємо обробники команд...")

import handlers.profile
import handlers.main_quest
import handlers.my_quests

print("✅ Усі обробники успішно підключені до бота!")


# ==========================
# 4. Запуск
# ==========================

if __name__ == "__main__":

    # Запускаємо Flask у фоні
    server_thread = Thread(target=run_flask)
    server_thread.daemon = True
    server_thread.start()

    print("🧹 Видаляємо старий Webhook...")
    bot.remove_webhook()

    print("🚀 Запускаємо бота через Long Polling...")

    bot.infinity_polling()
