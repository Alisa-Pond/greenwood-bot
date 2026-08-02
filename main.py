import os
import logging
import telebot

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
    # Очищаємо вебхуки, щоб вони не блокували polling
    print("🧹 Видаляємо старий Webhook...")
    bot.remove_webhook()
    
    print("🚀 Запускаємо бота через Long Polling...")
    # infinity_polling автоматично перезапускає опитування при мережевих збоях
    bot.infinity_polling(skip_pending_updates=True)
