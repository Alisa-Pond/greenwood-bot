from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from services.database import get_player, update_player


# =========================================================
# НАЛАШТУВАННЯ
# =========================================================

KYIV = ZoneInfo("Europe/Kyiv")

SPHERE_NAMES = {
    "health": "💪",
    "wisdom": "🧠",
    "art": "🎨",
    "finance": "💵",
    "relations": "🤝"
}

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
# ДОБА ГРІНВУДУ
# =========================================================

def get_greenwood_date(dt=None):
    """
    Доба Грінвуду триває з 07:00 до 06:59 наступного дня.

    Наприклад:
    11.08 06:59 → ще доба 10.08
    11.08 07:00 → вже доба 11.08
    """

    if dt is None:
        dt = datetime.now(KYIV)

    if dt.hour < 7:
        dt = dt - timedelta(days=1)

    return dt.date()


def format_date(date):
    return date.strftime("%d.%m.%Y")


# =========================================================
# СФЕРИ
# =========================================================

def sphere_emoji(sphere):
    return SPHERE_NAMES.get(sphere, sphere)


def get_spheres(item):
    """
    Отримує сфери зі старих і нових форматів запису.
    """

    spheres = item.get("spheres")

    if not spheres:
        spheres = item.get("sphere")

    if not spheres:
        return []

    # -----------------------------------------------------
    # Один рядок
    # -----------------------------------------------------

    if isinstance(spheres, str):

        result = []

        for key, emoji in SPHERE_NAMES.items():

            if key in spheres or emoji in spheres:
                result.append(key)

        return result

    # -----------------------------------------------------
    # Список
    # -----------------------------------------------------

    if isinstance(spheres, list):

        result = []

        for sphere in spheres:

            if isinstance(sphere, dict):

                key = sphere.get("key")

                if key in SPHERE_NAMES:
                    result.append(key)
                    continue

                emoji = sphere.get("emoji")

                for sphere_key, sphere_emoji_value in SPHERE_NAMES.items():

                    if emoji == sphere_emoji_value:
                        result.append(sphere_key)
                        break

            elif sphere in SPHERE_NAMES:

                result.append(sphere)

            elif sphere in SPHERE_NAMES.values():

                for key, emoji in SPHERE_NAMES.items():

                    if sphere == emoji:
                        result.append(key)
                        break

        return result

    return []


# =========================================================
# ЗАГАЛЬНІ ДАНІ
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

    except (TypeError, ValueError):
        return 0.0


# =========================================================
# ІСТОРІЯ ВИКОНАНИХ СПРАВ
# =========================================================

def get_history(player):

    statistics = player.get("statistics") or {}

    history = statistics.get("completed_history")

    if not isinstance(history, list):
        return []

    return history


def get_completed_for_date(player, target_date):

    history = get_history(player)

    result = []

    target = target_date.isoformat()

    for entry in history:

        if entry.get("greenwood_date") == target:
            result.append(entry)

    return result


# =========================================================
# ШТРАФ
# =========================================================

def calculate_penalty(xp):
    """
    За пропущену справу стягується 2/3
    від її початкової нагороди.
    """

    return xp * (2 / 3)


def subtract_total_xp(player, xp):

    player["xp_total"] = max(
        0.0,
        float(player.get("xp_total", 0))
        - float(xp)
    )


def subtract_xp_from_spheres(
    player,
    spheres,
    total_xp
):

    if not spheres or total_xp <= 0:
        return

    player_spheres = player.get("spheres") or {}

    share = total_xp / len(spheres)

    for sphere in spheres:

        if sphere not in player_spheres:
            continue

        current_xp = float(
            player_spheres[sphere].get("xp", 0)
        )

        player_spheres[sphere]["xp"] = max(
            0.0,
            current_xp - share
        )


# =========================================================
# РИТУАЛИ
# =========================================================

def ritual_is_for_date(ritual, target_date):

    if ritual.get("daily") is True:
        return True

    days = ritual.get("days") or []

    if not isinstance(days, list):
        return False

    weekday_number = target_date.weekday()

    if weekday_number in days:
        return True

    weekday_name = WEEKDAYS[weekday_number]

    if weekday_name in days:
        return True

    return False


def ritual_was_completed_on_date(
    ritual,
    target_date
):

    completed = ritual.get("last_completed")

    if not completed:
        return False

    possible_formats = [
        "%d.%m.%Y",
        "%d.%m.%y"
    ]

    for fmt in possible_formats:

        try:

            parsed = datetime.strptime(
                completed,
                fmt
            ).date()

            return parsed == target_date

        except ValueError:
            continue

    if completed == target_date.isoformat():
        return True

    return False


