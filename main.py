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

# 2. Імпортуємо конфіг та екземпляр бота
from services.config import BOT_TOKEN, bot

telebot.logger.setLevel(logging.INFO)

# 3. Підключаємо обробники команд (Handlers)
print("⏳ Завантаження обробників команд...")
import handlers.profile
import handlers.main_quest
import handlers.quests
import handlers.scrolls
import handlers.rituals
import handlers.greenhouse
print("✅ Усі обробники успішно підключені до бота!")

if __name__ == "__main__":
    print("🧹 Видалення старого Webhook...")
    try:
        bot.remove_webhook()
    except Exception as e:
        print(f"⚠️ Не вдалося видалити вебхук: {e}")
    
    print("🚀 Запуск бота Хроніки Грінвуду (Long Polling)...")
    # skip_pending=True захищає від спаму старок повідомлень та конфліктів при перезапуску
    bot.infinity_polling()
