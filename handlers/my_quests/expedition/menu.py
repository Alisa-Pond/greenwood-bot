from services.config import bot
from services.database import get_player
from keyboards import get_expedition_menu


print("🧭 Реєструємо хендлер експедицій...")


# =========================================================
# ОТРИМАТИ АКТИВНУ ЕКСПЕДИЦІЮ
# =========================================================

def get_active_expedition(player):
    """
    Повертає поточну активну або призупинену експедицію.

    У колонці expeditions зберігається
    максимум одна поточна експедиція.
    """

    expeditions = player.get(
        "expeditions"
    ) or []

    if not isinstance(expeditions, list):
        return None

    if not expeditions:
        return None

    expedition = expeditions[0]

    if not isinstance(expedition, dict):
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
# ФОРМАТУВАННЯ ЧАСУ
# =========================================================

def format_active_time(active_seconds):

    try:
        active_seconds = int(
            active_seconds or 0
        )

    except (
        TypeError,
        ValueError
    ):
        active_seconds = 0

    hours = active_seconds // 3600

    minutes = (
        active_seconds % 3600
    ) // 60

    seconds = (
        active_seconds % 60
    )

    if hours > 0:

        return (
            f"{hours} год "
            f"{minutes} хв"
        )

    if minutes > 0:

        return (
            f"{minutes} хв"
        )

    return (
        f"{seconds} с"
    )


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

    # -----------------------------------------------------
    # ЗАХИСТ
    # -----------------------------------------------------

    if not player:

        bot.send_message(
            message.chat.id,
            (
                "🐜 <b>Генерал Мураха:</b>\n\n"
                "Не можу знайти твій табір. "
                "Спробуй ще раз."
            ),
            parse_mode="HTML"
        )

        return

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

        # -------------------------------------------------
        # ВАЖЛИВО:
        # Імпортуємо timer тут, щоб menu.py
        # не створював зайвих циклічних імпортів.
        # -------------------------------------------------

        from handlers.my_quests.expedition.timer import (
            calculate_active_seconds
        )

        active_seconds = calculate_active_seconds(
            active_expedition
        )

        time_text = format_active_time(
            active_seconds
        )

        # -------------------------------------------------
        # ПРИВАЛ
        # -------------------------------------------------

        if status == "paused":

            text = (
                "🐜 <b>Генерал Мураха доповідає!</b>\n\n"

                "Експедиція тимчасово зупинена.\n\n"

                "Загін на привалі. Наметове містечко "
                "розгорнуто, вогонь підтримується, "
                "а розвідники відновлюють сили.\n\n"

                f"⏱️ <b>Активний час:</b> "
                f"{time_text}\n\n"

                "Коли будеш готова, загін зможе "
                "продовжити експедицію."
            )

        # -------------------------------------------------
        # ЕКСПЕДИЦІЯ ТРИВАЄ
        # -------------------------------------------------

        else:

            text = (
                "🐜 <b>Генерал Мураха доповідає!</b>\n\n"

                "🧭 <b>Експедиція триває.</b>\n\n"

                f"⏱️ <b>Активний час:</b> "
                f"{time_text}\n\n"

                "Загін продовжує дослідження "
                "лісових територій.\n\n"

                "Що довше триває похід, "
                "то більше досвіду та знахідок "
                "можуть принести розвідники."
            )

        bot.send_message(
            message.chat.id,
            text,
            parse_mode="HTML",
            reply_markup=get_expedition_menu(
                active_expedition
            )
        )

        return

    # =====================================================
    # НЕМАЄ АКТИВНОЇ ЕКСПЕДИЦІЇ
    # =====================================================

    from handlers.my_quests.expedition.start import (
        start_expedition
    )

    start_expedition(
        message
    )
