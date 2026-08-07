from services.config import bot
from keyboards import get_quests_menu, get_expeditions_menu


print("⚙️ Реєструємо меню експедицій...")


@bot.message_handler(func=lambda message: message.text == "🧭 Експедиції")
def open_expeditions(message):

    bot.send_message(
        message.chat.id,
        "🧭 <b>Експедиції</b>\n\n"
        "Цей розділ ще розробляється.",
        parse_mode="HTML",
        reply_markup=get_expeditions_menu()
    )
    
@bot.message_handler(func=lambda m: m.text == "🔙 Назад до квестів")
def back_from_expeditions(message):

    bot.send_message(
        message.chat.id,
        "📝 Меню квестів",
        reply_markup=get_quests_menu()
    )