# =========================================================
# DEADLINE
# =========================================================

def parse_deadline(value):

    if not value:
        return None

    if not isinstance(value, str):
        return None

    for fmt in (
        "%d.%m.%y",
        "%d.%m.%Y"
    ):

        try:

            return datetime.strptime(
                value,
                fmt
            ).date()

        except ValueError:
            continue

    return None


# =========================================================
# ПОРЯДОК ДЕННИЙ
# =========================================================

def build_agenda(player, target_date):

    scrolls = player.get("scrolls") or []
    rituals = player.get("rituals") or []
    plants = player.get("plants") or []

    lines = []

    # -----------------------------------------------------
    # СУВОЇ
    # -----------------------------------------------------

    for scroll in scrolls:

        title = get_title(scroll)
        xp = get_xp(scroll)

        deadline = parse_deadline(
            scroll.get("deadline")
            or scroll.get("date")
        )

        if deadline == target_date:
            icon = "🔥"
        else:
            icon = "📜"

        lines.append(
            f"{icon} <b>{title}</b> "
            f"({xp:.1f} XP)"
        )

    # -----------------------------------------------------
    # РИТУАЛИ
    # -----------------------------------------------------

    for ritual in rituals:

        if not ritual_is_for_date(
            ritual,
            target_date
        ):
            continue

        title = get_title(ritual)
        xp = get_xp(ritual)

        lines.append(
            f"🔄 <b>{title}</b> "
            f"({xp:.1f} XP)"
        )

    # -----------------------------------------------------
    # РОСЛИНИ
    # -----------------------------------------------------

    for plant in plants:

        title = get_title(plant)
        xp = get_xp(plant)

        deadline = parse_deadline(
            plant.get("deadline")
        )

        icon = "🔥" if deadline == target_date else "🌱"

        lines.append(
            f"{icon} <b>{title}</b> "
            f"({xp:.1f} XP)"
        )

    return lines


# =========================================================
# ПІДСУМОК ОДНОГО ГРАВЦЯ
# =========================================================

