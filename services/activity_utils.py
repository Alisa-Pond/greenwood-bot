from datetime import datetime


# =========================================================
# СФЕРИ
# =========================================================

SPHERE_NAMES = {
    "health": "💪",
    "wisdom": "🧠",
    "art": "🎨",
    "finance": "💵",
    "relations": "🤝",
}


SPHERE_DISPLAY_NAMES = {
    "health": "Здоров'я",
    "wisdom": "Мудрість",
    "art": "Творчість",
    "finance": "Фінанси",
    "relations": "Зв'язки",
}


# =========================================================
# СФЕРА → EMOJI
# =========================================================

def get_sphere_emoji(sphere):

    if sphere in SPHERE_NAMES:
        return SPHERE_NAMES[sphere]

    if sphere in SPHERE_NAMES.values():
        return sphere

    return sphere


# =========================================================
# НАЗВА СФЕРИ
# =========================================================

def get_sphere_name(sphere):

    if sphere in SPHERE_DISPLAY_NAMES:
        return SPHERE_DISPLAY_NAMES[sphere]

    for key, emoji in SPHERE_NAMES.items():

        if sphere == emoji:
            return SPHERE_DISPLAY_NAMES[key]

    return str(sphere)


# =========================================================
# ОТРИМАТИ СФЕРИ З АКТИВНОСТІ
# =========================================================

def get_spheres(item):

    spheres = (
        item.get("spheres")
        or item.get("sphere")
    )

    if not spheres:
        return []

    # -----------------------------------------------------
    # Одна сфера як рядок
    # -----------------------------------------------------

    if isinstance(spheres, str):

        result = []

        for sphere_key, emoji in SPHERE_NAMES.items():

            if (
                sphere_key == spheres
                or emoji in spheres
            ):

                result.append(emoji)

        return result or [spheres]

    # -----------------------------------------------------
    # Декілька сфер
    # -----------------------------------------------------

    if isinstance(spheres, list):

        result = []

        for sphere in spheres:

            if isinstance(sphere, dict):

                emoji = sphere.get("emoji")

                if emoji:

                    result.append(emoji)

                elif sphere.get("name"):

                    result.append(
                        sphere["name"]
                    )

            else:

                result.append(
                    get_sphere_emoji(sphere)
                )

        return list(
            dict.fromkeys(result)
        )

    return []


# =========================================================
# НАЗВА АКТИВНОСТІ
# =========================================================

def get_title(item):

    return (
        item.get("title")
        or item.get("name")
        or item.get("task")
        or "Без назви"
    )


# =========================================================
# XP АКТИВНОСТІ
# =========================================================

def get_xp(item):

    try:

        return float(
            item.get("xp")
            or item.get("points")
            or item.get("reward_xp")
            or 0
        )

    except (
        TypeError,
        ValueError
    ):

        return 0.0


# =========================================================
# СЬОГОДНІШНЯ ДАТА
# =========================================================

def get_today():

    return datetime.now().strftime(
        "%d.%m.%Y"
    )


# =========================================================
# ПАРСИНГ ДЕДЛАЙНУ
# =========================================================

def parse_deadline(deadline):

    if not deadline:
        return None

    value = str(
        deadline
    ).strip()

    for fmt in (
        "%d.%m.%y",
        "%d.%m.%Y"
    ):

        try:

            return datetime.strptime(
                value,
                fmt
            )

        except ValueError:

            continue

    return None


# =========================================================
# ПЕРЕВІРКА ПРОСТРОЧЕННЯ
# =========================================================

def is_overdue(item):

    deadline = parse_deadline(
        item.get("deadline")
    )

    if not deadline:
        return False

    today = datetime.now().replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0
    )

    return today > deadline


# =========================================================
# ШТРАФ ЗА ПРОСТРОЧЕННЯ
# =========================================================

def get_penalty_xp(item):

    for field in (
        "penalty",
        "penalty_xp",
        "overdue_penalty"
    ):

        value = item.get(
            field
        )

        if value is not None:

            try:

                return abs(
                    float(value)
                )

            except (
                TypeError,
                ValueError
            ):

                pass

    return 0.0


# =========================================================
# ВИЗНАЧИТИ КЛЮЧ СФЕРИ
# =========================================================

def _get_sphere_key(sphere):

    if sphere in SPHERE_NAMES:
        return sphere

    for key, emoji in SPHERE_NAMES.items():

        if sphere == emoji:
            return key

    return None


