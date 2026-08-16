from datetime import datetime

SPHERE_NAMES = {
    "health": "💪",
    "wisdom": "🧠",
    "art": "🎨",
    "finance": "💵",
    "relations": "🤝",
}


# =========================================================
# СФЕРИ
# =========================================================

def get_sphere_emoji(sphere):

    if sphere in SPHERE_NAMES:
        return SPHERE_NAMES[sphere]

    if sphere in SPHERE_NAMES.values():
        return sphere

    return sphere


def get_spheres(item):

    spheres = item.get("spheres") or item.get("sphere")

    if not spheres:
        return []

    # -----------------------------------------------------
    # Якщо сфера записана як рядок
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
    # Якщо сфери записані як список
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
# ЗАГАЛЬНІ ДАНІ АКТИВНОСТІ
# =========================================================

def get_title(item):

    return (
        item.get("title")
        or item.get("name")
        or item.get("task")
        or "Без назви"
    )


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


def get_today():

    return datetime.now().strftime(
        "%d.%m.%Y"
    )


# =========================================================
# ДЕДЛАЙНИ
# =========================================================

def parse_deadline(deadline):

    if not deadline:
        return None

    value = str(deadline).strip()

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


def get_penalty_xp(item):

    for field in (
        "penalty",
        "penalty_xp",
        "overdue_penalty"
    ):

        value = item.get(field)

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
# XP СФЕР
# =========================================================
#
# XP активності ділиться між усіма вибраними сферами.
#
# Наприклад:
#
# 9 XP + 🧠🎨
#
# 9 / 2 = 4.5 XP
#
# 🧠 +4.5
# 🎨 +4.5
#
# Після додавання XP перевіряється підвищення рівня.
#
# При підвищенні:
#
# старий max_xp × 1.5 = новий max_xp
#
# =========================================================

def add_xp_to_spheres(
    player,
    spheres,
    total_xp
):

    if (
        not spheres
        or total_xp <= 0
    ):
        return []

    player_spheres = (
        player.get("spheres")
        or {}
    )

    # -----------------------------------------------------
    # Нормалізуємо список сфер
    # -----------------------------------------------------

    normalized_spheres = []

    for sphere in spheres:

        sphere_key = None

        for key, emoji in SPHERE_NAMES.items():

            if (
                sphere == key
                or sphere == emoji
            ):

                sphere_key = key
                break

        if (
            sphere_key
            and sphere_key in player_spheres
            and sphere_key not in normalized_spheres
        ):

            normalized_spheres.append(
                sphere_key
            )

    if not normalized_spheres:
        return []

    # -----------------------------------------------------
    # Ділимо XP між сферами
    # -----------------------------------------------------

    share = (
        float(total_xp)
        / len(normalized_spheres)
    )

    level_ups = []

    # -----------------------------------------------------
    # Додаємо XP та перевіряємо рівні
    # -----------------------------------------------------

    for sphere_key in normalized_spheres:

        data = player_spheres[
            sphere_key
        ]

        data["xp"] = (
            float(
                data.get("xp", 0)
            )
            + share
        )

        # -------------------------------------------------
        # Перевіряємо можливі підвищення
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

            old_max_xp = float(
                data.get(
                    "max_xp",
                    10
                )
            )

            data["xp"] -= old_max_xp

            old_level = int(
                data.get(
                    "lvl",
                    1
                )
            )

            new_level = (
                old_level + 1
            )

            new_max_xp = (
                old_max_xp * 1.5
            )

            data["lvl"] = new_level
            data["max_xp"] = new_max_xp

            level_ups.append(
                {
                    "type": "sphere",
                    "sphere": sphere_key,
                    "emoji": SPHERE_NAMES[
                        sphere_key
                    ],
                    "level": new_level,
                }
            )

    return level_ups


# =========================================================
# ЗАГАЛЬНИЙ XP
# =========================================================

def add_total_xp(
    player,
    xp
):

    if xp <= 0:
        return []

    current_xp = float(
        player.get(
            "xp_total",
            0
        )
    )

    current_level = int(
        player.get(
            "level",
            1
        )
    )

    # -----------------------------------------------------
    # Для загального рівня використовуємо таку ж систему:
    #
    # стартовий поріг = 10 XP
    #
    # після кожного рівня:
    #
    # max_xp × 1.5
    #
    # -----------------------------------------------------

    max_xp = float(
        player.get(
            "max_xp",
            10
        )
    )

    current_xp += float(xp)

    level_ups = []

    # -----------------------------------------------------
    # Перевіряємо підвищення рівня
    # -----------------------------------------------------

    while current_xp >= max_xp:

        current_xp -= max_xp

        current_level += 1

        max_xp *= 1.5

        level_ups.append(
            {
                "type": "player",
                "level": current_level,
            }
        )

    player["xp_total"] = current_xp
    player["level"] = current_level
    player["max_xp"] = max_xp

    return level_ups


# =========================================================
# ПОВІДОМЛЕННЯ ПРО ПІДВИЩЕННЯ РІВНЯ
# =========================================================

def build_level_up_messages(
    level_ups
):

    if not level_ups:
        return []

    messages = []

    # -----------------------------------------------------
    # Повідомлення про сфери
    # -----------------------------------------------------

    for event in level_ups:

        if event.get("type") != "sphere":
            continue

        emoji = event.get(
            "emoji",
            ""
        )

        sphere_names = {
            "health": "Здоров'я",
            "wisdom": "Мудрість",
            "art": "Творчість",
            "finance": "Фінанси",
            "relations": "Зв'язки",
        }

        sphere_name = sphere_names.get(
            event.get("sphere"),
            "Сфера"
        )

        level = event.get(
            "level"
        )

        messages.append(
            "✨ <b>На мить тебе огортає сяйво.</b>\n\n"

            "🦇 <b>Марчелло</b> 🦇:\n"
            "«Схоже, твої зусилля не минули "
            "безслідно.»\n\n"

            f"{emoji} <b>{sphere_name}: "
            f"рівень {level}!</b>"
        )

    # -----------------------------------------------------
    # Повідомлення про загальний рівень
    # -----------------------------------------------------

    for event in level_ups:

        if event.get("type") != "player":
            continue

        level = event.get(
            "level"
        )

        messages.append(
            "✨ <b>Твого героя на мить "
            "огортає яскраве світло.</b>\n\n"

            "🦇 <b>Марчелло</b> 🦇:\n"
            "«А ось це вже не просто "
            "маленький прогрес.»\n\n"

            f"🧙‍♂️ <b>Твій герой досяг "
            f"рівня {level}!</b>\n\n"

            "«Тепер можеш із гордістю "
            "робити вигляд, що знаєш, "
            "що робиш.»"
        )

    return messages


# =========================================================
# СТАТИСТИКА
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

    player["statistics"] = statistics


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
