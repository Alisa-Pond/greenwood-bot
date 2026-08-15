import os
import logging
from threading import Thread

import telebot
from flask import Flask

print("🌲 ЗАПУЩЕНО ХРОНІКИ ГРІНВУДУ")


# =========================================================
# FLASK СЕРВЕР ДЛЯ RENDER
# =========================================================

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


server_thread = Thread(
    target=run_flask,
    daemon=True
)

server_thread.start()


# =========================================================
# ЗАВАНТАЖЕННЯ БОТА
# =========================================================

print("🔧 Завантажую services.config...")

from services.config import bot

print("✅ services.config завантажено")


# =========================================================
# НАЛАШТУВАННЯ LOGGING
# =========================================================

telebot.logger.setLevel(logging.INFO)


# =========================================================
# SCHEDULER
# =========================================================

from services.scheduler import start_scheduler


# =========================================================
# РЕЄСТРАЦІЯ HANDLERS
# =========================================================

# =========================================================
# РЕЄСТРАЦІЯ HANDLERS
# =========================================================

import handlers.profile
import handlers.main_quest

import handlers.my_quests.menu

# ---------------------------------------------------------
# ВИКОНАННЯ СПРАВ
# ---------------------------------------------------------

import handlers.complete_activity
import handlers.complete_scroll
import handlers.complete_ritual
import handlers.complete_plant
import handlers.complete_unplanned

# ---------------------------------------------------------
# СУВОЇ
# ---------------------------------------------------------

import handlers.my_quests.scrolls.menu
import handlers.my_quests.scrolls.create
import handlers.my_quests.scrolls.delete

# ---------------------------------------------------------
# РИТУАЛИ
# ---------------------------------------------------------

import handlers.my_quests.rituals.menu
import handlers.my_quests.rituals.create
import handlers.my_quests.rituals.delete

# ---------------------------------------------------------
# ТЕПЛИЦЯ
# ---------------------------------------------------------

import handlers.my_quests.greenhouse.menu
import handlers.my_quests.greenhouse.create
import handlers.my_quests.greenhouse.delete
import handlers.my_quests.greenhouse.archive

# ---------------------------------------------------------
# ЕКСПЕДИЦІЇ
# ---------------------------------------------------------

import handlers.my_quests.expedition.menu
import handlers.my_quests.expedition.start
import handlers.my_quests.expedition.timer
import handlers.my_quests.expedition.complete

# ---------------------------------------------------------
# РЮКЗАК
# ---------------------------------------------------------

import handlers.backpack


print("🎉 Усі основні обробники підключені!")


# =========================================================
# ЗАПУСК
# =========================================================

if __name__ == "__main__":

    print("🧹 Видалення старого Webhook...")

    try:
        bot.remove_webhook()

    except Exception as error:

        print(
            f"⚠️ Помилка видалення webhook: {error}"
        )


    print(
        "🚀 Запуск бота Хроніки Грінвуду..."
    )


    # -----------------------------------------------------
    # ЗАПУСК ПЛАНУВАЛЬНИКА
    # -----------------------------------------------------

    start_scheduler()


    print(
        "⏰ Планувальник підсумків запущено."
    )

    print(
        "🌅 Щоденні підсумки: 07:00 за Києвом."
    )


    # -----------------------------------------------------
    # TELEGRAM POLLING
    # -----------------------------------------------------

    bot.infinity_polling(
        skip_pending=True
    )
