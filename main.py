import os
import logging
from threading import Thread

import telebot
from flask import Flask

print("🌲 ЗАПУЩЕНО ХРОНІКИ ГРІНВУДУ")


# =========================
# Flask сервер для Render
# =========================

app = Flask(__name__)


@app.route("/")
def home():
    return "Хроніки Грінвуду оживають! 🌲", 200


def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(
        host="0.0.0.0",
        port=port,
        use_reloader=False
    )


server_thread = Thread(target=run_flask)
server_thread.daemon = True
server_thread.start()


# =========================
# Завантаження бота
# =========================

print("🔧 Завантажую services.config...")

from services.config import bot

print("✅ services.config завантажено")


telebot.logger.setLevel(logging.INFO)


# =========================
# Реєстрація handlers
# =========================

print("⏳ Завантаження profile...")
import handlers.profile
print("✅ profile готовий")


print("⏳ Завантаження main_quest...")
import handlers.main_quest
print("✅ main_quest готовий")


print("⏳ Завантаження my_quests...")
import handlers.my_quests.menu
print("✅ my_quests готовий")


print("⏳ Завантаження backpack...")
import handlers.backpack
print("✅ backpack готовий")


print("🎉 Усі основні обробники підключені!")


# =========================
# Запуск
# =========================

if __name__ == "__main__":

    print("🧹 Видалення старого Webhook...")

    try:
        bot.remove_webhook()
    except Exception as e:
        print(f"⚠️ Помилка видалення webhook: {e}")


    print("🚀 Запуск бота Хроніки Грінвуду...")

    bot.infinity_polling(
        skip_pending=True
    )
