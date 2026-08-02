import os
import logging
import telebot
from flask import Flask, request

# 1. Імпортуємо конфіг і бот
from services.config import BOT_TOKEN, bot

# Вмикаємо дебаг-логгер для telebot
telebot.logger.setLevel(logging.DEBUG)

# 2. Імпортуємо обробники команд
print("⏳ Завантажуємо обробники команд...")
import handlers.profile
import handlers.main_quest
import handlers.my_quests
print("✅ Усі обробники успішно підключені до бота!")

# 3. ДІАГНОСТИКА: Перевіряємо завантажені хендлери ДО запуску сервера
print(f"🔍 ПЕРЕВІРКА: Усього зареєстровано хендлерів: {len(bot.message_handlers)}")
for h in bot.message_handlers:
    func_name = getattr(h.get('function'), '__name__', 'Unknown')
    print(f"   - Хендлер: {func_name} | Фільтри: {h.get('filters')}")

# 4. Налаштування Flask-сервера для Webhook
app = Flask(__name__)
WEBHOOK_URL = f"https://greenwood-bot-yw5w.onrender.com/{BOT_TOKEN}"

@app.route('/')
def home():
    return "🌲 Greenwood Chronicles працює!", 200

@app.route('/set_webhook', methods=['GET', 'POST'])
def set_webhook():
    bot.remove_webhook()
    status = bot.set_webhook(url=WEBHOOK_URL)
    if status:
        return f"✅ Вебхук встановлено на: {WEBHOOK_URL}", 200
    else:
        return "❌ Не вдалося встановити вебхук", 500

@app.route('/' + str(BOT_TOKEN), methods=['POST'])
def getMessage():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        
        # Передаємо повідомлення в telebot
        bot.process_new_updates([update])
        return "OK", 200
    else:
        return "Forbidden", 403

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
