from services.config import bot
from keyboards import get_quests_menu, get_scrolls_menu


print("⚙️ Реєструємо меню сувоїв...")


@bot.message_handler(func=lambda message: message.text == "📜 Сувої")
def open_scrolls(message):

    bot.send_message(
    message.chat.id,
    "📜 <b>Сувої</b>\n\n"
    "🦇 <b>Марчелло🦇:</b> Ось і вони. "
    "Усі справи, які ти урочисто вирішила виконати, "
    "записані тут. Тепер залишилося лише виконати їх. ",
    parse_mode="HTML",
    reply_markup=get_scrolls_menu()
)

@bot.message_handler(func=lambda m: m.text == "🔙 Назад до квестів")
def back_from_scrolls(message):

    bot.send_message(
        message.chat.id,
        "📝 Меню квестів",
        reply_markup=get_quests_menu()
    )
