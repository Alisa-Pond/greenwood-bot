from datetime import datetime
from telebot import types

from services.config import bot
from services.database import get_player, update_player

from services.activity_utils import (
    get_title,
    get_xp,
    get_spheres,
    get_today,
    add_level_xp,
    add_xp_to_spheres,
    update_statistics,
    build_back_button,
    build_level_up_messages,
)

from services.activity_loot import try_activity_loot


WEEKDAYS = [
    "пн",
    "вт",
    "ср",
    "чт",
    "пт",
    "сб",
    "нд"
]


# =========================================================
# ПЕРЕВІРКА ДНЯ РИТУАЛУ
# =========================================================

def ritual_is_for_today(ritual):

    if ritual.get("daily") is True:
        return True

    days = ritual.get("days") or []

    if not isinstance(days, list):
        return False

    today = datetime.now().weekday()

    return (
        today in days
        or WEEKDAYS[today] in days
    )


# =========================================================
# ВИБІР РИТУАЛУ
# =========================================================

@bot.message_handler(
    func=lambda message:
        message.text == "🔄 Провести ритуал"
)
def choose_ritual(message):

    user_id = str(
        message.from_user.id
    )

    player = get_player(
        user_id
    )

    rituals = player.get(
        "rituals"
    ) or []

    if not rituals:

        bot.send_message(
            message.chat.id,

            "🔄 <b>Жодного активного ритуалу.</b>\n\n"
            "Ліс сьогодні напрочуд тихий. 🌲",

            parse_mode="HTML",
            reply_markup=build_back_button(),
        )

        return

    # -----------------------------------------------------
    # ШУКАЄМО РИТУАЛИ НА СЬОГОДНІ
    # -----------------------------------------------------

    available = []

    for index, ritual in enumerate(rituals):

        if ritual_is_for_today(
            ritual
        ):

            available.append(
                (index, ritual)
            )

    if not available:

        bot.send_message(
            message.chat.id,

            "💤 <b>Сьогодні жоден ритуал "
            "не чекає на виконання.</b>\n\n"
            "Твої ритуали відпочивають "
            "до свого дня. 🌙",

            parse_mode="HTML",
            reply_markup=build_back_button(),
        )

        return

    # -----------------------------------------------------
    # КНОПКИ
    # -----------------------------------------------------

    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    for index, ritual in available:

        markup.row(
            types.KeyboardButton(
                f"🔄 {index + 1}. "
                f"{get_title(ritual)}"
            )
        )

    markup.row(
        types.KeyboardButton("🔙 Назад")
    )

    msg = bot.send_message(
        message.chat.id,

        "🔄 <b>Сьогоднішні ритуали:</b>\n\n"
        "Обери той, який щойно провела.",

        parse_mode="HTML",
        reply_markup=markup,
    )

    bot.register_next_step_handler(
        msg,
        complete_ritual
    )


# =========================================================
# ВИКОНАННЯ РИТУАЛУ
# =========================================================