def make_player_summary(user_id):

    player = get_player(str(user_id))

    now = datetime.now(KYIV)

    current_greenwood_date = get_greenwood_date(now)

    previous_date = (
        current_greenwood_date
        - timedelta(days=1)
    )

    # =====================================================
    # ЗБИРАЄМО ВИКОНАНЕ
    # =====================================================

    completed = get_completed_for_date(
        player,
        previous_date
    )

    earned_by_sphere = {
        key: 0.0
        for key in SPHERE_NAMES
    }

    penalties_by_sphere = {
        key: 0.0
        for key in SPHERE_NAMES
    }

    completed_scrolls = []
    completed_rituals = []
    completed_plants = []

    for entry in completed:

        entry_type = entry.get("type")

        title = entry.get(
            "title",
            "Без назви"
        )

        xp = get_xp(entry)

        spheres = get_spheres(entry)

        # -------------------------------------------------
        # Нарахування XP по сферах
        # -------------------------------------------------

        if spheres:

            share = xp / len(spheres)

            for sphere in spheres:

                if sphere in earned_by_sphere:

                    earned_by_sphere[sphere] += share

        # -------------------------------------------------
        # Категорія
        # -------------------------------------------------

        if entry_type == "scroll":

            completed_scrolls.append(
                (title, xp)
            )

        elif entry_type == "ritual":

            completed_rituals.append(
                (title, xp)
            )

        elif entry_type == "plant":

            completed_plants.append(
                (title, xp)
            )

    # =====================================================
    # ПРОПУЩЕНІ СУВОЇ
    # =====================================================

    scrolls = player.get("scrolls") or []

    remaining_scrolls = []
    missed_activities = []

    for scroll in scrolls:

        deadline = parse_deadline(
            scroll.get("deadline")
        )

        # Сувій без дедлайну не штрафується
        if deadline is None:

            remaining_scrolls.append(scroll)
            continue

        # Дедлайн ще не минув
        if deadline >= current_greenwood_date:

            remaining_scrolls.append(scroll)
            continue

        # -------------------------------------------------
        # Прострочений сувій
        # -------------------------------------------------

        xp = get_xp(scroll)
        penalty = calculate_penalty(xp)

        spheres = get_spheres(scroll)

        subtract_total_xp(
            player,
            penalty
        )

        subtract_xp_from_spheres(
            player,
            spheres,
            penalty
        )

        if spheres:

            share = penalty / len(spheres)

            for sphere in spheres:

                if sphere in penalties_by_sphere:

                    penalties_by_sphere[sphere] += share

        missed_activities.append(
            (
                "📜",
                get_title(scroll),
                penalty
            )
        )

    player["scrolls"] = remaining_scrolls

    # =====================================================
    # ПРОПУЩЕНІ РИТУАЛИ
    # =====================================================

    rituals = player.get("rituals") or []

    for ritual in rituals:

        # Ритуал повинен був відбутися
        # саме в попередню добу

        if not ritual_is_for_date(
            ritual,
            previous_date
        ):
            continue

        # Якщо виконаний вчасно,
        # штрафу немає

        if ritual_was_completed_on_date(
            ritual,
            previous_date
        ):
            continue

        xp = get_xp(ritual)
        penalty = calculate_penalty(xp)

        spheres = get_spheres(ritual)

        subtract_total_xp(
            player,
            penalty
        )

        subtract_xp_from_spheres(
            player,
            spheres,
            penalty
        )

        if spheres:

            share = penalty / len(spheres)

            for sphere in spheres:

                if sphere in penalties_by_sphere:

                    penalties_by_sphere[sphere] += share

        missed_activities.append(
            (
                "🔄",
                get_title(ritual),
                penalty
            )
        )

    # =====================================================
    # ЗБЕРІГАЄМО ДАТУ ОСТАННЬОГО ПІДСУМКУ
    # =====================================================

    statistics = player.get("statistics") or {}

    statistics["last_summary_date"] = (
        current_greenwood_date.isoformat()
    )

    player["statistics"] = statistics

    # =====================================================
    # ЗБЕРІГАЄМО ЗМІНИ
    # =====================================================

    update_player(
        str(user_id),
        {
            "xp_total": player["xp_total"],
            "spheres": player["spheres"],
            "scrolls": player["scrolls"],
            "rituals": player["rituals"],
            "statistics": player["statistics"]
        }
    )

    # =====================================================
    # ФОРМУЄМО ПОВІДОМЛЕННЯ
    # =====================================================

    text = (
        "🌅 <b>Ранкові хроніки Грінвуду</b>\n\n"
        f"📅 <b>{format_date(previous_date)}</b>\n"
        "────────────────────\n\n"
    )

    # =====================================================
    # ВИКОНАНО
    # =====================================================

    text += (
        "✨ <b>Виконано за попередню добу</b>\n\n"
    )

    if not (
        completed_scrolls
        or completed_rituals
        or completed_plants
    ):

        text += (
            "Хроніка поки що мовчить. 🌲\n\n"
        )

    else:

        for title, xp in completed_scrolls:

            text += (
                f"📜 <b>{title}</b> "
                f"✨ +{xp:.1f} XP\n"
            )

        for title, xp in completed_rituals:

            text += (
                f"🔄 <b>{title}</b> "
                f"✨ +{xp:.1f} XP\n"
            )

        for title, xp in completed_plants:

            text += (
                f"🌳 <b>{title}</b> "
                f"✨ +{xp:.1f} XP\n"
            )

        text += "\n"

    # =====================================================
    # ПРОПУЩЕНО
    # =====================================================

    text += (
        "⚠️ <b>Пропущено за дедлайном</b>\n\n"
    )

    if not missed_activities:

        text += (
            "Нічого не пропущено. Ліс задоволений. 🌿\n\n"
        )

    else:

        for icon, title, penalty in missed_activities:

            text += (
                f"{icon} <b>{title}</b> "
                f"−{penalty:.1f} XP\n"
            )

        text += "\n"

    # =====================================================
    # РУХ СФЕР
    # =====================================================

    text += (
        "🎯 <b>Рух сфер</b>\n\n"
    )

    any_sphere_activity = False

    for sphere, emoji in SPHERE_NAMES.items():

        earned = earned_by_sphere[sphere]
        penalty = penalties_by_sphere[sphere]

        if earned == 0 and penalty == 0:
            continue

        any_sphere_activity = True

        text += (
            f"{emoji} "
            f"<b>+{earned:.1f}</b> / "
            f"<b>−{penalty:.1f}</b> XP\n"
        )

    if not any_sphere_activity:

        text += (
            "Сфери за попередню добу не змінилися.\n"
        )

    text += "\n"

    # =====================================================
    # ПОРЯДОК ДЕННИЙ
    # =====================================================

    text += (
        "📖 <b>Порядок денний</b>\n\n"
        f"📅 Сьогодні: "
        f"<b>{format_date(current_greenwood_date)}, "
        f"{WEEKDAYS[current_greenwood_date.weekday()]}</b>\n\n"
    )

    agenda = build_agenda(
        player,
        current_greenwood_date
    )

    if agenda:

        for line in agenda:

            text += f"{line}\n"

    else:

        text += (
            "🌲 Сьогодні ліс дозволяє "
            "трохи видихнути."
        )

    return text
