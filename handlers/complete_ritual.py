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
    # ПОКАЗУЄМО РИТУАЛИ
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
        "\n✏️ Напиши номер ритуалу "
        "або декілька номерів через кому.\n\n"
        "Наприклад: <b>1, 2</b>"
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
# ПАРСИНГ НОМЕРІВ РИТУАЛІВ
# =========================================================

def parse_ritual_numbers(text):

    if not text:
        return None

    parts = text.split(",")

    numbers = []

    for part in parts:

        part = part.strip()

        if not part:
            return None

        try:

            number = int(part)

        except (
            ValueError,
            TypeError
        ):

            return None

        if number <= 0:
            return None

        numbers.append(
            number
        )

    # Прибираємо дублікати,
    # але зберігаємо порядок вибору
    unique_numbers = []

    for number in numbers:

        if number not in unique_numbers:

            unique_numbers.append(
                number
            )

    return unique_numbers


# =========================================================
# ВИКОНАННЯ РИТУАЛУ / РИТУАЛІВ
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
    # ОТРИМУЄМО НОМЕРИ РИТУАЛІВ
    # =====================================================

    selected_numbers = parse_ritual_numbers(
        message.text.strip()
    )

    # =====================================================
    # ПЕРЕВІРКА НОМЕРІВ
    # =====================================================

    if not selected_numbers:

        bot.send_message(
            message.chat.id,

            "🔄 <b>Не вдалося розпізнати номери.</b>\n\n"
            "Напиши один номер або декілька через кому.\n"
            "Наприклад: <b>1, 2</b>",

            parse_mode="HTML",
        )

        choose_ritual(
            message
        )

        return

    # Перетворюємо номери користувача
    # на індекси списку rituals
    selected_indices = [
        number - 1
        for number in selected_numbers
    ]

    # Перевіряємо, чи всі номери існують
    invalid_indices = [
        index
        for index in selected_indices
        if not 0 <= index < len(rituals)
    ]

    if invalid_indices:

        bot.send_message(
            message.chat.id,

            "🔄 <b>Не вдалося знайти один "
            "або декілька ритуалів.</b>\n\n"
            "Перевір номери та спробуй ще раз.",

            parse_mode="HTML",
        )

        choose_ritual(
            message
        )

        return

    # =====================================================
    # ДАНІ
    # =====================================================

    today = get_today()

    ritual_archive = (
        player.get(
            "ritual_archive"
        )
        or []
    )

    completed_rituals = []

    total_xp = 0.0

    total_completed = 0

    level_up_data_list = []

    loot_items = []

    # =====================================================
    # ОБРОБКА КОЖНОГО ВИБРАНОГО РИТУАЛУ
    # =====================================================

    for selected_index in selected_indices:

        ritual = rituals[
            selected_index
        ]

        # -------------------------------------------------
        # ПЕРЕВІРКА ДНЯ
        # -------------------------------------------------

        if not ritual_is_for_today(
            ritual
        ):

            bot.send_message(
                message.chat.id,

                f"🌙 <b>Ритуал №{selected_index + 1}</b>\n\n"
                "Цей ритуал сьогодні не запланований.\n"
                "Його день ще не настав.",

                parse_mode="HTML",
            )

            continue

        # -------------------------------------------------
        # ПЕРЕВІРКА ПОВТОРНОГО ВИКОНАННЯ
        # -------------------------------------------------

        if ritual.get(
            "last_completed"
        ) == today:

            bot.send_message(
                message.chat.id,

                f"🌙 <b>Ритуал №{selected_index + 1}</b>\n\n"
                "Цей ритуал уже виконано сьогодні.",

                parse_mode="HTML",
            )

            continue

        # -------------------------------------------------
        # ДАНІ РИТУАЛУ
        # -------------------------------------------------

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
        # XP ГЕРОЯ + XP СФЕР
        # -------------------------------------------------
        #
        # add_xp_to_character()
        # використовує актуальну систему рівнів.
        #
        # Вона відповідає за:
        #
        # 🧙‍♂️ XP героя
        # 🎯 XP сфер
        # ✨ level up героя
        # ✨ level up сфер
        #
        # -------------------------------------------------

        level_up_data = add_xp_to_character(
            player,
            spheres,
            xp
        )

        level_up_data_list.append(
            level_up_data
        )

        # -------------------------------------------------
        # ЛУТ
        # -------------------------------------------------

        loot = try_activity_loot(
            player
        )

        if loot:

            loot_items.append(
                loot
            )

        # -------------------------------------------------
        # АРХІВ РИТУАЛІВ
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
        # ЗБИРАЄМО РЕЗУЛЬТАТ
        # -------------------------------------------------

        completed_rituals.append(
            {
                "title": title,
                "xp": xp,
                "spheres": spheres,
            }
        )

        total_xp += xp

        total_completed += 1

    # =====================================================
    # ЯКЩО ЖОДЕН РИТУАЛ НЕ БУВ ВИКОНАНИЙ
    # =====================================================

    if total_completed == 0:

        bot.send_message(
            message.chat.id,

            "🔄 <b>Жоден із вибраних ритуалів "
            "не вдалося провести.</b>\n\n"
            "Перевір, чи вони доступні сьогодні "
            "та чи не були вже виконані.",

            parse_mode="HTML",
        )

        choose_ritual(
            message
        )

        return

    # =====================================================
    # ЗБЕРІГАЄМО ЗМІНИ
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
        completed_rituals=total_completed
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

    for level_up_data in level_up_data_list:

        send_level_up_notifications(
            message.chat.id,
            level_up_data
        )

    # =====================================================
    # ТЕКСТ УСПІШНОГО ВИКОНАННЯ
    # =====================================================

    result_text = (
        "🔥 <b>Ритуал"
        + ("и проведено!" if total_completed > 1 else " проведено!")
        + "</b>\n\n"
    )

    for completed in completed_rituals:

        spheres_text = " ".join(
            completed["spheres"]
        )

        result_text += (
            f"🔄 <b>{completed['title']}</b>\n"
            f"⭐ Отримано: <b>{completed['xp']:.1f} XP</b>\n"
            f"🎯 Сфери: {spheres_text}\n\n"
        )

    # =====================================================
    # ЛУТ
    # =====================================================

    if loot_items:

        result_text += "🎁 <b>Знайдено:</b>\n"

        for loot in loot_items:

            result_text += (
                f"• <b>{loot}</b>\n"
            )

        result_text += "\n"

    # =====================================================
    # АРХІВ
    # =====================================================

    result_text += (
        "🕯️ Запис"
        + ("и збережено" if total_completed > 1 else " збережено")
        + " в <b>Архіві ритуалів</b>."
    )

    # =====================================================
    # ФІНАЛЬНЕ ПОВІДОМЛЕННЯ
    # =====================================================

    bot.send_message(
        message.chat.id,

        result_text,

        parse_mode="HTML",
    )

    # =====================================================
    # ПОВЕРТАЄМОСЯ В МЕНЮ «ВИКОНАТИ СПРАВУ»
    # =====================================================

    from handlers.complete_activity import start_complete

    start_complete(
        message
    )