def complete_ritual(message):

    if message.text == "🔙 Назад":

        from handlers.complete_activity import start_complete

        start_complete(message)

        return

    user_id = str(
        message.from_user.id
    )

    player = get_player(
        user_id
    )

    rituals = player.get(
        "rituals"
    ) or []

    # -----------------------------------------------------
    # ВИЗНАЧАЄМО НОМЕР
    # -----------------------------------------------------

    try:

        selected_index = (
            int(
                message.text
                .split(".")[0]
                .replace("🔄", "")
                .strip()
            )
            - 1
        )

    except (
        ValueError,
        IndexError
    ):

        selected_index = None

    # -----------------------------------------------------
    # ПЕРЕВІРКА
    # -----------------------------------------------------

    if (
        selected_index is None
        or not 0 <= selected_index < len(rituals)
    ):

        bot.send_message(
            message.chat.id,

            "🔄 Не вдалося знайти цей ритуал."
        )

        choose_ritual(message)

        return

    ritual = rituals[
        selected_index
    ]

    title = get_title(
        ritual
    )

    xp = get_xp(
        ritual
    )

    spheres = get_spheres(
        ritual
    )

    today = get_today()

    # -----------------------------------------------------
    # ПЕРЕВІРКА ДНЯ
    # -----------------------------------------------------

    if not ritual_is_for_today(
        ritual
    ):

        bot.send_message(
            message.chat.id,

            "🌙 <b>Сьогодні цей ритуал "
            "не можна провести.</b>\n\n"
            "Його день ще не настав.",

            parse_mode="HTML",
            reply_markup=build_back_button(),
        )

        return

    # -----------------------------------------------------
    # ПЕРЕВІРКА ПОВТОРНОГО ВИКОНАННЯ
    # -----------------------------------------------------

    if ritual.get(
        "last_completed"
    ) == today:

        bot.send_message(
            message.chat.id,

            "🌙 <b>Цей ритуал уже "
            "виконано сьогодні.</b>",

            parse_mode="HTML",
            reply_markup=build_back_button(),
        )

        return

    # -----------------------------------------------------
    # XP ПЕРСОНАЖА
    # -----------------------------------------------------

    character_level_ups = add_level_xp(
        player,
        xp
    )

    # -----------------------------------------------------
    # XP СФЕР
    # -----------------------------------------------------

    sphere_level_ups = add_xp_to_spheres(
        player,
        spheres,
        xp
    )

    # -----------------------------------------------------
    # ЛУТ
    # -----------------------------------------------------

    loot = try_activity_loot(
        player
    )

    # -----------------------------------------------------
    # АРХІВ РИТУАЛІВ
    # -----------------------------------------------------

    ritual_archive = (
        player.get(
            "ritual_archive"
        ) or []
    )

    completed_ritual = dict(
        ritual
    )

    completed_ritual[
        "completed_date"
    ] = today

    ritual_archive.append(
        completed_ritual
    )

    # -----------------------------------------------------
    # ОНОВЛЮЄМО РИТУАЛ
    # -----------------------------------------------------

    ritual[
        "last_completed"
    ] = today

    rituals[
        selected_index
    ] = ritual

    player[
        "rituals"
    ] = rituals

    player[
        "ritual_archive"
    ] = ritual_archive

    # -----------------------------------------------------
    # СТАТИСТИКА
    # -----------------------------------------------------

    update_statistics(
        player,
        completed_rituals=1
    )

    # -----------------------------------------------------
    # SUPABASE
    # -----------------------------------------------------

    update_player(
        user_id,
        {
            "level": player["level"],
            "level_xp": player["level_xp"],
            "level_max_xp": player["level_max_xp"],

            "spheres": player["spheres"],

            "rituals": player["rituals"],
            "ritual_archive": player[
                "ritual_archive"
            ],

            "statistics": player[
                "statistics"
            ],

            "inventory": player.get(
                "inventory"
            ) or [],
        }
    )

    # -----------------------------------------------------
    # ПОВІДОМЛЕННЯ
    # -----------------------------------------------------

    loot_text = ""

    if loot:

        loot_text = (
            f"\n🎁 Знайдено: "
            f"<b>{loot}</b>"
        )

    spheres_text = " ".join(
        spheres
    )

    bot.send_message(
        message.chat.id,

        "🔥 <b>Ритуал проведено!</b>\n\n"

        f"🔄 <b>{title}</b>\n"
        f"⭐ Отримано: <b>{xp:.1f} XP</b>\n"
        f"🎯 Сфери: {spheres_text}"

        f"{loot_text}\n\n"

        "🕯️ Запис збережено в "
        "<b>Архіві ритуалів</b>.",

        parse_mode="HTML",

        reply_markup=build_back_button(),
    )

    # -----------------------------------------------------
    # ПОВІДОМЛЕННЯ ПРО ПІДВИЩЕННЯ РІВНЯ
    # -----------------------------------------------------

    level_up_messages = build_level_up_messages(
        character_level_ups,
        sphere_level_ups
    )

    for level_up_message in level_up_messages:

        bot.send_message(
            message.chat.id,
            level_up_message,
            parse_mode="HTML"
        )
