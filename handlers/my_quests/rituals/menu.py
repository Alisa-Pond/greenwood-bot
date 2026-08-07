from services.config import bot
from keyboards import get_quests_menu, get_rituals_menu


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

@bot.message_handler(func=lambda m: m.text == "🔙 Назад до квестів")
def back_from_rituals(message):

    bot.send_message(
        message.chat.id,
        "📝 Меню квестів",
        reply_markup=get_quests_menu()
    )
