from datetime import datetime
from telebot import types

from services.config import bot
from services.database import get_player, update_player

from services.activity_utils import (
    get_title,
    get_xp,
    get_spheres,
    get_today,
    add_xp_to_character,
    update_statistics,
    build_back_button,
    send_level_up_notifications,
)

from services.activity_loot import try_activity_loot


# =========================================================
# ДНІ ТИЖНЯ
# =========================================================

WEEKDAYS = [
    "пн",
    "вт",
    "ср",
    "чт",
    "пт",
    "сб",
    "нд",
]


# =========================================================
# ПЕРЕВІРКА ДНЯ РИТУАЛУ
# =========================================================

def ritual_is_for_today(ritual):

    # Якщо ритуал щоденний
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
# ФОРМАТ РИТУАЛУ ДЛЯ ВІДОБРАЖЕННЯ
# =========================================================
#
# Формат:
#
# [Сфери] ; [Бали] ; [Дні] ; [Назва справи]
#
# Наприклад:
#
# 💪🧠 ; 10 ; пн ср пт ; Вивчити нову тему
#
# =========================================================

def format_ritual(ritual):

    spheres = get_spheres(ritual)

    spheres_text = "".join(
        spheres
    )

    xp = get_xp(ritual)

    days = ritual.get("days") or []

    # -----------------------------------------------------
    # ДНІ
    # -----------------------------------------------------

    if ritual.get("daily") is True:

        days_text = "щодня"

    elif isinstance(days, list):

        formatted_days = []

        for day in days:

            if isinstance(day, int):

                if 0 <= day < len(WEEKDAYS):

                    formatted_days.append(
                        WEEKDAYS[day]
                    )

            else:

                formatted_days.append(
                    str(day)
                )

        days_text = " ".join(
            formatted_days
        )

        if not days_text:
            days_text = "—"

    else:

        days_text = "—"

    title = get_title(
        ritual
    )

    return (
        f"{spheres_text} ; "
        f"{xp:g} ; "
        f"{days_text} ; "
        f"{title}"
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

    # =====================================================
    # РИТУАЛИ, ЯКІ МОЖНА ВИКОНАТИ СЬОГОДНІ
    # =====================================================

    available = []

    for index, ritual in enumerate(
        rituals
    ):

        if ritual_is_for_today(
            ritual
        ):

            available.append(
                (
                    index,
                    ritual
                )
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

    # =====================================================
    # ПОКАЗУЄМО РИТУАЛИ ЗВИЧАЙНИМ ТЕКСТОМ
    # =====================================================

    text = (
        "🔄 <b>Сьогоднішні ритуали:</b>\n\n"
    )

    for index, ritual in available:

        text += (
            f"<b>{index + 1}.</b> "
            f"{format_ritual(ritual)}\n"
        )

    text += (
        "\n✏️ Напиши номер ритуалу, "
        "який ти виконала."
    )

    # =====================================================
    # КЛАВІАТУРА
    # =====================================================

    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    markup.row(
        types.KeyboardButton(
            "🔙 Назад"
        )
    )

    msg = bot.send_message(
        message.chat.id,

        text,

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

    # =====================================================
    # НАЗАД
    # =====================================================

    if message.text == "🔙 Назад":

        from handlers.complete_activity import start_complete

        start_complete(
            message
        )

        return

    # =====================================================
    # ОТРИМУЄМО ГРАВЦЯ
    # =====================================================

    user_id = str(
        message.from_user.id
    )

    player = get_player(
        user_id
    )

    rituals = player.get(
        "rituals"
    ) or []

    # =====================================================
    # ВИБІР НОМЕРА
    # =====================================================

    try:

        selected_index = (
            int(
                message.text.strip()
            )
            - 1
        )

    except (
        ValueError,
        TypeError
    ):

        selected_index = None

    # =====================================================
    # ПЕРЕВІРКА НОМЕРА
    # =====================================================

    if (
        selected_index is None
        or not 0 <= selected_index < len(
            rituals
        )
    ):

        bot.send_message(
            message.chat.id,

            "🔄 <b>Не вдалося знайти "
            "цей ритуал.</b>\n\n"
            "Напиши номер ритуалу ще раз.",

            parse_mode="HTML",
        )

        choose_ritual(
            message
        )

        return

    # =====================================================
    # ОТРИМУЄМО РИТУАЛ
    # =====================================================

    ritual = rituals[
        selected_index
    ]

    # =====================================================
    # ПЕРЕВІРКА, ЧИ РИТУАЛ МОЖНА ВИКОНУВАТИ СЬОГОДНІ
    # =====================================================

    if not ritual_is_for_today(
        ritual
    ):

        bot.send_message(
            message.chat.id,

            "🌙 <b>Цей ритуал сьогодні "
            "не запланований.</b>\n\n"
            "Його день ще не настав.",

            parse_mode="HTML",

            reply_markup=build_back_button(),
        )

        return

    # =====================================================
    # ДАНІ РИТУАЛУ
    # =====================================================

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

    # =====================================================
    # ПЕРЕВІРКА ПОВТОРНОГО ВИКОНАННЯ
    # =====================================================

    if ritual.get(
        "last_completed"
    ) == today:

        bot.send_message(
            message.chat.id,

            "🌙 <b>Цей ритуал уже "
            "виконано сьогодні.</b>\n\n"
            "Завтра він знову чекатиме на тебе.",

            parse_mode="HTML",

            reply_markup=build_back_button(),
        )

        return

    # =====================================================
    # XP ГЕРОЯ + XP СФЕР
    # =====================================================
    #
    # ОДНА функція робить усе:
    #
    # 🧙‍♂️ XP героя
    # 🎯 XP сфер
    # ✨ level up героя
    # ✨ level up сфер
    #
    # =====================================================

    level_up_data = add_xp_to_character(
        player,
        spheres,
        xp
    )

    # =====================================================
    # ЛУТ
    # =====================================================

    loot = try_activity_loot(
        player
    )

    # =====================================================
    # АРХІВ РИТУАЛІВ
    # =====================================================

    ritual_archive = (
        player.get(
            "ritual_archive"
        )
        or []
    )

    completed_ritual = dict(
        ritual
    )

    completed_ritual[
        "completed_date"
    ] = today

    completed_ritual[
        "earned_xp"
    ] = xp

    ritual_archive.append(
        completed_ritual
    )

    # =====================================================
    # ОНОВЛЮЄМО РИТУАЛ
    # =====================================================

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

    # =====================================================
    # СТАТИСТИКА
    # =====================================================

    update_statistics(
        player,
        completed_rituals=1
    )

    # =====================================================
    # SUPABASE
    # =====================================================

    update_player(
        user_id,
        {
            "level": player.get(
                "level",
                1
            ),

            "level_xp": player.get(
                "level_xp",
                0.0
            ),

            "level_max_xp": player.get(
                "level_max_xp",
                10.0
            ),

            "spheres": player.get(
                "spheres"
            ) or {},

            "rituals": player.get(
                "rituals"
            ) or [],

            "ritual_archive": player.get(
                "ritual_archive"
            ) or [],

            "statistics": player.get(
                "statistics"
            ) or {},

            "inventory": player.get(
                "inventory"
            ) or [],
        }
    )

    # =====================================================
    # ПОВІДОМЛЕННЯ ПРО LEVEL UP
    # =====================================================

    send_level_up_notifications(
        message.chat.id,
        level_up_data
    )

    # =====================================================
    # ТЕКСТ ЛУТУ
    # =====================================================

    loot_text = ""

    if loot:

        loot_text = (
            f"\n🎁 Знайдено: "
            f"<b>{loot}</b>"
        )

    # =====================================================
    # ТЕКСТ СФЕР
    # =====================================================

    spheres_text = " ".join(
        spheres
    )

    # =====================================================
    # ФІНАЛЬНЕ ПОВІДОМЛЕННЯ
    # =====================================================

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
