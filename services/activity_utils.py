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


# =========================================================
# БАЗОВИЙ XP ДЛЯ РІВНЯ
# =========================================================

BASE_LEVEL_XP = 10.0

LEVEL_XP_MULTIPLIER = 1.5


# =========================================================
# СМАЙЛИК СФЕРИ
# =========================================================

def get_sphere_emoji(sphere):

    if sphere in SPHERE_NAMES:
        return SPHERE_NAMES[sphere]

    if sphere in SPHERE_NAMES.values():
        return sphere

    return sphere


# =========================================================
# ОТРИМАТИ СФЕРИ З АКТИВНОСТІ
# =========================================================

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

            if sphere_key == spheres or emoji in spheres:
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

        return list(dict.fromkeys(result))

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

    except (TypeError, ValueError):

        return 0.0


# =========================================================
# СЬОГОДНІ
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

        value = item.get(field)

        if value is not None:

            try:

                return abs(
                    float(value)
                )

            except (TypeError, ValueError):

                pass

    return 0.0


# =========================================================
# XP ДО НАСТУПНОГО РІВНЯ СФЕРИ
# =========================================================

def get_sphere_level_xp(sphere_data):

    return float(
        sphere_data.get(
            "max_xp",
            BASE_LEVEL_XP
        )
    )


# =========================================================
# XP ДО НАСТУПНОГО ЗАГАЛЬНОГО РІВНЯ
# =========================================================
#
# Рівень 1:
# 10 XP
#
# Рівень 2:
# 15 XP
#
# Рівень 3:
# 22.5 XP
#
# Рівень 4:
# 33.75 XP
#
# І т.д.
#
# Функція повертає XP, необхідний для переходу
# з поточного рівня на наступний.
#
# =========================================================

def get_total_level_requirement(level):

    requirement = BASE_LEVEL_XP

    for _ in range(
        max(0, int(level) - 1)
    ):

        requirement *= LEVEL_XP_MULTIPLIER

    return requirement


# =========================================================
# XP, НЕОБХІДНИЙ ДЛЯ ДОСЯГНЕННЯ РІВНЯ
# =========================================================
#
# Наприклад:
#
# Для 2 рівня:
# 10 XP
#
# Для 3 рівня:
# 10 + 15 = 25 XP
#
# Для 4 рівня:
# 10 + 15 + 22.5 = 47.5 XP
#
# =========================================================

def get_total_xp_required_for_level(level):

    level = int(level)

    if level <= 1:
        return 0.0

    total_required = 0.0
    requirement = BASE_LEVEL_XP

    for _ in range(1, level):

        total_required += requirement

        requirement *= LEVEL_XP_MULTIPLIER

    return total_required


# =========================================================
# ДОДАТИ XP ДО СФЕР
# =========================================================
#
# Якщо:
#
# 9 XP + 🧠🎨
#
# тоді:
#
# 🧠 +4.5 XP
# 🎨 +4.5 XP
#
# Після цього кожна сфера окремо перевіряється
# на підвищення рівня.
#
# =========================================================

def add_xp_to_spheres(
    player,
    spheres,
    total_xp
):

    level_ups = []

    if not spheres or total_xp <= 0:
        return level_ups

    player_spheres = player.get(
        "spheres"
    ) or {}

    # -----------------------------------------------------
    # Прибираємо дублікати
    # -----------------------------------------------------

    unique_spheres = list(
        dict.fromkeys(spheres)
    )

    if not unique_spheres:
        return level_ups

    # -----------------------------------------------------
    # XP ділиться порівну
    # -----------------------------------------------------

    share = (
        float(total_xp)
        / len(unique_spheres)
    )

    # -----------------------------------------------------
    # Обробляємо кожну сферу
    # -----------------------------------------------------

    for sphere in unique_spheres:

        sphere_key = None

        # -------------------------------------------------
        # Пошук ключа сфери
        # -------------------------------------------------

        for key, emoji in SPHERE_NAMES.items():

            if (
                sphere == key
                or sphere == emoji
            ):

                sphere_key = key
                break

        # -------------------------------------------------
        # Якщо передано ключ напряму
        # -------------------------------------------------

        if sphere in player_spheres:

            sphere_key = sphere

        # -------------------------------------------------
        # Невідома сфера
        # -------------------------------------------------

        if (
            not sphere_key
            or sphere_key not in player_spheres
        ):

            continue

        data = player_spheres[sphere_key]

        old_level = int(
            data.get("lvl", 1)
        )

        # -------------------------------------------------
        # Додаємо XP
        # -------------------------------------------------

        data["xp"] = (
            float(data.get("xp", 0))
            + share
        )

        # -------------------------------------------------
        # Перевірка level-up
        # -------------------------------------------------

        while (
            data["xp"]
            >= float(
                data.get(
                    "max_xp",
                    BASE_LEVEL_XP
                )
            )
        ):

            max_xp = float(
                data.get(
                    "max_xp",
                    BASE_LEVEL_XP
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

            data["max_xp"] = (
                max_xp
                * LEVEL_XP_MULTIPLIER
            )

        new_level = int(
            data.get(
                "lvl",
                1
            )
        )

        # -------------------------------------------------
        # Записуємо level-up
        # -------------------------------------------------

        if new_level > old_level:

            level_ups.append(
                {
                    "sphere": sphere_key,
                    "emoji": SPHERE_NAMES.get(
                        sphere_key,
                        sphere_key
                    ),
                    "old_level": old_level,
                    "new_level": new_level
                }
            )

    return level_ups


# =========================================================
# ДОДАТИ ЗАГАЛЬНИЙ XP ПЕРСОНАЖА
# =========================================================
#
# Загальний XP НЕ ділиться між сферами.
#
# Якщо активність дає 9 XP:
#
# xp_total += 9
#
# Після цього перевіряється загальний рівень.
#
# =========================================================

def add_total_xp(
    player,
    xp
):

    try:

        xp = float(xp)

    except (
        TypeError,
        ValueError
    ):

        return {
            "xp_gained": 0.0,
            "level_ups": []
        }

    if xp <= 0:

        return {
            "xp_gained": 0.0,
            "level_ups": []
        }

    # -----------------------------------------------------
    # Поточний рівень
    # -----------------------------------------------------

    old_level = int(
        player.get(
            "level",
            1
        )
    )

    # -----------------------------------------------------
    # Додаємо загальний XP
    # -----------------------------------------------------

    player["xp_total"] = (
        float(
            player.get(
                "xp_total",
                0
            )
        )
        + xp
    )

    # -----------------------------------------------------
    # Визначаємо новий рівень
    # -----------------------------------------------------
    #
    # xp_total є накопиченим XP.
    #
    # Тому шукаємо найвищий рівень,
    # поріг якого вже досягнуто.
    #
    # -----------------------------------------------------

    new_level = old_level

    while (
        player["xp_total"]
        >= get_total_xp_required_for_level(
            new_level + 1
        )
    ):

        new_level += 1

    player["level"] = new_level

    # -----------------------------------------------------
    # Якщо рівень підвищився
    # -----------------------------------------------------

    level_ups = []

    if new_level > old_level:

        level_ups.append(
            {
                "old_level": old_level,
                "new_level": new_level
            }
        )

    return {
        "xp_gained": xp,
        "level_ups": level_ups
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

    statistics = player.get(
        "statistics"
    ) or {}

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
# КНОПКА "НАЗАД"
# =========================================================

def build_back_button():

    from telebot import types

    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    markup.row(
        types.KeyboardButton(
            "🔙 Назад"
        )
    )

    return markup
