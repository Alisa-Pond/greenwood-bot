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
# ЧАС ГРІНВУДУ
# =========================================================

def get_greenwood_date(dt=None):
    """
    Повертає дату поточної доби Грінвуду.

    Доба починається о 07:00 за Києвом,
    а не о 00:00.
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
    Отримує список сфер із сувою / ритуалу / рослини.

    Підтримує різні формати старих і нових записів.
    """

    spheres = item.get("spheres")

    if not spheres:
        spheres = item.get("sphere")

    if not spheres:
        return []

    # -----------------------------------------------------
    # Якщо сфери записані одним рядком
    # -----------------------------------------------------

    if isinstance(spheres, str):

        result = []

        for key, emoji in SPHERE_NAMES.items():

            if key in spheres or emoji in spheres:
                result.append(key)

        return result

    # -----------------------------------------------------
    # Якщо сфери записані списком
    # -----------------------------------------------------

    if isinstance(spheres, list):

        result = []

        for sphere in spheres:

            # Новий формат:
            # {"key": "health", "emoji": "💪"}

            if isinstance(sphere, dict):

                key = sphere.get("key")

                if key and key in SPHERE_NAMES:
                    result.append(key)
                    continue

                emoji = sphere.get("emoji")

                for sphere_key, sphere_emoji_value in SPHERE_NAMES.items():

                    if emoji == sphere_emoji_value:
                        result.append(sphere_key)
                        break

            # Формат:
            # "health"

            elif sphere in SPHERE_NAMES:
                result.append(sphere)

            # Формат:
            # "💪"

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

    history = statistics.get(
        "completed_history"
    )

    if not isinstance(history, list):
        history = []

    return history


def save_history(player, history):

    statistics = player.get("statistics") or {}

    statistics["completed_history"] = history

    player["statistics"] = statistics


# =========================================================
# ВИКОНАНІ СПРАВИ ЗА ПОПЕРЕДНЮ ДОБУ
# =========================================================

def get_completed_for_date(player, target_date):

    history = get_history(player)

    result = []

    target = target_date.isoformat()

    for entry in history:

        if entry.get("greenwood_date") == target:
            result.append(entry)

    return result


# =========================================================
# ШТРАФ ЗА ПРОПУЩЕНУ СПРАВУ
# =========================================================

def calculate_penalty(xp):
    """
    За пропущене завдання стягуємо 2/3
    від початкової нагороди.
    """

    return xp * (2 / 3)


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
            player_spheres[sphere].get(
                "xp",
                0
            )
        )

        player_spheres[sphere]["xp"] = max(
            0,
            current_xp - share
        )


def subtract_total_xp(player, xp):

    player["xp_total"] = max(
        0,
        float(
            player.get(
                "xp_total",
                0
            )
        ) - xp
    )


# =========================================================
# АКТИВНІ РИТУАЛИ В ПЕВНИЙ ДЕНЬ
# =========================================================

def ritual_is_for_date(
    ritual,
    target_date
):

    if ritual.get("daily") is True:
        return True

    days = ritual.get("days") or []

    if not isinstance(days, list):
        return False

    weekday = WEEKDAYS[
        target_date.weekday()
    ]

    # Наприклад:
    # [0, 2, 4]

    if target_date.weekday() in days:
        return True

    # Наприклад:
    # ["пн", "ср", "пт"]

    if weekday in days:
        return True

    return False


# =========================================================
# ПОРЯДОК ДЕННИЙ
# =========================================================

