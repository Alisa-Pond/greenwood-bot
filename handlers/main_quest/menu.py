import logging
from telebot import TeleBot
from telebot.types import Message, CallbackQuery

from services.database import get_player, update_player
from handlers.main_quest.chapter1 import start_chapter_1, handle_chapter_1_callback

logger = logging.getLogger(__name__)


def init_main_quest_state() -> dict:
    """Створює початковий стан основного квесту для нового гравця."""
    return {
        "current_chapter": 1,
        "step": 1,
        "completed": False,
        "chapter_data": {}
    }


def register_main_quest_handlers(bot: TeleBot):
    """Реєстрація обробників дій для основного квесту."""

    @bot.message_handler(func=lambda message: message.text in ["📖 Основний квест", "Основний квест"])
    def main_quest_entry_point(message: Message):
        chat_id = message.chat.id
        player = get_player(chat_id)

        if not player:
            bot.send_message(chat_id, "❌ Помилка: профілю персонажа не знайдено.")
            return

        # Зчитуємо або ініціалізуємо main_quest з JSON гравця
        main_quest = player.get("main_quest")
        if not main_quest or not isinstance(main_quest, dict):
            main_quest = init_main_quest_state()
            player["main_quest"] = main_quest
            update_player(chat_id, {"main_quest": main_quest})

        current_chapter = main_quest.get("current_chapter", 1)

        # Маршрутизація по главах
        if current_chapter == 1:
            start_chapter_1(bot, message, player)
        else:
            bot.send_message(
                chat_id,
                "🌲 Ти завершив усі доступні глави основного квесту. Нові пригоди чекають попереду!"
            )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("mq_"))
    def main_quest_callback_router(call: CallbackQuery):
        chat_id = call.message.chat.id
        player = get_player(chat_id)

        if not player:
            bot.answer_callback_query(call.id, "Помилка завантаження даних гравця.", show_alert=True)
            return

        main_quest = player.get("main_quest", {})
        current_chapter = main_quest.get("current_chapter", 1)

        if current_chapter == 1:
            handle_chapter_1_callback(bot, call, player)
        else:
            bot.answer_callback_query(call.id, "Невідома глава квесту.")
