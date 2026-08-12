from telebot import types

from services.config import bot
from services.database import get_player


print("🧭 Реєструємо хендлер експедицій...")


# =========================================================
# КЛАВІАТУРИ
# =========================================================

def expedition_menu_keyboard(active_expedition=None):
    """
    Створює клавіатуру меню Експедицій
    залежно від поточного стану експедиції.
    """

    keyboard = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    # -----------------------------------------------------
    # Експедиція НЕ активна
    # -----------------------------------------------------

    if not active_expedition:

        keyboard.add(
            types.KeyboardButton(
                "🐜 Відправити мурах в експедицію"
            )
        )

    # -----------------------------------------------------
    # Експедиція активна
    # -----------------------------------------------------

    else:

        status = active_expedition.get(
            "status",
            "active"
        )

        if status == "paused":

            keyboard.add(
                types.KeyboardButton(
                    "▶️ Продовжити експедицію"
                )
            )

        else:

            keyboard.add(
                types.KeyboardButton(
                    "🏕️ Зробити привал"
                )
            )

        keyboard.add(
            types.KeyboardButton(
                "🏁 Завершити експедицію"
            )
        )

    # -----------------------------------------------------
    # Назад
    # -----------------------------------------------------

    keyboard.add(
        types.KeyboardButton(
            "🔙 Назад"
        )
    )

    return keyboard


# =========================================================
# ОТРИМАТИ АКТИВНУ ЕКСПЕДИЦІЮ
# =========================================================

def get_active_expedition(player):
    """
    Повертає поточну активну експедицію.

    На цьому етапі в колонці expeditions
    зберігається максимум одна поточна експедиція.
    """

    expeditions = player.get(
        "expeditions"
    ) or []

    if not expeditions:
        return None

    expedition = expeditions[0]

    if not isinstance(
        expedition,
        dict
    ):
        return None

    status = expedition.get(
        "status",
        "active"
    )

    if status in (
        "active",
        "paused"
    ):

        return expedition

    return None


# =========================================================
# МЕНЮ ЕКСПЕДИЦІЙ
# =========================================================

@bot.message_handler(
    func=lambda message:
        message.text == "🧭 Експедиції"
)
def show_expeditions(message):

    user_id = str(
        message.from_user.id
    )

    player = get_player(
        user_id
    )

    active_expedition = get_active_expedition(
        player
    )

    # =====================================================
    # Є АКТИВНА ЕКСПЕДИЦІЯ
    # =====================================================

    if active_expedition:

        status = active_expedition.get(
            "status",
            "active"
        )

        active_seconds = active_expedition.get(
            "active_seconds",
            0
        )

        hours = active_seconds // 3600
        minutes = (
            active_seconds % 3600
        ) // 60

        if hours > 0:

            time_text = (
                f"{hours} год {minutes} хв"
            )

        else:

            time_text = (
                f"{minutes} хв"
            )

        if status == "paused":

            text = (
                "🐜 <b>Генерал Мураха доповідає!</b>\n\n"

                "Експедиція тимчасово зупинена. "
                "Загін розклав карти, перевіряє запаси "
                "та чекає на подальший наказ.\n\n"

                f"⏱️ Активний час: <b>{time_text}</b>\n\n"

                "Коли будеш готова продовжити подорож, "
                "дай наказ вирушати далі."
            )

        else:

            text = (
                "🐜 <b>Генерал Мураха доповідає!</b>\n\n"

                "Загін зараз у експедиції.\n"
                "Мурахи досліджують Грінвуд, "
                "поки ти займаєшся своїми справами.\n\n"

                f"⏱️ Активний час: <b>{time_text}</b>\n\n"

                "Коли захочеш зробити привал або "
                "повернути загін, скористайся кнопками нижче."
            )

        bot.send_message(
            message.chat.id,
            text,
            parse_mode="HTML",
            reply_markup=expedition_menu_keyboard(
                active_expedition
            )
        )

        return

    # =====================================================
    # НЕМАЄ АКТИВНОЇ ЕКСПЕДИЦІЇ
    # =====================================================

    text = (
        "🐜 <b>Генерал Мураха доповідає!</b>\n\n"

        "🧭 <b>Експедиції</b> — це подорожі "
        "маленького загону мурах просторами Грінвуду.\n\n"

        "Поки ти навчаєшся, працюєш або займаєшся "
        "власними справами, наші розвідники вирушають "
        "досліджувати лісові стежки, тихий ставок "
        "та небесні простори.\n\n"

        "⏱️ Чим довше триває експедиція, "
        "тим більше часу мають мурахи на пошуки "
        "дивовижних речей.\n\n"

        "🎒 Після повернення всі знайдені артефакти "
        "будуть передані до твого рюкзака.\n\n"

        "🐜 <i>Генерал Мураха готовий відправити загін.</i>"
    )

    bot.send_message(
        message.chat.id,
        text,
        parse_mode="HTML",
        reply_markup=expedition_menu_keyboard()
    )
