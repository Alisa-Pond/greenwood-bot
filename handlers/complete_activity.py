from telebot import types

from services.config import bot

# Імпортуємо модулі, щоб завантажити їхні функції.
from handlers import complete_scroll
from handlers import complete_ritual
from handlers import complete_plant
from handlers import complete_unplanned


print("⚙️ Завантажено систему виконання справ...")


# =========================================================
# ГОЛОВНЕ МЕНЮ ВИКОНАННЯ
# =========================================================

@bot.message_handler(
    func=lambda message: message.text == "✅ Виконати справу"
)
def start_complete(message):

    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    markup.row(
        types.KeyboardButton("📜 Виконати сувій"),
        types.KeyboardButton("🔄 Провести ритуал")
    )

    markup.row(
        types.KeyboardButton("🌱 Завершити вирощування")
    )

    markup.row(
        types.KeyboardButton("✨ Зробити поза планом")
    )

    markup.row(
        types.KeyboardButton("🔙 Назад")
    )

    bot.send_message(
        message.chat.id,

        "🪷 <b>Час перетворити зроблене на XP!</b>\n\n"

        "Обери, що саме ти щойно завершила:\n\n"

        "📜 <b>Сувій</b> — запланована одноразова справа.\n"
        "🔄 <b>Ритуал</b> — справа, що повертається за розкладом.\n"
        "🌱 <b>Рослина</b> — велика ціль, яку ти виростила до кінця.\n"
        "✨ <b>Поза планом</b> — корисна справа, якої не було в планах.\n\n"

        "🦇 <b>Марчелло</b> уже тримає перо над книгою XP.",

        parse_mode="HTML",
        reply_markup=markup
    )
