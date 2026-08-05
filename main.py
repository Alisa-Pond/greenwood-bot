import os
import logging
from threading import Thread
import telebot
from flask import Flask
print("🌲 ЗАПУЩЕНО НОВИЙ MAIN.PY ХРОНІК ГРІНВУДУ")
# 1. Запускаємо веб-сервер Flask у фоні для зовнішніх Pinger/Cron сервісів
app = Flask(__name__)

@app.route('/')
def home():
    return "Хроніки Грінвуду оживають! 🌲", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    # use_reloader=False важливо, щоб Flask не створював дублюючі потоки
    app.run(host="0.0.0.0", port=port, use_reloader=False)

# Фоновий потік для Flask
server_thread = Thread(target=run_flask)
server_thread.daemon = True
server_thread.start()

print("🔧 Завантажую services.config...")

from services.config import BOT_TOKEN, bot

print("✅ services.config завантажено")

telebot.logger.setLevel(logging.INFO)

print("⏳ Завантаження profile...")
import handlers.profile
print("✅ profile готовий")

print("⏳ Завантаження main_quest...")
import handlers.main_quest
print("✅ main_quest готовий")

print("⏳ Завантаження quests...")
import handlers.quests
print("✅ quests готовий")

print("⏳ Завантаження scrolls...")
import handlers.scrolls
print("✅ scrolls готовий")

print("⏳ Завантаження rituals...")
import handlers.rituals
print("✅ rituals готовий")

print("⏳ Завантаження greenhouse...")
import handlers.greenhouse
print("✅ greenhouse готовий")

print("🎉 Усі обробники успішно підключені!")

if __name__ == "__main__":
    print("🧹 Видалення старого Webhook...")
    try:
        bot.remove_webhook()
    except Exception as e:
        print(f"⚠️ Не вдалося видалити вебхук: {e}")
    
    print("🚀 Запуск бота Хроніки Грінвуду (Long Polling)...")
    # skip_pending=True захищає від спаму старок повідомлень та конфліктів при перезапуску
    bot.infinity_polling()
