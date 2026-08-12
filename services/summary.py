from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from services.config import bot, supabase
from services.database import get_player, update_player


print("📖 Завантажено систему ранкових хронік Грінвуду...")


# =========================================================
# НАЛАШТУВАННЯ
# =========================================================

KYIV = ZoneInfo("Europe/Kyiv")

SUMMARY_HOUR = 7


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
    """
    Доба Грінвуду починається о 07:00 за Києвом.

    Наприклад:

    06:30 12.08 → ще доба 11.08
    07:00 12.08 → вже доба 12.08
    """

    if dt is None:
        dt = datetime.now(KYIV)

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=KYIV)

    if dt.hour < SUMMARY_HOUR:
        dt = dt - timedelta(days=1)

    return dt.date()


def format_date(date):
    return date.strftime("%d.%m.%Y")


# =========================================================
# ЗАГАЛЬНІ ДОПОМІЖНІ ФУНКЦІЇ
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
# СФЕРИ
# =========================================================

def get_spheres(item):
    """
    Повертає ключі сфер:

    ["health", "art", "relations"]

    Підтримує:
    - health
    - 💪
    - список
    - рядок
    - старі формати записів
    """

    spheres = item.get("spheres")

    if not spheres:
        spheres = item.get("sphere")

    if not spheres:
        return []

    result = []

    # -----------------------------------------------------
    # Рядок
    # -----------------------------------------------------

    if isinstance(spheres, str):

        for key, emoji in SPHERE_NAMES.items():

            if key in spheres or emoji in spheres:

                if key not in result:
                    result.append(key)

        return result

    # -----------------------------------------------------
    # Список
    # -----------------------------------------------------

    if isinstance(spheres, list):

        for sphere in spheres:

            if isinstance(sphere, dict):

                key = sphere.get("key")

                if key in SPHERE_NAMES:
                    if key not in result:
                        result.append(key)
                    continue

                emoji = sphere.get("emoji")

                for sphere_key, sphere_emoji in SPHERE_NAMES.items():

                    if emoji == sphere_emoji:

                        if sphere_key not in result:
                            result.append(sphere_key)

                        break

            else:

                if sphere in SPHERE_NAMES:

                    if sphere not in result:
                        result.append(sphere)

                elif sphere in SPHERE_NAMES.values():

                    for key, emoji in SPHERE_NAMES.items():

                        if sphere == emoji:

                            if key not in result:
                                result.append(key)

                            break

        return result

    return []


def sphere_emoji(sphere):
    return SPHERE_NAMES.get(
        sphere,
        sphere
    )


# =========================================================
# XP
# =========================================================

def subtract_total_xp(player, xp):
    """
    Віднімає XP із загального XP персонажа.
    """

    current = float(
        player.get("xp_total", 0)
    )

    player["xp_total"] = max(
        0.0,
        current - xp
    )


def subtract_xp_from_spheres(
    player,
    spheres,
    total_xp
):
    """
    Віднімає штраф XP рівномірно
    між усіма сферами справи.
    """

    if not spheres:
        return

    if total_xp <= 0:
        return

    player_spheres = (
        player.get("spheres")
        or {}
    )

    share = (
        total_xp / len(spheres)
    )

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
            0.0,
            current_xp - share
        )


def calculate_penalty(xp):
    """
    Штраф за пропущену справу:
    2/3 від її початкової нагороди.
    """

    return xp * (2 / 3)


# =========================================================
# ДАТИ DEADLINE
# =========================================================

def parse_deadline(value):
    """
    Підтримує:

    25.08.26
    25.08.2026
    """

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
# РИТУАЛИ
# =========================================================

def ritual_is_for_date(
    ritual,
    target_date
):
    """
    Перевіряє, чи мав ритуал виконуватися
    у конкретну дату.
    """

    if ritual.get("daily") is True:
        return True

    days = ritual.get("days") or []

    if not isinstance(days, list):
        return False

    weekday_number = target_date.weekday()

    if weekday_number in days:
        return True

    weekday_name = WEEKDAYS[
        weekday_number
    ]

    if weekday_name in days:
        return True

    return False