# =========================================================
# ДОДАТИ XP ДО СФЕР
# =========================================================
#
# Приклад:
#
# Активність:
# 🧠🎨
# 9 XP
#
# Отримаємо:
#
# 🧠 +4.5 XP
# 🎨 +4.5 XP
#
# Якщо:
#
# 🧠
# 9 XP
#
# Отримаємо:
#
# 🧠 +9 XP
#
# Функція повертає список level up.
#
# =========================================================

def add_xp_to_spheres(
    player,
    spheres,
    total_xp
):

    level_ups = []

    if not spheres:
        return level_ups

    try:

        total_xp = float(
            total_xp
        )

    except (
        TypeError,
        ValueError
    ):

        return level_ups

    if total_xp <= 0:
        return level_ups

    player_spheres = (
        player.get("spheres")
        or {}
    )

    share = (
        total_xp
        / len(spheres)
    )

    for sphere in spheres:

        sphere_key = _get_sphere_key(
            sphere
        )

        if not sphere_key:
            continue

        if sphere_key not in player_spheres:
            continue

        data = player_spheres[
            sphere_key
        ]

        old_level = int(
            data.get(
                "lvl",
                1
            )
        )

        data["xp"] = (
            float(
                data.get(
                    "xp",
                    0
                )
            )
            + share
        )

        # -------------------------------------------------
        # LEVEL UP
        # -------------------------------------------------

        while (
            data["xp"]
            >= float(
                data.get(
                    "max_xp",
                    10
                )
            )
        ):

            max_xp = float(
                data.get(
                    "max_xp",
                    10
                )
            )

            data["xp"] -= max_xp

            data["lvl"] = (
                int(
                    data.get(
                        "lvl",
                        1
                    )
                )
                + 1
            )

            # Наступний рівень потребує
            # у 1.5 раза більше XP.

            data["max_xp"] = (
                max_xp * 1.5
            )

        new_level = int(
            data.get(
                "lvl",
                1
            )
        )

        if new_level > old_level:

            level_ups.append({

                "key": sphere_key,

                "emoji": SPHERE_NAMES[
                    sphere_key
                ],

                "name": SPHERE_DISPLAY_NAMES[
                    sphere_key
                ],

                "old_level": old_level,

                "new_level": new_level,

            })

    player["spheres"] = (
        player_spheres
    )

    return level_ups


# =========================================================
# ДОДАТИ XP ДО РІВНЯ ПЕРСОНАЖА
# =========================================================
#
# Використовуються поля:
#
# level
# level_xp
# level_max_xp
#
# Приклад:
#
# Рівень 1
# 8 / 10 XP
#
# +5 XP
#
# стає:
#
# Рівень 2
# 3 / 15 XP
#
# =========================================================

def add_xp_to_player(
    player,
    xp
):

    level_ups = []

    try:

        xp = float(xp)

    except (
        TypeError,
        ValueError
    ):

        return level_ups

    if xp <= 0:
        return level_ups

    # -----------------------------------------------------
    # ЗАХИСТ ВІД ВІДСУТНІХ ПОЛІВ
    # -----------------------------------------------------

    if player.get("level") is None:

        player["level"] = 1

    if player.get("level_xp") is None:

        player["level_xp"] = 0.0

    if player.get("level_max_xp") is None:

        player["level_max_xp"] = 10.0

    # -----------------------------------------------------
    # ДОДАЄМО XP
    # -----------------------------------------------------

    player["level_xp"] = (
        float(
            player.get(
                "level_xp",
                0
            )
        )
        + xp
    )

    # -----------------------------------------------------
    # LEVEL UP
    # -----------------------------------------------------

    while (
        player["level_xp"]
        >= float(
            player.get(
                "level_max_xp",
                10
            )
        )
    ):

        old_level = int(
            player.get(
                "level",
                1
            )
        )

        max_xp = float(
            player.get(
                "level_max_xp",
                10
            )
        )

        player["level_xp"] -= max_xp

        player["level"] = (
            old_level + 1
        )

        # Наступний рівень =
        # попередня вимога × 1.5

        player["level_max_xp"] = (
            max_xp * 1.5
        )

        level_ups.append({

            "old_level": old_level,

            "new_level": player[
                "level"
            ]

        })

    return level_ups


# =========================================================
# СТАРА НАЗВА ДЛЯ СУМІСНОСТІ
# =========================================================
#
# Старі handlers можуть викликати:
#
# add_total_xp(...)
#
# Тепер це просто додавання XP
# до поточного рівня персонажа.
#
# =========================================================

def add_total_xp(
    player,
    xp
):

    return add_xp_to_player(
        player,
        xp
    )


