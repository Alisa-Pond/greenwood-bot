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

        # Прибираємо дублікати
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
# ДОДАТИ XP ДО СФЕР
# =========================================================
#
# XP ділиться порівну між усіма вибраними сферами.
#
# Наприклад:
#
# 9 XP + 🧠🎨
#
# 🧠 отримує 4.5 XP
# 🎨 отримує 4.5 XP
#
# Після додавання XP перевіряється level-up
# кожної сфери окремо.
#
# Функція повертає список підвищень рівня.
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
    # Прибираємо дублікати сфер
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
    # Додаємо XP кожній сфері
    # -----------------------------------------------------

    for sphere in unique_spheres:

        sphere_key = None

        # -------------------------------------------------
        # Пошук сфери за ключем або emoji
        # -------------------------------------------------

        for key, emoji in SPHERE_NAMES.items():

            if (
                sphere == key
                or sphere == emoji
            ):

                sphere_key = key
                break

        # -------------------------------------------------
        # Якщо передали безпосередньо ключ,
        # який існує в player["spheres"]
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

        # -------------------------------------------------
        # Поточний рівень
        # -------------------------------------------------

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
        # Перевіряємо підвищення рівня
        #
        # while, а не if, тому що велика нагорода
        # може підняти сферу одразу на декілька рівнів.
        # -------------------------------------------------

        while (
            data["xp"]
            >= float(
                data.get("max_xp", 10)
            )
        ):

            max_xp = float(
                data.get("max_xp", 10)
            )

            data["xp"] -= max_xp

            data["lvl"] = (
                int(data.get("lvl", 1))
                + 1
            )

            data["max_xp"] = (
                max_xp * 1.5
            )

        # -------------------------------------------------
        # Перевіряємо, чи був level-up
        # -------------------------------------------------

        new_level = int(
            data.get("lvl", 1)
        )

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
    # Поточні значення
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
    # Зараз загальний level персонажа
    # не має окремого max_xp у player.
    #
    # Тому поки що просто накопичуємо xp_total.
    #
    # Механіку загального рівня ми підключимо окремо,
    # коли визначимо його формулу.
    # -----------------------------------------------------

    return {
        "xp_gained": xp,
        "level_ups": []
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
