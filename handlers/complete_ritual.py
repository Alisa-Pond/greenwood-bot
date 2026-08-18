from datetime import datetime

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
    "нд"
]


# =========================================================
# ПЕРЕВІРКА ДНЯ РИТУАЛУ
# =========================================================

def ritual_is_for_today(ritual):

    # -----------------------------------------------------
    # ЩОДЕННИЙ РИТУАЛ
    # -----------------------------------------------------

    if ritual.get("daily") is True:
        return True

    days = ritual.get(
        "days"
    ) or []

    if not isinstance(
        days,
        list
    ):
        return False

    today = datetime.now().weekday()

    return (
        today in days
        or WEEKDAYS[today] in days
    )


# =========================================================
# ФОРМАТУВАННЯ ДНІВ
# =========================================================

def format_ritual_days(ritual):

    # -----------------------------------------------------
    # ЩОДЕННИЙ
    # -----------------------------------------------------

    if ritual.get("daily") is True:

        return "щодня"

    days = ritual.get(
        "days"
    ) or []

    if not isinstance(
        days,
        list
    ):
        return "без днів"

    result = []

    for day in days:

        # -----------------------------------------------
        # Якщо день збережений як число
        # -----------------------------------------------

        if isinstance(
            day,
            int
        ):

            if 0 <= day < len(WEEKDAYS):

                result.append(
                    WEEKDAYS[day]
                )

            continue

        # -----------------------------------------------
        # Якщо день збережений як текст
        # -----------------------------------------------

        day_text = str(
            day
        ).strip().lower()

        # Повні назви днів, якщо раптом вони є
        full_days = {
            "понеділок": "пн",
            "вівторок": "вт",
            "середа": "ср",
            "четвер": "чт",
            "п'ятниця": "пт",
            "п’ятниця": "пт",
            "субота": "сб",
            "неділя": "нд",
        }

        day_text = full_days.get(
            day_text,
            day_text
        )

        if day_text in WEEKDAYS:

            result.append(
                day_text
            )

    if not result:

        return "без днів"

    # -----------------------------------------------------
    # Прибираємо дублікати
    # -----------------------------------------------------

    result = list(
        dict.fromkeys(
            result
        )
    )

    return ", ".join(
        result
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

    # =====================================================
    # НЕМАЄ РИТУАЛІВ
    # =====================================================

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
    # РИТУАЛИ НА СЬОГОДНІ
    # =====================================================

    available = []

    for index, ritual in enumerate(
        rituals
    ):

        if ritual_is_for_today(
            ritual
        ):

            # ---------------------------------------------
            # Якщо вже виконано сьогодні,
            # не показуємо його серед доступних
            # ---------------------------------------------

            if ritual.get(
                "last_completed"
            ) == get_today():

                continue

            available.append(
                (
                    index,
                    ritual
                )
            )

    # =====================================================
    # НЕМАЄ ДОСТУПНИХ
    # =====================================================

    if not available:

        bot.send_message(
            message.chat.id,

            "💤 <b>Сьогодні жоден ритуал "
            "не чекає на виконання.</b>\n\n"

            "Можливо, всі сьогоднішні ритуали "
            "вже проведені або їхній день "
            "ще не настав. 🌙",

            parse_mode="HTML",

            reply_markup=build_back_button(),
        )

        return

    # =====================================================
    # СПИСОК РИТУАЛІВ
    # =====================================================

    ritual_text = (
        "🔄 <b>Сьогоднішні ритуали:</b>\n\n"
    )

    for index, ritual in available:

        spheres = get_spheres(
            ritual
        )

        spheres_text = "".join(
            spheres
        )

        xp = get_xp(
            ritual
        )

        days_text = format_ritual_days(
            ritual
        )

        title = get_title(
            ritual
        )

        # -------------------------------------------------
        # ФОРМАТ
        # -------------------------------------------------

        ritual_text += (
            f"{index + 1}. "
            f"{spheres_text} ; "
            f"{xp:g} ; "
            f"{days_text} ; "
            f"{title}\n"
        )

    # =====================================================
    # ІНСТРУКЦІЯ
    # =====================================================

    ritual_text += (
        "\n"
        "✍️ <b>Напиши номер ритуалу, який проведено.</b>\n"
        "Можна провести одразу кілька:\n\n"

        "<code>1</code>\n"
        "або\n"
        "<code>1 2 4</code>"
    )

    msg = bot.send_message(
        message.chat.id,

        ritual_text,

        parse_mode="HTML",

        reply_markup=build_back_button(),
    )

    bot.register_next_step_handler(
        msg,
        complete_ritual
    )


# =========================================================
# ВИКОНАННЯ РИТУАЛІВ
# =========================================================

def complete_ritual(message):

    if message.text == "🔙 Назад":

        from handlers.complete_activity import start_complete

        start_complete(
            message
        )

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

    if not rituals:

        bot.send_message(
            message.chat.id,

            "🔄 Активних ритуалів більше немає.",

            reply_markup=build_back_button(),
        )

        return

    # =====================================================
    # ОТРИМУЄМО НОМЕРИ
    # =====================================================

    try:

        numbers = message.text.split()

        if not numbers:

            raise ValueError

        selected_indexes = []

        for number in numbers:

            if not number.isdigit():

                raise ValueError

            index = int(
                number
            ) - 1

            if not 0 <= index < len(
                rituals
            ):

                raise ValueError

            selected_indexes.append(
                index
            )

        # -------------------------------------------------
        # ЗАХИСТ ВІД ПОВТОРІВ
        # -------------------------------------------------

        if len(
            selected_indexes
        ) != len(
            set(selected_indexes)
        ):

            raise ValueError

    except (
        ValueError,
        AttributeError
    ):

        bot.send_message(
            message.chat.id,

            "🦇 <b>Марчелло не зрозумів "
            "твоїх записів.</b>\n\n"

            "Введи номер ритуалу:\n"
            "<code>1</code>\n\n"

            "або кілька номерів:\n"
            "<code>1 2 4</code>",

            parse_mode="HTML",

            reply_markup=build_back_button(),
        )

        bot.register_next_step_handler(
            message,
            complete_ritual
        )

        return

    # =====================================================
    # СЬОГОДНІ
    # =====================================================

    today = get_today()

    # =====================================================
    # НАКОПИЧУЄМО РЕЗУЛЬТАТИ
    # =====================================================

    total_xp = 0.0

    completed_titles = []

    completed_count = 0

    all_level_up_data = []

    all_loot = []

    ritual_archive = (
        player.get(
            "ritual_archive"
        )
        or []
    )

    # =====================================================
    # ОБРОБКА
    #
    # Тут НЕ видаляємо ритуали.
    # Ритуал є повторюваним.
    #
    # Просто оновлюємо last_completed.
    # =====================================================

    for selected_index in selected_indexes:

        ritual = rituals[
            selected_index
        ]

        # -------------------------------------------------
        # ПЕРЕВІРКА ДНЯ
        # -------------------------------------------------

        if not ritual_is_for_today(
            ritual
        ):

            continue

        # -------------------------------------------------
        # ПЕРЕВІРКА ПОВТОРНОГО ВИКОНАННЯ
        # -------------------------------------------------

        if ritual.get(
            "last_completed"
        ) == today:

            continue

        title = get_title(
            ritual
        )

        xp = get_xp(
            ritual
        )

        spheres = get_spheres(
            ritual
        )

        # -------------------------------------------------
        # XP ПЕРСОНАЖА
        # -------------------------------------------------

        level_up_data = add_xp_to_character(
            player,
            spheres,
            xp
        )

        # -------------------------------------------------
        # LEVEL UP
        # -------------------------------------------------

        if level_up_data:

            if isinstance(
                level_up_data,
                list
            ):

                all_level_up_data.extend(
                    level_up_data
                )

            else:

                all_level_up_data.append(
                    level_up_data
                )

        # -------------------------------------------------
        # ЛУТ
        # -------------------------------------------------

        loot = try_activity_loot(
            player
        )

        if loot:

            all_loot.append(
                loot
            )

        # -------------------------------------------------
        # АРХІВ
        # -------------------------------------------------

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

        # -------------------------------------------------
        # ОНОВЛЮЄМО РИТУАЛ
        # -------------------------------------------------

        ritual[
            "last_completed"
        ] = today

        rituals[
            selected_index
        ] = ritual

        # -------------------------------------------------
        # РЕЗУЛЬТАТИ
        # -------------------------------------------------

        total_xp += xp

        completed_titles.append(
            title
        )

        completed_count += 1

    # =====================================================
    # ЯКЩО ЖОДЕН РИТУАЛ НЕ БУВ ВИКОНАНИЙ
    # =====================================================

    if completed_count == 0:

        bot.send_message(
            message.chat.id,

            "🌙 <b>Жоден із вибраних ритуалів "
            "не вдалося провести.</b>\n\n"

            "Перевір, чи належать вони "
            "до сьогоднішнього дня і чи "
            "не були вже виконані.",

            parse_mode="HTML",

            reply_markup=build_back_button(),
        )

        return

    # =====================================================
    # ОНОВЛЮЄМО PLAYER
    # =====================================================

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
        completed_rituals=completed_count
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
    # LEVEL UP
    # =====================================================

    for level_up_data in all_level_up_data:

        send_level_up_notifications(
            message.chat.id,
            level_up_data
        )

    # =====================================================
    # СПИСОК ВИКОНАНИХ РИТУАЛІВ
    # =====================================================

    titles_text = "\n".join(
        f"🔄 {title}"
        for title in completed_titles
    )

    # =====================================================
    # ЛУТ
    # =====================================================

    loot_text = ""

    if all_loot:

        loot_text = (
            "\n🎁 <b>Знайдено:</b>\n"

            + "\n".join(
                f"• {loot}"
                for loot in all_loot
            )
        )

    # =====================================================
    # РЕЗУЛЬТАТ
    # =====================================================

    bot.send_message(
        message.chat.id,

        "🔥 <b>Ритуал проведено!</b>\n\n"

        f"✨ Виконано ритуалів: "
        f"<b>{completed_count}</b>\n\n"

        f"{titles_text}\n\n"

        f"⭐ Загалом отримано: "
        f"<b>{total_xp:.1f} XP</b>"

        f"{loot_text}\n\n"

        "🕯️ Записи збережено в "
        "<b>Архіві ритуалів</b>.",

        parse_mode="HTML",

        reply_markup=build_back_button(),
    )
