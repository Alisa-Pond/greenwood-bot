import os
import logging
import telebot
from flask import Flask
from threading import Thread

app = Flask(__name__)

@app.route('/')
def home():
    return "Greenwood Chronicles is alive! 🌲"

def run_flask():
    app.run(host="0.0.0.0", port=10000)
# 1. Імпортуємо конфіг і бот
from services.config import BOT_TOKEN, bot

# Вмикаємо логування Telebot
telebot.logger.setLevel(logging.INFO)


# 2. Підключаємо обробники команд
print("⏳ Завантажуємо обробники команд...")
import handlers.profile
import handlers.main_quest
import handlers.my_quests
print("✅ Усі обробники успішно підключені до бота!")

# 3. Перевіряємо завантажені хендлери
print(f"🔍 ПЕРЕВІРКА: Усього зареєстровано хендлерів: {len(bot.message_handlers)}")

if __name__ == "__main__":
    print("🌐 Запускаємо Flask маячок...")
    flask_thread = Thread(target=run_flask)
    flask_thread.start()

    print("🧹 Видаляємо старий Webhook...")
    bot.remove_webhook()

    print("🚀 Запускаємо бота через Long Polling...")
    bot.infinity_polling()
