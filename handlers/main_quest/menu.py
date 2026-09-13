from telebot import types

from services.config import bot
from services.database import get_player

from keyboards import get_main_menu


# =========================================================
# ОСНОВНИЙ КВЕСТ
# =========================================================

@bot.message_handler(
    func=lambda message: message.text == "📖 Основний квест"
)
def main_quest_menu(message):

    user_id = str(
        message.from_user.id
    )

    player = get_player(
        user_id
    )

    if not player:
        bot.send_message(
            message.chat.id,
            "🌲 Не вдалося знайти твого персонажа."
        )
        return

    main_quest = player.get(
        "main_quest",
        {}
    )

    chapter = main_quest.get(
        "chapter",
        1
    )

    current_task = main_quest.get(
        "current_task"
    )

    # =====================================================
    # ГЛАВА 1
    # =====================================================

    if chapter == 1:

        from handlers.main_quest.chapter1 import show_chapter1

        show_chapter1(
            message,
            player,
            current_task
        )

        return

    # =====================================================
    # ЯКЩО ГЛАВА ЩЕ НЕ РЕАЛІЗОВАНА
    # =====================================================

    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    markup.row(
        types.KeyboardButton("🔙 Назад")
    )

    bot.send_message(
        message.chat.id,
        "🌲 Ця частина історії Грінвуду ще не відкрита.",
        reply_markup=markup
    )


# =========================================================
# НАЗАД
# =========================================================

@bot.message_handler(
    func=lambda message: message.text == "🔙 Назад"
)
def main_quest_back(message):

    bot.send_message(
        message.chat.id,
        "🌲 Ти повернувся до головної стежки.",
        reply_markup=get_main_menu()
    )
