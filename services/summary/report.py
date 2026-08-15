from html import escape

from .calculations import get_spheres, get_title, get_xp
from .config import SPHERE_NAMES, WEEKDAYS, format_date, parse_date


def _sphere_prefix(item):
    spheres = get_spheres(item)

    if not spheres:
        return ""

    return "".join(
        SPHERE_NAMES[sphere]
        for sphere in spheres
        if sphere in SPHERE_NAMES
    )


def _safe_title(item):
    return escape(get_title(item))


def _deadline_text(item):
    raw_deadline = item.get("deadline")
    deadline = parse_date(raw_deadline)

    if deadline:
        return format_date(deadline)

    if raw_deadline:
        return escape(str(raw_deadline))

    return "без дедлайну"


def _days_text(item):
    days = item.get("days") or []

    if item.get("daily") is True:
        return "щодня"

    if isinstance(days, list):
        return ", ".join(str(day) for day in days)

    if days:
        return escape(str(days))

    return "не вказано"


def _format_activity(item, activity_type, xp_prefix="⭐"):
    sphere_prefix = _sphere_prefix(item)
    title = _safe_title(item)
    xp = get_xp(item)

    if activity_type == "ritual":
        extra = f"📅 Дні: {_days_text(item)}"
    else:
        extra = f"📅 Дедлайн: {_deadline_text(item)}"

    prefix = f"{sphere_prefix} " if sphere_prefix else ""

    return (
        f"{prefix}<b>{title}</b>\n"
        f"{xp_prefix} {xp:.1f} XP\n"
        f"{extra}\n"
    )


def build_completed_section(
    completed_scrolls,
    completed_rituals,
    completed_plants,
):
    parts = ["✨ <b>Виконано за попередню добу</b>\n"]

    if not (
        completed_scrolls
        or completed_rituals
        or completed_plants
    ):
        parts.append("Поки що хроніка мовчить. 🌲\n")
        return "\n".join(parts)

    if completed_scrolls:
        parts.append("📜 <b>Сувої</b>\n")

        for item in completed_scrolls:
            parts.append(
                _format_activity(item, "scroll") + "\n"
            )

    if completed_rituals:
        parts.append("🔄 <b>Ритуали</b>\n")

        for item in completed_rituals:
            # Навмисно без 📜 перед ритуалом.
            parts.append(
                _format_activity(item, "ritual") + "\n"
            )

    if completed_plants:
        parts.append("🌱 <b>Рослини</b>\n")

        for item in completed_plants:
            parts.append(
                _format_activity(item, "plant") + "\n"
            )

    return "\n".join(parts)


def build_missed_section(missed_activities):
    parts = ["⚠️ <b>Пропущено</b>\n"]

    if not missed_activities:
        parts.append("Нічого. Ліс задоволений. 🌿\n")
        return "\n".join(parts)

    # Той самий порядок: сувої → ритуали → рослини.
    order = {
        "scroll": 0,
        "ritual": 1,
        "plant": 2,
    }

    sorted_items = sorted(
        missed_activities,
        key=lambda x: order.get(x["type"], 99),
    )

    current_type = None

    for entry in sorted_items:
        activity_type = entry["type"]
        item = entry["item"]
        penalty = entry["penalty"]

        if activity_type != current_type:
            current_type = activity_type

            heading = {
                "scroll": "📜 <b>Сувої</b>\n",
                "ritual": "🔄 <b>Ритуали</b>\n",
                "plant": "🌱 <b>Рослини</b>\n",
            }.get(activity_type)

            if heading:
                parts.append(heading)

        sphere_prefix = _sphere_prefix(item)
        title = _safe_title(item)

        if sphere_prefix:
            title_line = f"{sphere_prefix} <b>{title}</b>"
        else:
            title_line = f"<b>{title}</b>"

        parts.append(
            f"{title_line}\n"
            f"⚠️ −{penalty:.1f} XP\n"
            + (
                f"📅 Дні: {_days_text(item)}\n\n"
                if activity_type == "ritual"
                else f"📅 Дедлайн: {_deadline_text(item)}\n\n"
            )
        )

    return "\n".join(parts)


def build_spheres_section(
    earned_by_sphere,
    penalties_by_sphere,
):
    parts = ["🎯 <b>Рух сфер</b>\n"]
    sphere_activity = False

    for sphere, emoji in SPHERE_NAMES.items():
        earned = earned_by_sphere[sphere]
        penalty = penalties_by_sphere[sphere]

        if earned == 0 and penalty == 0:
            continue

        sphere_activity = True

        parts.append(
            f"{emoji} +{earned:.1f} / −{penalty:.1f} XP"
        )

    if not sphere_activity:
        parts.append("Сфери сьогодні не змінилися.")

    return "\n".join(parts)


def build_agenda(player, current_date):
    parts = [
        "📖 <b>Порядок денний</b>\n",
        f"📅 Сьогодні: <b>{format_date(current_date)}, "
        f"{WEEKDAYS[current_date.weekday()]}</b>\n",
    ]

    agenda = []

    for scroll in player.get("scrolls") or []:
        deadline = parse_date(scroll.get("deadline"))
        marker = "🔥" if deadline == current_date else ""

        sphere_prefix = _sphere_prefix(scroll)
        title = _safe_title(scroll)
        xp = get_xp(scroll)

        prefix = f"{sphere_prefix} " if sphere_prefix else ""

        agenda.append(
            f"{marker} {prefix}<b>{title}</b> "
            f"({xp:.1f} XP)"
        )

    for ritual in player.get("rituals") or []:
        if not _ritual_is_for_date_local(ritual, current_date):
            continue

        sphere_prefix = _sphere_prefix(ritual)
        title = _safe_title(ritual)
        xp = get_xp(ritual)

        prefix = f"{sphere_prefix} " if sphere_prefix else ""

        agenda.append(
            f"{prefix}<b>{title}</b> ({xp:.1f} XP)"
        )

    for plant in player.get("plants") or []:
        deadline = parse_date(plant.get("deadline"))
        marker = "🔥" if deadline == current_date else ""

        sphere_prefix = _sphere_prefix(plant)
        title = _safe_title(plant)
        xp = get_xp(plant)

        prefix = f"{sphere_prefix} " if sphere_prefix else ""

        agenda.append(
            f"{marker} {prefix}<b>{title}</b> "
            f"({xp:.1f} XP)"
        )

    if agenda:
        parts.append("\n".join(agenda))
    else:
        parts.append(
            "🌲 Сьогодні ліс дозволяє трохи видихнути."
        )

    return "\n".join(parts)


def _ritual_is_for_date_local(ritual, target_date):
    if ritual.get("daily") is True:
        return True

    days = ritual.get("days") or []

    if not isinstance(days, list):
        return False

    weekday_number = target_date.weekday()

    if weekday_number in days:
        return True

    return WEEKDAYS[weekday_number] in days


def build_full_report(
    previous_date,
    current_date,
    completed_scrolls,
    completed_rituals,
    completed_plants,
    missed_activities,
    earned_by_sphere,
    penalties_by_sphere,
    player,
):
    sections = [
        "🌅 <b>Ранкові хроніки Грінвуду</b>\n",
        f"📅 <b>{format_date(previous_date)}</b>\n"
        "────────────────────",
        build_completed_section(
            completed_scrolls,
            completed_rituals,
            completed_plants,
        ),
        build_missed_section(missed_activities),
        build_spheres_section(
            earned_by_sphere,
            penalties_by_sphere,
        ),
        build_agenda(player, current_date),
    ]

    return "\n\n".join(sections)

