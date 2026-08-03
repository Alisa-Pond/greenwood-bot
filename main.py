import os
import logging
import telebot
from flask import Flask
from threading import Thread

# 1. Запускаємо веб-сервер Flask у фоні для Cron-job.org
app = Flask(__name__)

@app.route('/')
def home():
    return "Greenwood Chronicles is alive! 🌲", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# Фоновий поток для Flask
server_thread = Thread(target=run_flask)
server_thread.daemon = True
server_thread.start()

# 2. Імпортуємо конфіг та бот
from services.config import BOT_TOKEN, bot

telebot.logger.setLevel(logging.INFO)

# 3. Підключаємо обробники команд
print("⏳ Завантажуємо обробники команд...")
import handlers.profile
import handlers.main_quest
import handlers.my_quests
print("✅ Усі обробники успішно підключені до бота!")

if __name__ == "__main__":
    print("🧹 Видаляємо старий Webhook...")
    bot.remove_webhook()
    
    print("🚀 Запускаємо бота через Long Polling...")
    bot.infinity_polling()
