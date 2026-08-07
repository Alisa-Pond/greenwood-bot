from services.config import bot
from keyboards import get_rituals_menu


print("⚙️ Реєструємо меню ритуалів...")


@bot.message_handler(func=lambda message: message.text == "🕯 Ритуали")
def open_rituals(message):

    bot.send_message(
        message.chat.id,
        "🕯 <b>Ритуали</b>\n\n"
        "Тут живуть твої щоденні звички.",
        parse_mode="HTML",
        reply_markup=get_rituals_menu()
    )
