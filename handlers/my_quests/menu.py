from services.config import bot

from keyboards import (
    get_main_menu,
    get_quests_menu
)


print("⚙️ Реєструємо меню 'Мої квести'...")


# =========================
# Відкрити меню "Мої квести"
# =========================

@bot.message_handler(func=lambda message: message.text == "📝 Мої квести")
def open_quests_menu(message):

    text = (
        "📝 <b>Мої квести</b>\n\n"
        "Тут ти плануєш свої пригоди.\n\n"
        "📜 <b>Сувої</b> — одноразові справи.\n"
        "🕯 <b>Ритуали</b> — щоденні звички.\n"
        "🌱 <b>Теплиця</b> — довгострокові цілі.\n"
        "🧭 <b>Експедиції</b> — особливі пригоди (незабаром).\n\n"
        "Оберіть розділ:"
    )

    bot.send_message(
        message.chat.id,
        text,
        parse_mode="HTML",
        reply_markup=get_quests_menu()
    )


# =========================
# Назад у головне меню
# =========================

@bot.message_handler(func=lambda message: message.text == "🔙 Назад")
def back_to_main_menu(message):

    bot.send_message(
        message.chat.id,
        "🌲 Повертаємось до головного меню.",
        reply_markup=get_main_menu()
    )