# =========================================================
# ДОДАТИ XP ДО ПЕРСОНАЖА + СФЕР
# =========================================================
#
# ЦЕ ОСНОВНА ФУНКЦІЯ ДЛЯ АКТИВНОСТЕЙ.
#
# Вона одразу:
#
# 1. Додає XP до персонажа.
# 2. Перевіряє level up персонажа.
# 3. Додає XP до сфер.
# 4. Перевіряє level up сфер.
#
# Повертає:
#
# {
#     "player": [...],
#     "spheres": [...]
# }
#
# =========================================================

def add_xp_to_character(
    player,
    spheres,
    xp
):

    player_level_ups = add_xp_to_player(
        player,
        xp
    )

    sphere_level_ups = add_xp_to_spheres(
        player,
        spheres,
        xp
    )

    return {
        "player": player_level_ups,
        "spheres": sphere_level_ups
    }


# =========================================================
# ОНОВИТИ СТАТИСТИКУ
# =========================================================

def update_statistics(
    player,
    completed_scrolls=0,
    completed_rituals=0,
    plants_harvested=0,
    expeditions_completed=0
):

    statistics = (
        player.get("statistics")
        or {}
    )

    if not isinstance(
        statistics,
        dict
    ):

        statistics = {}

    for key, amount in {

        "completed_scrolls":
            completed_scrolls,

        "completed_rituals":
            completed_rituals,

        "plants_harvested":
            plants_harvested,

        "expeditions_completed":
            expeditions_completed,

    }.items():

        statistics[key] = (
            int(
                statistics.get(
                    key,
                    0
                )
            )
            + amount
        )

    statistics.setdefault(
        "last_summary_date",
        None
    )

    player["statistics"] = (
        statistics
    )


# =========================================================
# КНОПКА НАЗАД
# =========================================================

def build_back_button():

    from telebot import types

    markup = (
        types.ReplyKeyboardMarkup(
            resize_keyboard=True
        )
    )

    markup.row(
        types.KeyboardButton(
            "🔙 Назад"
        )
    )

    return markup


# =========================================================
# ПОВІДОМЛЕННЯ ПРО LEVEL UP СФЕРИ
# =========================================================

def format_sphere_level_up(
    level_up
):

    return (
        "✨ <b>На мить тебе огортає сяйво.</b>\n\n"

        "🦇 <b>Марчелло</b> 🦇:\n"
        "«Схоже, твої зусилля "
        "не минули безслідно.»\n\n"

        f"{level_up['emoji']} "
        f"<b>{level_up['name']}</b> "
        f"досягла рівня "
        f"<b>{level_up['new_level']}</b>!"
    )


# =========================================================
# ПОВІДОМЛЕННЯ ПРО LEVEL UP ПЕРСОНАЖА
# =========================================================

def format_player_level_up(
    level_up
):

    return (
        "✨ <b>Твого героя на мить "
        "огортає яскраве світло.</b>\n\n"

        "🦇 <b>Марчелло</b> 🦇:\n"
        "«А ось це вже не просто "
        "маленький прогрес.»\n\n"

        f"🧙‍♂️ <b>Твій герой досяг "
        f"рівня {level_up['new_level']}!</b>\n\n"

        "«Тепер можеш із гордістю "
        "робити вигляд, що знаєш, "
        "що робиш.»"
    )


# =========================================================
# ВІДПРАВИТИ ПОВІДОМЛЕННЯ ПРО LEVEL UP
# =========================================================
#
# Використання в handler:
#
# result = add_xp_to_character(
#     player,
#     spheres,
#     xp
# )
#
# send_level_up_notifications(
#     message.chat.id,
#     result
# )
#
# =========================================================

def send_level_up_notifications(
    chat_id,
    level_up_data
):

    from services.config import bot

    if not level_up_data:
        return

    # -----------------------------------------------------
    # LEVEL UP ПЕРСОНАЖА
    # -----------------------------------------------------

    player_level_ups = (
        level_up_data.get(
            "player",
            []
        )
    )

    for level_up in player_level_ups:

        bot.send_message(
            chat_id,

            format_player_level_up(
                level_up
            ),

            parse_mode="HTML"
        )

    # -----------------------------------------------------
    # LEVEL UP СФЕР
    # -----------------------------------------------------

    sphere_level_ups = (
        level_up_data.get(
            "spheres",
            []
        )
    )

    for level_up in sphere_level_ups:

        bot.send_message(
            chat_id,

            format_sphere_level_up(
                level_up
            ),

            parse_mode="HTML"
        )
