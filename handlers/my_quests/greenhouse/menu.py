from services.config import bot
from keyboards import get_greenhouse_menu


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
