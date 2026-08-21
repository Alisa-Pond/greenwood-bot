from services.config import bot
from services.database import get_player
from keyboards import get_expedition_menu


print("🧭 Реєструємо хендлер експедицій...")


# =========================================================
# ОТРИМАТИ АКТИВНУ ЕКСПЕДИЦІЮ
# =========================================================

def get_active_expedition(player):
    """
    Повертає поточну активну експедицію.

    У колонці expeditions зберігається
    максимум одна поточна експедиція.
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

    if hours > 0:

        return (
            f"{hours} год {minutes} хв"
        )

    return f"{minutes} хв"


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

        time_text = format_active_time(
            active_seconds
        )

        # -------------------------------------------------
        # ПРИВАЛ
        # -------------------------------------------------

        if status == "paused":

            text = (
                "🐜 <b>Генерал Мураха доповідає!</b>\n\n"

                "Експедиція тимчасово зупинена.\n"
                "Загін на привалі. Наметове містечко розгорнуто, "
                "вогонь підтримується, юшка в казані кипить. "
                "Розвідники відновлюють сили.\n\n"

                f"⏱️ Активний час: "
                f"<b>{time_text}</b>\n\n"

                "За наказом вирушимо далі."
            )

        # -------------------------------------------------
        # ЕКСПЕДИЦІЯ ТРИВАЄ
        # -------------------------------------------------

        else:

            text = (
                "🐜 <b>Генерал Мураха доповідає! 🐜</b>\n\n"

                "Експедиція триває.\n\n"

                f"⏱️ Активний час: "
                f"<b>{time_text}</b>\n\n"

                "Загін продовжує пошуки. "
                "Очікуємо подальший наказ"
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

    text = (
        "🐜 <b>Генерал Мураха доповідає! 🐜</b>\n\n"

        "🧭 <b>Експедиція</b> — це вихід розвідувального "
        "загону в дикі землі Грінвуду.\n\n"

        "Ліс не лежить без діла. Стежки змінюються, "
        "у старих дуплах з'являються нові таємниці, "
        "а під корінням іноді знаходиться те, "
        "чого там учора ще не було.\n\n"

        "🐜 Загін вирушає в дорогу й досліджує ліс, "
        "поки триває похід. Чим довше мурахи залишаються "
        "в експедиції, тим більше території вони встигають обстежити.\n\n"

        "🎒 Повернувшись, розвідники принесуть усе, "
        "що вдалося знайти серед лісових хащів.\n\n"

        "<i>Загін споряджений. Чекаємо наказу на висування.</i>"
    )

    bot.send_message(
        message.chat.id,
        text,
        parse_mode="HTML",
        reply_markup=get_expedition_menu()
    )

    # =====================================================
    # ОДРАЗУ ПЕРЕХОДИМО ДО ВИБОРУ СФЕР
    # =====================================================

    from handlers.my_quests.expedition.start import (
        start_expedition
    )

    start_expedition(
        message
    )
