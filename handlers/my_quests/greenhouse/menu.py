from services.config import bot
from keyboards import get_quests_menu, get_greenhouse_menu


print("⚙️ Реєструємо меню теплиці...")


@bot.message_handler(func=lambda message: message.text == "🌱 Теплиця")
def open_greenhouse(message):

    bot.send_message(
        message.chat.id,
        "🌱 <b>Теплиця</b>\n\n"
        "Посади насіння своєї великої мети.",
        parse_mode="HTML",
        reply_markup=get_greenhouse_menu()
    )

@bot.message_handler(func=lambda m: m.text == "🔙 Назад до квестів")
def back_from_greenhouse(message):

    bot.send_message(
        message.chat.id,
        "📝 Меню квестів",
        reply_markup=get_quests_menu()
    )