def build_agenda(
    player,
    target_date
):

    scrolls = player.get("scrolls") or []
    rituals = player.get("rituals") or []
    plants = player.get("plants") or []

    lines = []

    # =====================================================
    # СУВОЇ
    # =====================================================

    for scroll in scrolls:

        title = get_title(scroll)
        xp = get_xp(scroll)

        deadline = (
            scroll.get("deadline")
            or scroll.get("date")
        )

        fire = False

        if deadline:

            try:

                parsed = None

                for fmt in (
                    "%d.%m.%y",
                    "%d.%m.%Y"
                ):

                    try:

                        parsed = datetime.strptime(
                            deadline,
                            fmt
                        ).date()

                        break

                    except ValueError:
                        continue

                if parsed == target_date:
                    fire = True

            except Exception:
                pass

        icon = "🔥" if fire else "📜"

        lines.append(
            f"{icon} <b>{title}</b> "
            f"({xp:.1f} XP)"
        )

    # =====================================================
    # РИТУАЛИ
    # =====================================================

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

    # =====================================================
    # РОСЛИНИ
    # =====================================================

    for plant in plants:

        title = get_title(plant)
        xp = get_xp(plant)

        deadline = plant.get(
            "deadline"
        )

        icon = "🌱"

        if deadline:

            try:

                parsed = None

                for fmt in (
                    "%d.%m.%y",
                    "%d.%m.%Y"
                ):

                    try:

                        parsed = datetime.strptime(
                            deadline,
                            fmt
                        ).date()

                        break

                    except ValueError:
                        continue

                if parsed == target_date:
                    icon = "🔥"

            except Exception:
                pass

        lines.append(
            f"{icon} <b>{title}</b> "
            f"({xp:.1f} XP)"
        )

    return lines


# =========================================================
# ПІДСУМОК ОДНОГО ГРАВЦЯ
# =========================================================

