from telebot import types

from services.config import bot
from services.database import get_player

# Імпорт цих модулів реєструє їхні @bot.message_handler.
from handlers import complete_scroll, complete_ritual, complete_plant, complete_unplanned  # noqa: F401,E402

print("⚙️ Завантажено систему виконання справ...")


@bot.message_handler(func=lambda message: message.text == "✅ Виконати справу")
def start_complete(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(
        types.KeyboardButton("📜 Виконати сувій"),
        types.KeyboardButton("🔄 Провести ритуал"),
    )
    markup.row(types.KeyboardButton("🌱 Завершити вирощування"))
    markup.row(types.KeyboardButton("✨ Зробити поза планом"))
    markup.row(types.KeyboardButton("🔙 Назад"))

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
        reply_markup=markup,
    )