def ritual_was_completed_on_date(
    ritual,
    target_date
):
    """
    Перевіряє last_completed ритуалу.
    """

    completed = ritual.get(
        "last_completed"
    )

    if not completed:
        return False

    if completed == target_date.isoformat():
        return True

    if completed == target_date.strftime(
        "%d.%m.%Y"
    ):
        return True

    return False


# =========================================================
# ОТРИМАННЯ ВИКОНАНИХ СПРАВ З АРХІВУ
# =========================================================

def get_archive_entries_for_date(
    archive,
    target_date
):
    """
    Повертає записи архіву,
    виконані в конкретну дату.

    Основний формат:

    completed_date:
        09.08.2026

    Також підтримує ISO:
        2026-08-09
    """

    if not isinstance(archive, list):
        return []

    result = []

    formatted = target_date.strftime(
        "%d.%m.%Y"
    )

    iso = target_date.isoformat()

    for entry in archive:

        completed_date = entry.get(
            "completed_date"
        )

        if completed_date in (
            formatted,
            iso
        ):

            result.append(entry)

    return result


# =========================================================
# ПОБУДОВА ПОРЯДКУ ДЕННОГО
# =========================================================

def build_agenda(
    player,
    target_date
):
    """
    Формує список справ,
    які актуальні сьогодні.
    """

    scrolls = (
        player.get("scrolls")
        or []
    )

    rituals = (
        player.get("rituals")
        or []
    )

    plants = (
        player.get("plants")
        or []
    )

    lines = []

    # =====================================================
    # СУВОЇ
    # =====================================================

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

        deadline = parse_deadline(
            plant.get("deadline")
        )

        if deadline == target_date:

            icon = "🔥"

        else:

            icon = "🌱"

        lines.append(
            f"{icon} <b>{title}</b> "
            f"({xp:.1f} XP)"
        )

    return lines


# =========================================================
# ОНОВЛЕННЯ СТАТИСТИКИ
# =========================================================

def update_statistics(
    player,
    completed_scrolls,
    completed_rituals,
    completed_plants,
    summary_date
):
    """
    Оновлює statistics.

    completed_history НЕ використовується
    як джерело даних.

    Він залишається в statistics лише
    для сумісності зі структурою Supabase.
    """

    statistics = (
        player.get("statistics")
        or {}
    )

    statistics.setdefault(
        "completed_scrolls",
        0
    )

    statistics.setdefault(
        "completed_rituals",
        0
    )

    statistics.setdefault(
        "plants_harvested",
        0
    )

    statistics.setdefault(
        "expeditions_completed",
        0
    )

    statistics.setdefault(
        "completed_history",
        []
    )

    statistics["completed_scrolls"] = (
        len(
            player.get(
                "scroll_archive",
                []
            )
        )
    )

    statistics["completed_rituals"] = (
        len(
            player.get(
                "ritual_archive",
                []
            )
        )
    )

    statistics["plants_harvested"] = (
        len(
            player.get(
                "plant_archive",
                []
            )
        )
    )

    statistics["last_summary_date"] = (
        summary_date.isoformat()
    )

    player["statistics"] = statistics


# =========================================================
# ПІДСУМОК ОДНОГО ГРАВЦЯ
# =========================================================

