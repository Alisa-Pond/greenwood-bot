from services.config import bot
from services.database import get_player


print("⚙️ Реєструємо хендлер рюкзака...")


# =========================================================
# РЮКЗАК
# =========================================================

@bot.message_handler(
    func=lambda message:
        message.text == "🎒 Рюкзак"
)
def show_inventory(message):

    user_id = str(
        message.from_user.id
    )

    current_player = get_player(
        user_id
    )

    inventory = current_player.get(
        "inventory",
        []
    )

    # =====================================================
    # ПОРОЖНІЙ РЮКЗАК
    # =====================================================

    if not inventory:

        bot.send_message(
            message.chat.id,
            (
                "🎒 <b>Твій рюкзак порожній.</b>\n\n"
                "Можливо, час вирушити на пошуки "
                "чогось цікавого? 🐜"
            ),
            parse_mode="HTML"
        )

        return

    # =====================================================
    # НОВИЙ ФОРМАТ
    #
    # {
    #     "rainbow_shell": 3,
    #     "strange_leaf": 2
    # }
    # =====================================================

    if isinstance(
        inventory,
        dict
    ):

        inv_text = (
            "🎒 <b>Вміст твого рюкзака:</b>\n\n"
        )

        for item, count in inventory.items():

            inv_text += (
                f"• {item} ×{count}\n"
            )

    # =====================================================
    # СТАРИЙ ФОРМАТ
    #
    # [
    #     "🐚 Райдужна мушля",
    #     "🐚 Райдужна мушля",
    #     "🍂 Листок"
    # ]
    # =====================================================

    elif isinstance(
        inventory,
        list
    ):

        items_counts = {}

        for item in inventory:

            item = str(item)

            items_counts[item] = (
                items_counts.get(
                    item,
                    0
                ) + 1
            )

        inv_text = (
            "🎒 <b>Вміст твого рюкзака:</b>\n\n"
        )

        for item, count in items_counts.items():

            inv_text += (
                f"• {item} ×{count}\n"
            )

    # =====================================================
    # НЕВІДОМИЙ ФОРМАТ
    # =====================================================

    else:

        bot.send_message(
            message.chat.id,
            (
                "🎒 Не вдалося розібрати вміст "
                "рюкзака. Схоже, гобліни трохи "
                "переплутали записи. 🧌"
            ),
            parse_mode="HTML"
        )

        return

    # =====================================================
    # ВІДПРАВЛЯЄМО РЮКЗАК
    # =====================================================

    bot.send_message(
        message.chat.id,
        inv_text,
        parse_mode="HTML"
    )
