from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from services.config import bot
from services.database import (
    get_player,
    get_all_players,
    update_player
)


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
# ДАТА ГРІНВУДУ
# =========================================================

def get_greenwood_date(dt=None):

    if dt is None:
        dt = datetime.now(KYIV)

    if dt.hour < 7:
        dt -= timedelta(days=1)

    return dt.date()


def format_date(date):

    return date.strftime(
        "%d.%m.%Y"
    )


def parse_date(value):

    if not value:
        return None

    if hasattr(value, "date"):
        return value.date()

    if not isinstance(value, str):
        return None

    value = value.strip()

    for fmt in (
        "%d.%m.%y",
        "%d.%m.%Y",
        "%Y-%m-%d"
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
# СФЕРИ
# =========================================================

def get_spheres(item):

    spheres = item.get("spheres")

    if not spheres:
        spheres = item.get("sphere")

    if not spheres:
        return []

    result = []

    if isinstance(
        spheres,
        str
    ):

        for key, emoji in SPHERE_NAMES.items():

            if (
                spheres == key
                or emoji in spheres
            ):
                result.append(key)

        return result

    if isinstance(
        spheres,
        list
    ):

        for sphere in spheres:

            if isinstance(
                sphere,
                dict
            ):

                key = sphere.get(
                    "key"
                )

                emoji = sphere.get(
                    "emoji"
                )

                if (
                    key
                    and key in SPHERE_NAMES
                ):

                    result.append(key)

                elif emoji:

                    for sphere_key, sphere_emoji in SPHERE_NAMES.items():

                        if (
                            emoji
                            == sphere_emoji
                        ):

                            result.append(
                                sphere_key
                            )

                            break

            elif sphere in SPHERE_NAMES:

                result.append(
                    sphere
                )

            elif sphere in SPHERE_NAMES.values():

                for key, emoji in SPHERE_NAMES.items():

                    if sphere == emoji:

                        result.append(key)

                        break

    return list(
        dict.fromkeys(result)
    )


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

    except (
        TypeError,
        ValueError
    ):

        return 0.0


# =========================================================
# ШТРАФ
# =========================================================

def calculate_penalty(item):

    """
    Штраф за пропущену справу.

    Основне правило:
        штраф = 2/3 від XP.

    Підтримуються різні назви поля,
    щоб не ламати вже створені записи.
    """

    try:

        penalty_value = (
            item.get("penalty")
        )

        if penalty_value is None:

            penalty_value = (
                item.get("penalty_xp")
            )

        if penalty_value is None:

            penalty_value = (
                item.get("penalty_points")
            )

        if penalty_value is not None:

            return max(
                0.0,
                float(penalty_value)
            )

    except (
        TypeError,
        ValueError
    ):
        pass

    xp = get_xp(item)

    return xp * (
        2 / 3
    )


# =========================================================
# ВІДНІМАННЯ XP
# =========================================================

def subtract_xp(
    player,
    total_xp,
    spheres
):

    if total_xp <= 0:
        return

    player["xp_total"] = max(
        0.0,
        float(
            player.get(
                "xp_total",
                0
            )
        ) - total_xp
    )

    player_spheres = (
        player.get("spheres")
        or {}
    )

    if not spheres:
        return

    share = (
        total_xp
        / len(spheres)
    )

    for sphere in spheres:

        if sphere not in player_spheres:
            continue

        sphere_data = (
            player_spheres[sphere]
        )

        current_xp = float(
            sphere_data.get(
                "xp",
                0
            )
        )

        sphere_data["xp"] = max(
            0.0,
            current_xp - share
        )


# =========================================================
# РИТУАЛЬНИЙ РОЗКЛАД
# =========================================================

def ritual_is_for_date(
    ritual,
    target_date
):

    if ritual.get(
        "daily"
    ) is True:

        return True

    days = ritual.get(
        "days"
    ) or []

    if not isinstance(
        days,
        list
    ):
        return False

    weekday_number = (
        target_date.weekday()
    )

    if weekday_number in days:
        return True

    weekday_name = WEEKDAYS[
        weekday_number
    ]

    if weekday_name in days:
        return True

    return False


# =========================================================
# ЧИ БУВ РИТУАЛ ВИКОНАНИЙ
# =========================================================

def ritual_was_completed(
    ritual,
    target_date
):

    completed_date = (
        ritual.get(
            "last_completed"
        )
    )

    if not completed_date:
        return False

    parsed = parse_date(
        completed_date
    )

    return (
        parsed == target_date
    )


# =========================================================
# ЗАПИС ШТРАФУ В СТАТИСТИКУ
# =========================================================

def update_statistics(
    player,
    key,
    amount=1
):

    statistics = (
        player.get(
            "statistics"
        ) or {}
    )

    if not isinstance(
        statistics,
        dict
    ):
        statistics = {}

    statistics[key] = (
        int(
            statistics.get(
                key,
                0
            )
        )
        + amount
    )

    player["statistics"] = (
        statistics
    )


# =========================================================
# ПІДСУМОК ОДНОГО ГРАВЦЯ
# =========================================================

def make_player_summary(
    user_id
):

    user_id = str(user_id)

    player = get_player(
        user_id
    )

    now = datetime.now(
        KYIV
    )

    current_date = (
        get_greenwood_date(now)
    )

    previous_date = (
        current_date
        - timedelta(days=1)
    )

    # =====================================================
    # ЗАХИСТ ВІД ПОВТОРНОГО ПІДСУМКУ
    # =====================================================

    statistics = (
        player.get(
            "statistics"
        ) or {}
    )

    last_summary_date = (
        statistics.get(
            "last_summary_date"
        )
    )

    if (
        last_summary_date
        == current_date.isoformat()
    ):

        return None

    # =====================================================
    # АРХІВ ВИКОНАНИХ СПРАВ
    # =====================================================

    scroll_archive = (
        player.get(
            "scroll_archive"
        ) or []
    )

    ritual_archive = (
        player.get(
            "ritual_archive"
        ) or []
    )

    plant_archive = (
        player.get(
            "plant_archive"
        ) or []
    )

    completed_scrolls = []
    completed_rituals = []
    completed_plants = []

    earned_by_sphere = {
        key: 0.0
        for key in SPHERE_NAMES
    }

    # =====================================================
    # ВИКОНАНІ СУВОЇ
    # =====================================================

    for item in scroll_archive:

        completed_date = parse_date(
            item.get(
                "completed_date"
            )
        )

        if completed_date != previous_date:
            continue

        xp = get_xp(item)

        spheres = get_spheres(
            item
        )

        completed_scrolls.append(
            (
                get_title(item),
                xp
            )
        )

        if spheres:

            share = (
                xp / len(spheres)
            )

            for sphere in spheres:

                if sphere in earned_by_sphere:

                    earned_by_sphere[
                        sphere
                    ] += share

    # =====================================================
    # ВИКОНАНІ РИТУАЛИ
    # =====================================================

    for item in ritual_archive:

        completed_date = parse_date(
            item.get(
                "completed_date"
            )
        )

        if completed_date != previous_date:
            continue

        xp = get_xp(item)

        spheres = get_spheres(
            item
        )

        completed_rituals.append(
            (
                get_title(item),
                xp
            )
        )

        if spheres:

            share = (
                xp / len(spheres)
            )

            for sphere in spheres:

                if sphere in earned_by_sphere:

                    earned_by_sphere[
                        sphere
                    ] += share

    # =====================================================
    # ВИКОНАНІ РОСЛИНИ
    # =====================================================

    for item in plant_archive:

        completed_date = parse_date(
            item.get(
                "completed_date"
            )
        )

        if completed_date != previous_date:
            continue

        xp = get_xp(item)

        spheres = get_spheres(
            item
        )

        completed_plants.append(
            (
                get_title(item),
                xp
            )
        )

        if spheres:

            share = (
                xp / len(spheres)
            )

            for sphere in spheres:

                if sphere in earned_by_sphere:

                    earned_by_sphere[
                        sphere
                    ] += share

    # =====================================================
    # ШТРАФИ
    # =====================================================

    penalties_by_sphere = {
        key: 0.0
        for key in SPHERE_NAMES
    }

    missed_activities = []

    scrolls = (
        player.get(
            "scrolls"
        ) or []
    )

    remaining_scrolls = []

    # =====================================================
    # ПРОПУЩЕНІ СУВОЇ
    # =====================================================

    for scroll in scrolls:

        deadline = parse_date(
            scroll.get(
                "deadline"
            )
        )

        if deadline is None:

            remaining_scrolls.append(
                scroll
            )

            continue

        if deadline >= current_date:

            remaining_scrolls.append(
                scroll
            )

            continue

        penalty = calculate_penalty(
            scroll
        )

        spheres = get_spheres(
            scroll
        )

        subtract_xp(
            player,
            penalty,
            spheres
        )

        if spheres:

            share = (
                penalty
                / len(spheres)
            )

            for sphere in spheres:

                if sphere in penalties_by_sphere:

                    penalties_by_sphere[
                        sphere
                    ] += share

        missed_activities.append(
            (
                "📜",
                get_title(scroll),
                penalty
            )
        )

    player["scrolls"] = (
        remaining_scrolls
    )

    # =====================================================
    # ПРОПУЩЕНІ РОСЛИНИ
    # =====================================================

    plants = (
        player.get(
            "plants"
        ) or []
    )

    remaining_plants = []

    for plant in plants:

        deadline = parse_date(
            plant.get(
                "deadline"
            )
        )

        if deadline is None:

            remaining_plants.append(
                plant
            )

            continue

        if deadline >= current_date:

            remaining_plants.append(
                plant
            )

            continue

        penalty = calculate_penalty(
            plant
        )

        spheres = get_spheres(
            plant
        )

        subtract_xp(
            player,
            penalty,
            spheres
        )

        if spheres:

            share = (
                penalty
                / len(spheres)
            )

            for sphere in spheres:

                if sphere in penalties_by_sphere:

                    penalties_by_sphere[
                        sphere
                    ] += share

        missed_activities.append(
            (
                "🌱",
                get_title(plant),
                penalty
            )
        )

    player["plants"] = (
        remaining_plants
    )

    # =====================================================
    # ПРОПУЩЕНІ РИТУАЛИ
    # =====================================================

    rituals = (
        player.get(
            "rituals"
        ) or []
    )

    for ritual in rituals:

        if not ritual_is_for_date(
            ritual,
            previous_date
        ):
            continue

        if ritual_was_completed(
            ritual,
            previous_date
        ):
            continue

        penalty = calculate_penalty(
            ritual
        )

        spheres = get_spheres(
            ritual
        )

        subtract_xp(
            player,
            penalty,
            spheres
        )

        if spheres:

            share = (
                penalty
                / len(spheres)
            )

            for sphere in spheres:

                if sphere in penalties_by_sphere:

                    penalties_by_sphere[
                        sphere
                    ] += share

        missed_activities.append(
            (
                "🔄",
                get_title(ritual),
                penalty
            )
        )

    # =====================================================
    # ОНОВЛЮЄМО ДАТУ ОСТАННЬОГО ПІДСУМКУ
    # =====================================================

    statistics = (
        player.get(
            "statistics"
        ) or {}
    )

    statistics[
        "last_summary_date"
    ] = current_date.isoformat()

    player["statistics"] = (
        statistics
    )

    # =====================================================
    # ЗБЕРІГАЄМО ВСІ ЗМІНИ
    # =====================================================

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

            "plants": player[
                "plants"
            ],

            "statistics": player[
                "statistics"
            ]
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
                f"🌱 {title} "
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

        for icon, title, penalty in missed_activities:

            text += (
                f"{icon} {title} "
                f"−{penalty:.1f} XP\n"
            )

        text += "\n"

    # =====================================================
    # СФЕРИ
    # =====================================================

    text += (
        "🎯 <b>Рух сфер</b>\n\n"
    )

    sphere_activity = False

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

        sphere_activity = True

        text += (
            f"{emoji} "
            f"+{earned:.1f} / "
            f"−{penalty:.1f} XP\n"
        )

    if not sphere_activity:

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
        f"<b>{format_date(current_date)}, "
        f"{WEEKDAYS[current_date.weekday()]}</b>\n\n"
    )

    agenda = []

    for scroll in player.get(
        "scrolls"
    ) or []:

        title = get_title(
            scroll
        )

        xp = get_xp(
            scroll
        )

        deadline = parse_date(
            scroll.get(
                "deadline"
            )
        )

        icon = "🔥" if (
            deadline == current_date
        ) else "📜"

        agenda.append(
            f"{icon} <b>{title}</b> "
            f"({xp:.1f} XP)"
        )

    for ritual in player.get(
        "rituals"
    ) or []:

        if ritual_is_for_date(
            ritual,
            current_date
        ):

            agenda.append(
                f"🔄 <b>{get_title(ritual)}</b> "
                f"({get_xp(ritual):.1f} XP)"
            )

    for plant in player.get(
        "plants"
    ) or []:

        title = get_title(
            plant
        )

        xp = get_xp(
            plant
        )

        deadline = parse_date(
            plant.get(
                "deadline"
            )
        )

        icon = "🔥" if (
            deadline == current_date
        ) else "🌱"

        agenda.append(
            f"{icon} <b>{title}</b> "
            f"({xp:.1f} XP)"
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


# =========================================================
# НАДСИЛАННЯ ПІДСУМКІВ УСІМ ГРАВЦЯМ
# =========================================================

def send_daily_summaries():

    print(
        "🌅 Починаю формування "
        "щоденних підсумків..."
    )

    players = get_all_players()

    if not players:

        print(
            "ℹ️ Гравців для підсумку немає."
        )

        return

    sent = 0
    skipped = 0
    errors = 0

    for player_record in players:

        user_id = player_record.get(
            "user_id"
        )

        if not user_id:
            continue

        try:

            text = make_player_summary(
                user_id
            )

            if text is None:

                skipped += 1

                continue

            bot.send_message(
                int(user_id),
                text,
                parse_mode="HTML"
            )

            sent += 1

        except Exception as error:

            errors += 1

            print(
                f"❌ Не вдалося надіслати "
                f"підсумок {user_id}: "
                f"{error}"
            )

    print(
        "🌅 Підсумки завершено. "
        f"Надіслано: {sent}; "
        f"пропущено: {skipped}; "
        f"помилок: {errors}."
    )