def make_player_summary(user_id):
    """
    Створює ранковий підсумок
    конкретного користувача.

    user_id є єдиним ідентифікатором,
    за яким шукаються його дані.
    """

    user_id = str(user_id)

    player = get_player(
        user_id
    )

    now = datetime.now(KYIV)

    current_greenwood_date = (
        get_greenwood_date(now)
    )

    previous_date = (
        current_greenwood_date
        - timedelta(days=1)
    )

    # =====================================================
    # ЗАХИСТ ВІД ПОВТОРНОГО ПІДСУМКУ
    # =====================================================

    statistics = (
        player.get("statistics")
        or {}
    )

    last_summary = statistics.get(
        "last_summary_date"
    )

    if last_summary == (
        current_greenwood_date.isoformat()
    ):

        return None

    # =====================================================
    # АРХІВИ
    # =====================================================

    scroll_archive = (
        player.get("scroll_archive")
        or []
    )

    ritual_archive = (
        player.get("ritual_archive")
        or []
    )

    plant_archive = (
        player.get("plant_archive")
        or []
    )

    # =====================================================
    # ВИКОНАНІ СПРАВИ
    # =====================================================

    completed_scrolls = (
        get_archive_entries_for_date(
            scroll_archive,
            previous_date
        )
    )

    completed_rituals = (
        get_archive_entries_for_date(
            ritual_archive,
            previous_date
        )
    )

    completed_plants = (
        get_archive_entries_for_date(
            plant_archive,
            previous_date
        )
    )

    # =====================================================
    # XP ПО СФЕРАХ
    # =====================================================

    earned_by_sphere = {
        key: 0.0
        for key in SPHERE_NAMES
    }

    penalties_by_sphere = {
        key: 0.0
        for key in SPHERE_NAMES
    }

    # -----------------------------------------------------
    # Виконані сувої
    # -----------------------------------------------------

    for entry in completed_scrolls:

        xp = get_xp(entry)

        spheres = get_spheres(
            entry
        )

        if not spheres:
            continue

        share = (
            xp / len(spheres)
        )

        for sphere in spheres:

            if sphere in earned_by_sphere:

                earned_by_sphere[
                    sphere
                ] += share

    # -----------------------------------------------------
    # Виконані ритуали
    # -----------------------------------------------------

    for entry in completed_rituals:

        xp = get_xp(entry)

        spheres = get_spheres(
            entry
        )

        if not spheres:
            continue

        share = (
            xp / len(spheres)
        )

        for sphere in spheres:

            if sphere in earned_by_sphere:

                earned_by_sphere[
                    sphere
                ] += share

    # -----------------------------------------------------
    # Виконані рослини
    # -----------------------------------------------------

    for entry in completed_plants:

        xp = get_xp(entry)

        spheres = get_spheres(
            entry
        )

        if not spheres:
            continue

        share = (
            xp / len(spheres)
        )

        for sphere in spheres:

            if sphere in earned_by_sphere:

                earned_by_sphere[
                    sphere
                ] += share

    # =====================================================
    # ПРОПУЩЕНІ СУВОЇ
    # =====================================================

    scrolls = (
        player.get("scrolls")
        or []
    )

    remaining_scrolls = []

    missed_activities = []

    for scroll in scrolls:

        deadline = parse_deadline(
            scroll.get("deadline")
            or scroll.get("date")
        )

        if deadline is None:

            remaining_scrolls.append(
                scroll
            )

            continue

        # -------------------------------------------------
        # Дедлайн минув
        # -------------------------------------------------

        if deadline < current_greenwood_date:

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

            if spheres:

                share = (
                    penalty / len(spheres)
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

            # Сувій після дедлайну
            # більше не є активним.
            continue

        remaining_scrolls.append(
            scroll
        )

    player["scrolls"] = (
        remaining_scrolls
    )

    # =====================================================
    # ПРОПУЩЕНІ РОСЛИНИ
    # =====================================================

    plants = (
        player.get("plants")
        or []
    )

    for plant in plants:

        deadline = parse_deadline(
            plant.get("deadline")
        )

        if deadline is None:
            continue

        if deadline >= current_greenwood_date:
            continue

        # -------------------------------------------------
        # Рослина вже отримала штраф
        # -------------------------------------------------

        if plant.get(
            "penalty_applied"
        ) is True:

            continue

        xp = get_xp(plant)

        penalty = calculate_penalty(
            xp
        )

        spheres = get_spheres(
            plant
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

        if spheres:

            share = (
                penalty / len(spheres)
            )

            for sphere in spheres:

                if sphere in penalties_by_sphere:

                    penalties_by_sphere[
                        sphere
                    ] += share

        missed_activities.append(
            (
                get_title(plant),
                penalty
            )
        )

        # -------------------------------------------------
        # Фіксуємо, що штраф уже був
        # -------------------------------------------------

        plant["penalty_applied"] = True

    player["plants"] = plants

    # =====================================================
    # ПРОПУЩЕНІ РИТУАЛИ
    # =====================================================

    rituals = (
        player.get("rituals")
        or []
    )

    for ritual in rituals:

        if not ritual_is_for_date(
            ritual,
            previous_date
        ):

            continue

        if ritual_was_completed_on_date(
            ritual,
            previous_date
        ):

            continue

        xp = get_xp(ritual)

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

        if spheres:

            share = (
                penalty / len(spheres)
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

    player["rituals"] = rituals

    # =====================================================
    # СТАТИСТИКА
    # =====================================================

    update_statistics(
        player,
        completed_scrolls,
        completed_rituals,
        completed_plants,
        current_greenwood_date
    )

    # =====================================================
    # ЗБЕРЕЖЕННЯ ДАНИХ
    # =====================================================

    update_player(
        user_id,
        {
            "xp_total": player.get(
                "xp_total",
                0
            ),

            "spheres": player.get(
                "spheres",
                {}
            ),

            "scrolls": player.get(
                "scrolls",
                []
            ),

            "rituals": player.get(
                "rituals",
                []
            ),

            "plants": player.get(
                "plants",
                []
            ),

            "statistics": player.get(
                "statistics",
                {}
            )
        }
    )

    # =====================================================
    # ТЕКСТ
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

        for scroll in completed_scrolls:

            title = get_title(scroll)
            xp = get_xp(scroll)

            text += (
                f"📜 {title} "
                f"✨ +{xp:.1f} XP\n"
            )

        for ritual in completed_rituals:

            title = get_title(ritual)
            xp = get_xp(ritual)

            text += (
                f"🔄 {title} "
                f"✨ +{xp:.1f} XP\n"
            )

        for plant in completed_plants:

            title = get_title(plant)
            xp = get_xp(plant)

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

        for title, penalty in missed_activities:

            text += (
                f"❌ {title} "
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

    for sphere in SPHERE_NAMES:

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

        emoji = sphere_emoji(
            sphere
        )

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


# =========================================================
# ОТРИМАТИ ВСІХ ГРАВЦІВ
# =========================================================

def get_all_user_ids():
    """
    Отримує user_id усіх гравців
    безпосередньо з таблиці players.

    Підсумок кожному надсилається
    тільки за його власним user_id.
    """

    try:

        response = (
            supabase
            .table("players")
            .select("user_id")
            .execute()
        )

        if not response.data:
            return []

        return [
            str(row["user_id"])
            for row in response.data
            if row.get("user_id") is not None
        ]

    except Exception as error:

        print(
            "❌ Не вдалося отримати список "
            f"гравців: {error}"
        )

        return []


# =========================================================
# НАДСИЛАННЯ ЩОДЕННИХ ПІДСУМКІВ
# =========================================================

def send_daily_summaries():
    """
    Формує та надсилає ранковий підсумок
    кожному користувачу.

    Викликається scheduler.py о 07:00.
    """

    print(
        "🌅 Починаю формування "
        "щоденних підсумків..."
    )

    user_ids = get_all_user_ids()

    if not user_ids:

        print(
            "ℹ️ У таблиці players "
            "немає користувачів."
        )

        return

    sent = 0
    skipped = 0
    errors = 0

    for user_id in user_ids:

        try:

            summary = make_player_summary(
                user_id
            )

            # -------------------------------------------------
            # Якщо підсумок уже був сформований
            # -------------------------------------------------

            if summary is None:

                print(
                    f"⏭️ Підсумок для {user_id} "
                    "вже сформований."
                )

                skipped += 1
                continue

            # -------------------------------------------------
            # Надсилання саме цьому user_id
            # -------------------------------------------------

            bot.send_message(
                int(user_id),
                summary,
                parse_mode="HTML"
            )

            sent += 1

            print(
                f"✅ Підсумок надіслано "
                f"user_id={user_id}"
            )

        except Exception as error:

            errors += 1

            print(
                f"❌ Помилка підсумку "
                f"user_id={user_id}: {error}"
            )

    print(
        "🌅 Підсумки завершено. "
        f"Надіслано: {sent}, "
        f"пропущено: {skipped}, "
        f"помилок: {errors}"
    )
