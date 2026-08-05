from services.config import bot
from services.database import get_player, update_player
from services.utils import clean_skin_tones
from keyboards import get_scrolls_menu
from telebot import types
import re
print("📜 scrolls.py ЗАВАНТАЖЕНО")

@bot.message_handler(func=lambda message: message.text == "📜 Сувої завдань")
def show_scrolls_menu(message):
    print("📜 Натиснуто кнопку Сувої завдань")

    user_id = str(message.from_user.id)
    player = get_player(user_id)

    scrolls = player.get("quests", {}).get("scrolls", [])

    bot.send_message(
        message.chat.id,
        f"Тест. Знайдено сувоїв: {len(scrolls)}",
        reply_markup=get_scrolls_menu()
    )
