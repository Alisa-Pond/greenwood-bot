from telebot import types

from services.config import bot
from services.database import get_player

from handlers.main_quest.chapter1 import show_chapter1


# =========================================================
# 📖 ОСНОВНИЙ КВЕСТ
# =========================================================

@bot.message_handler(
    func=lambda message:
        message.text == "📖 Основний квест"
)
def main_quest_menu(
    message
):

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

    main_quest = (
        player.get(
            "main_quest"
        )
        or {}
    )

    chapter = main_quest.get(
        "chapter",
        1
    )

    current_task = main_quest.get(
        "current_task"
    )

    if chapter == 1:

        show_chapter1(
            message,
            player,
            current_task
        )

        return

    bot.send_message(
        message.chat.id,
        "🌲 Ця частина історії поки що недоступна."
    )
