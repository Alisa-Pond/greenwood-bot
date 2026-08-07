from services.config import bot
from keyboards import get_scrolls_menu


print("⚙️ Реєструємо меню сувоїв...")


@bot.message_handler(func=lambda message: message.text == "📜 Сувої")
def open_scrolls(message):

    bot.send_message(
        message.chat.id,
        "📜 <b>Сувої</b>\n\n"
        "Тут зберігаються всі твої одноразові справи та завдання.",
        parse_mode="HTML",
        reply_markup=get_scrolls_menu()
    )