def make_player_summary(user_id):

    player = get_player(user_id)

    now = datetime.now(KYIV)

    current_greenwood_date = get_greenwood_date(
        now
    )

    previous_date = (
        current_greenwood_date
        - timedelta(days=1)
    )

    # =====================================================
    # ВИКОНАНІ СПРАВИ
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

        entry_type = entry.get(
            "type"
        )

        title = entry.get(
            "title",
            "Без назви"
        )

        try:
            xp = float(
                entry.get(
                    "xp",
                    0
                )
            )

        except (
            TypeError,
            ValueError
        ):

            xp = 0.0

        spheres = entry.get(
            "spheres",
            []
        )

        if isinstance(
            spheres,
            str
        ):
            spheres = get_spheres(
                entry
            )

        # -------------------------------------------------
        # XP по сферах
        # -------------------------------------------------

        if spheres:

            share = (
                xp / len(spheres)
            )

            for sphere in spheres:

                if sphere in earned_by_sphere:

                    earned_by_sphere[
                        sphere
                    ] += share

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

    scrolls = player.get(
        "scrolls"
    ) or []

    missed_activities = []

    remaining_scrolls = []

    for scroll in scrolls:

        deadline = scroll.get(
            "deadline"
        )

        if not deadline:

            remaining_scrolls.append(
                scroll
            )

            continue

        try:

            parsed = None

            for fmt in (
                "%d.%m.%y",
                "%d.%m.%Y"
            ):

                try:

                    parsed = datetime.strptime(
                        deadline,
                        fmt
                    ).date()

                    break

                except ValueError:
                    continue

            if parsed is None:

                remaining_scrolls.append(
                    scroll
                )

                continue

        except ValueError:

            remaining_scrolls.append(
                scroll
            )

            continue

        if parsed < current_greenwood_date:

            xp = get_xp(scroll)

            penalty = calculate_penalty(
                xp
            )

            spheres = get_spheres(
                scroll
            )

            subtract_total_xp(
                player,
                penalty
            )

            subtract_xp_from_spheres(
                player,
                spheres,
                penalty
            )

            share = (
                penalty / len(spheres)
                if spheres
                else 0
            )

            for sphere in spheres:

                if sphere in penalties_by_sphere:

                    penalties_by_sphere[
                        sphere
                    ] += share

            missed_activities.append(
                (
                    get_title(scroll),
                    penalty
                )
            )

            continue

        remaining_scrolls.append(
            scroll
        )

    player["scrolls"] = (
        remaining_scrolls
    )

    # =====================================================
    # ПРОПУЩЕНІ РИТУАЛИ
    # =====================================================

    rituals = player.get(
        "rituals"
    ) or []

    for ritual in rituals:

        if not ritual_is_for_date(
            ritual,
            previous_date
        ):
            continue

        last_completed = ritual.get(
            "last_completed"
        )

        # Ритуал уже виконаний
        # у попередню добу

        if last_completed == previous_date.strftime(
            "%d.%m.%Y"
        ):

            continue

        # Також підтримуємо ISO-формат

        if last_completed == previous_date.isoformat():

            continue

        xp = get_xp(
            ritual
        )

        penalty = calculate_penalty(
            xp
        )

        spheres = get_spheres(
            ritual
        )

        subtract_total_xp(
            player,
            penalty
        )

        subtract_xp_from_spheres(
            player,
            spheres,
            penalty
        )

        share = (
            penalty / len(spheres)
            if spheres
            else 0
        )

        for sphere in spheres:

            if sphere in penalties_by_sphere:

                penalties_by_sphere[
                    sphere
                ] += share

        missed_activities.append(
            (
                get_title(ritual),
                penalty
            )
        )

    # =====================================================
    # ЗБЕРІГАЄМО
    # =====================================================

    statistics = (
        player.get(
            "statistics"
        ) or {}
    )

    statistics[
        "last_summary_date"
    ] = current_greenwood_date.isoformat()

    player[
        "statistics"
    ] = statistics

    update_player(
        user_id,
        {
            "xp_total": player[
                "xp_total"
            ],

            "spheres": player[
                "spheres"
            ],

            "scrolls": player[
                "scrolls"
            ],

            "rituals": player[
                "rituals"
            ],

            "statistics": player[
                "statistics"
            ]
        }
    )

    # =====================================================
    # ТЕКСТ ПІДСУМКУ
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
            "Поки що хроніка мовчить. 🌲\n\n"
        )

    else:

        for title, xp in completed_scrolls:

            text += (
                f"📜 {title} "
                f"✨ +{xp:.1f} XP\n"
            )

        for title, xp in completed_rituals:

            text += (
                f"🔄 {title} "
                f"✨ +{xp:.1f} XP\n"
            )

        for title, xp in completed_plants:

            text += (
                f"🌳 {title} "
                f"✨ +{xp:.1f} XP\n"
            )

        text += "\n"

    # =====================================================
    # ПРОПУЩЕНО
    # =====================================================

    text += (
        "⚠️ <b>Пропущено</b>\n\n"
    )

    if not missed_activities:

        text += (
            "Нічого. Ліс задоволений. 🌿\n\n"
        )

    else:

        for title, penalty in missed_activities:

            text += (
                f"❌ {title} "
                f"−{penalty:.1f} XP\n"
            )

        text += "\n"

    # =====================================================
    # СФЕРИ
    # =====================================================

    text += (
        "🎯 <b>Рух сфер</b>\n\n"
    )

    any_sphere_activity = False

    for sphere, emoji in SPHERE_NAMES.items():

        earned = earned_by_sphere[
            sphere
        ]

        penalty = penalties_by_sphere[
            sphere
        ]

        if (
            earned == 0
            and penalty == 0
        ):
            continue

        any_sphere_activity = True

        text += (
            f"{emoji} "
            f"+{earned:.1f} / "
            f"−{penalty:.1f} XP\n"
        )

    if not any_sphere_activity:

        text += (
            "Сфери сьогодні не змінилися.\n"
        )

    text += "\n"

    # =====================================================
    # ПОРЯДОК ДЕННИЙ
    # =====================================================

    text += (
        "📖 <b>Порядок денний</b>\n\n"
        f"📅 Сьогодні: "
        f"<b>{format_date(current_greenwood_date)}, "
        f"{WEEKDAYS[current_greenwood_date.weekday()]}"
        f"</b>\n\n"
    )

    agenda = build_agenda(
        player,
        current_greenwood_date
    )

    if agenda:

        for line in agenda:

            text += (
                f"{line}\n"
            )

    else:

        text += (
            "🌲 Сьогодні ліс дозволяє "
            "трохи видихнути."
        )

    return text
