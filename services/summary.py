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
    Доба Грінвуду починається о 07:00 за Києвом.

    06:59  -> ще попередня доба
    07:00  -> вже нова доба
    """

    if dt is None:
        dt = datetime.now(KYIV)

    if dt.hour < 7:
        dt = dt - timedelta(days=1)

    return dt.date()


def format_date(date):
    return date.strftime("%d.%m.%Y")


# =========================================================
# ЗАГАЛЬНІ ФУНКЦІЇ
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
    Підтримує формати:

    ["health", "art"]

    ["💪", "🎨"]

    [{"key": "health", "emoji": "💪"}]

    [{"emoji": "💪"}]
    """

    spheres = item.get("spheres")

    if not spheres:
        spheres = item.get("sphere")

    if not spheres:
        return []

    # -----------------------------------------------------
    # Рядок
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

                for sphere_key, sphere_emoji in SPHERE_NAMES.items():

                    if emoji == sphere_emoji:
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


def sphere_emoji(sphere):
    return SPHERE_NAMES.get(
        sphere,
        sphere
    )


# =========================================================
# ДАТА ДЕДЛАЙНУ
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
# ШТРАФ
# =========================================================

def calculate_penalty(xp):
    """
    Штраф за прострочене завдання:
    2/3 від початкової нагороди.
    """

    return xp * (2 / 3)


def subtract_total_xp(player, xp):

    current = float(
        player.get(
            "xp_total",
            0
        )
    )

    player["xp_total"] = max(
        0,
        current - xp
    )


def subtract_xp_from_spheres(
    player,
    spheres,
    total_xp
):

    if not spheres or total_xp <= 0:
        return

    player_spheres = player.get(
        "spheres"
    ) or {}

    share = total_xp / len(spheres)

    for sphere in spheres:

        if sphere not in player_spheres:
            continue

        current = float(
            player_spheres[sphere].get(
                "xp",
                0
            )
        )

        player_spheres[sphere]["xp"] = max(
            0,
            current - share
        )


# =========================================================
# СИСТЕМА ЗАПОБІГАННЯ ПОВТОРНОМУ ШТРАФУ
# =========================================================

def get_penalized_items(player):

    statistics = player.get(
        "statistics"
    ) or {}

    penalized = statistics.get(
        "penalized_items"
    )

    if not isinstance(
        penalized,
        list
    ):
        penalized = []

    return penalized


def make_item_identifier(
    item,
    item_type
):

    """
    Створює стабільний ідентифікатор
    для простроченого завдання.

    Це потрібно, щоб один і той самий
    сувій / ритуал / рослина не штрафувався
    щоранку повторно.
    """

    title = get_title(item)
    xp = get_xp(item)

    deadline = (
        item.get("deadline")
        or item.get("date")
        or ""
    )

    created_at = item.get(
        "created_at",
        ""
    )

    return (
        f"{item_type}|"
        f"{title}|"
        f"{xp}|"
        f"{deadline}|"
        f"{created_at}"
    )


def mark_item_penalized(
    player,
    identifier
):

    statistics = player.get(
        "statistics"
    ) or {}

    penalized = get_penalized_items(
        player
    )

    if identifier not in penalized:

        penalized.append(
            identifier
        )

    statistics[
        "penalized_items"
    ] = penalized

    player[
        "statistics"
    ] = statistics


# =========================================================
# ІСТОРІЯ ВИКОНАНИХ СПРАВ
# =========================================================

def get_completed_history(player):

    """
    completed_history є ОКРЕМОЮ колонкою Supabase.

    НЕ беремо її з statistics.
    """

    history = player.get(
        "completed_history"
    )

    if not isinstance(
        history,
        list
    ):
        history = []

    return history


# =========================================================
# ВИТЯГУВАННЯ ВИКОНАНИХ СПРАВ
# =========================================================

def get_completed_for_date(
    player,
    target_date
):

    """
    Шукає виконані справи за greenwood_date.

    Також підтримує completed_date
    у форматі DD.MM.YYYY.
    """

    history = get_completed_history(
        player
    )

    result = []

    target_iso = target_date.isoformat()
    target_normal = target_date.strftime(
        "%d.%m.%Y"
    )

    for entry in history:

        greenwood_date = entry.get(
            "greenwood_date"
        )

        completed_date = entry.get(
            "completed_date"
        )

        if (
            greenwood_date == target_iso
            or completed_date == target_normal
        ):

            result.append(
                entry
            )

    return result


# =========================================================
# АРХІВИ
# =========================================================

def get_scroll_archive(player):

    archive = player.get(
        "scroll_archive"
    )

    if not isinstance(
        archive,
        list
    ):
        return []

    return archive


def get_ritual_archive(player):

    archive = player.get(
        "ritual_archive"
    )

    if not isinstance(
        archive,
        list
    ):
        return []

    return archive


# =========================================================
# ОБ'ЄДНЕННЯ ВИКОНАНИХ СПРАВ
# =========================================================

def get_completed_activities(
    player,
    target_date
):

    """
    Основне джерело:
        completed_history

    Додатково підтримує:
        scroll_archive
        ritual_archive

    Це зроблено для сумісності з уже існуючими
    записами Supabase.
    """

    result = []

    # -----------------------------------------------------
    # completed_history
    # -----------------------------------------------------

    history = get_completed_for_date(
        player,
        target_date
    )

    for entry in history:

        result.append(
            entry
        )

    # -----------------------------------------------------
    # scroll_archive
    # -----------------------------------------------------

    for scroll in get_scroll_archive(
        player
    ):

        completed_date = scroll.get(
            "completed_date"
        )

        if completed_date == target_date.strftime(
            "%d.%m.%Y"
        ):

            entry = dict(scroll)

            entry["type"] = "scroll"

            result.append(
                entry
            )

    # -----------------------------------------------------
    # ritual_archive
    # -----------------------------------------------------

    for ritual in get_ritual_archive(
        player
    ):

        completed_date = ritual.get(
            "completed_date"
        )

        if completed_date == target_date.strftime(
            "%d.%m.%Y"
        ):

            entry = dict(ritual)

            entry["type"] = "ritual"

            result.append(
                entry
            )

    return result


# =========================================================
# ТИП ВИКОНАНОЇ СПРАВИ
# =========================================================

def detect_activity_type(entry):

    entry_type = (
        entry.get("type")
        or entry.get("activity_type")
        or entry.get("quest_type")
    )

    if entry_type:
        entry_type = str(
            entry_type
        ).lower()

        if entry_type in (
            "scroll",
            "suvoy",
            "сувій"
        ):
            return "scroll"

        if entry_type in (
            "ritual",
            "ритуал"
        ):
            return "ritual"

        if entry_type in (
            "plant",
            "plant_archive",
            "рослина"
        ):
            return "plant"

    # -----------------------------------------------------
    # Якщо тип не записаний
    # -----------------------------------------------------

    if "reward" in entry:
        return "plant"

    return "unknown"


# =========================================================
# РИТУАЛ НА ПЕВНУ ДАТУ
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

    weekday_number = target_date.weekday()

    if weekday_number in days:
        return True

    weekday_name = WEEKDAYS[
        weekday_number
    ]

    if weekday_name in days:
        return True

    return False


# =========================================================
# ПРОПУЩЕНІ ЗАВДАННЯ
# =========================================================

def process_missed_activity(
    player,
    item,
    item_type,
    current_greenwood_date,
    missed_activities,
    penalties_by_sphere
):

    identifier = make_item_identifier(
        item,
        item_type
    )

    penalized_items = get_penalized_items(
        player
    )

    # -----------------------------------------------------
    # Уже штрафували
    # -----------------------------------------------------

    if identifier in penalized_items:
        return

    xp = get_xp(item)

    if xp <= 0:
        return

    penalty = calculate_penalty(
        xp
    )

    spheres = get_spheres(
        item
    )

    # -----------------------------------------------------
    # Знімаємо загальний XP
    # -----------------------------------------------------

    subtract_total_xp(
        player,
        penalty
    )

    # -----------------------------------------------------
    # Знімаємо XP зі сфер
    # -----------------------------------------------------

    subtract_xp_from_spheres(
        player,
        spheres,
        penalty
    )

    # -----------------------------------------------------
    # Записуємо штраф по сферах
    # -----------------------------------------------------

    if spheres:

        share = (
            penalty / len(spheres)
        )

        for sphere in spheres:

            if sphere in penalties_by_sphere:

                penalties_by_sphere[
                    sphere
                ] += share

    # -----------------------------------------------------
    # Запам'ятовуємо штраф
    # -----------------------------------------------------

    mark_item_penalized(
        player,
        identifier
    )

    missed_activities.append(
        {
            "type": item_type,
            "title": get_title(item),
            "xp": xp,
            "penalty": penalty
        }
    )


# =========================================================
# ПЕРЕВІРКА ПРОСТРОЧЕНИХ СПРАВ
# =========================================================

def process_missed_activities(
    player,
    current_greenwood_date,
    penalties_by_sphere
):

    missed_activities = []

    # =====================================================
    # СУВОЇ
    # =====================================================

    scrolls = player.get(
        "scrolls"
    ) or []

    for scroll in scrolls:

        deadline = parse_deadline(
            scroll.get("deadline")
            or scroll.get("date")
        )

        if not deadline:
            continue

        if deadline < current_greenwood_date:

            process_missed_activity(
                player,
                scroll,
                "scroll",
                current_greenwood_date,
                missed_activities,
                penalties_by_sphere
            )

    # =====================================================
    # РИТУАЛИ
    # =====================================================

    rituals = player.get(
        "rituals"
    ) or []

    previous_date = (
        current_greenwood_date
        - timedelta(days=1)
    )

    for ritual in rituals:

        if not ritual_is_for_date(
            ritual,
            previous_date
        ):
            continue

        last_completed = ritual.get(
            "last_completed"
        )

        previous_normal = (
            previous_date.strftime(
                "%d.%m.%Y"
            )
        )

        previous_iso = (
            previous_date.isoformat()
        )

        if last_completed in (
            previous_normal,
            previous_iso
        ):
            continue

        process_missed_activity(
            player,
            ritual,
            "ritual",
            current_greenwood_date,
            missed_activities,
            penalties_by_sphere
        )

    # =====================================================
    # РОСЛИНИ
    # =====================================================

    plants = player.get(
        "plants"
    ) or []

    for plant in plants:

        deadline = parse_deadline(
            plant.get("deadline")
        )

        if not deadline:
            continue

        if deadline < current_greenwood_date:

            process_missed_activity(
                player,
                plant,
                "plant",
                current_greenwood_date,
                missed_activities,
                penalties_by_sphere
            )

    return missed_activities


# =========================================================
# ПОРЯДОК ДЕННИЙ
# =========================================================

def build_agenda(
    player,
    target_date
):

    lines = []

    # -----------------------------------------------------
    # СУВОЇ
    # -----------------------------------------------------

    scrolls = player.get(
        "scrolls"
    ) or []

    for scroll in scrolls:

        title = get_title(
            scroll
        )

        xp = get_xp(
            scroll
        )

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

    rituals = player.get(
        "rituals"
    ) or []

    for ritual in rituals:

        if not ritual_is_for_date(
            ritual,
            target_date
        ):
            continue

        title = get_title(
            ritual
        )

        xp = get_xp(
            ritual
        )

        lines.append(
            f"🔄 <b>{title}</b> "
            f"({xp:.1f} XP)"
        )

    # -----------------------------------------------------
    # РОСЛИНИ
    # -----------------------------------------------------

    plants = player.get(
        "plants"
    ) or []

    for plant in plants:

        title = get_title(
            plant
        )

        xp = get_xp(
            plant
        )

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
# ОНОВЛЕННЯ STATISTICS
# =========================================================

def update_statistics(
    player,
    current_greenwood_date
):

    """
    statistics використовується тільки
    для службової статистики.

    completed_history сюди НЕ записуємо.
    """

    statistics = player.get(
        "statistics"
    ) or {}

    statistics[
        "last_summary_date"
    ] = current_greenwood_date.isoformat()

    # Якщо цих значень немає,
    # створюємо їх без руйнування старої статистики.

    statistics.setdefault(
        "plants_harvested",
        0
    )

    statistics.setdefault(
        "completed_rituals",
        0
    )

    statistics.setdefault(
        "completed_scrolls",
        0
    )

    statistics.setdefault(
        "expeditions_completed",
        0
    )

    player[
        "statistics"
    ] = statistics


# =========================================================
# ФОРМУВАННЯ ПІДСУМКУ ОДНОГО ГРАВЦЯ
# =========================================================

def make_player_summary(user_id):

    player = get_player(
        user_id
    )

    now = datetime.now(
        KYIV
    )

    current_greenwood_date = (
        get_greenwood_date(
            now
        )
    )

    previous_date = (
        current_greenwood_date
        - timedelta(days=1)
    )

    # =====================================================
    # ВИКОНАНІ СПРАВИ
    # =====================================================

    completed = get_completed_activities(
        player,
        previous_date
    )

    completed_scrolls = []
    completed_rituals = []
    completed_plants = []

    earned_by_sphere = {
        key: 0.0
        for key in SPHERE_NAMES
    }

    for entry in completed:

        entry_type = detect_activity_type(
            entry
        )

        title = get_title(
            entry
        )

        xp = get_xp(
            entry
        )

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
        # Категорії
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
    # ПРОПУЩЕНІ
    # =====================================================

    penalties_by_sphere = {
        key: 0.0
        for key in SPHERE_NAMES
    }

    missed_activities = (
        process_missed_activities(
            player,
            current_greenwood_date,
            penalties_by_sphere
        )
    )

    # =====================================================
    # ОНОВЛЮЄМО STATISTICS
    # =====================================================

    update_statistics(
        player,
        current_greenwood_date
    )

    # =====================================================
    # ЗБЕРІГАЄМО ВСІ ПОТРІБНІ КОЛОНКИ
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
        "⚠️ <b>Пропущено за дедлайном</b>\n\n"
    )

    if not missed_activities:

        text += (
            "Нічого не пропущено. 🌿\n\n"
        )

    else:

        for activity in missed_activities:

            icon = {
                "scroll": "📜",
                "ritual": "🔄",
                "plant": "🌳"
            }.get(
                activity["type"],
                "❌"
            )

            text += (
                f"{icon} <b>{activity['title']}</b>\n"
                f"   −{activity['penalty']:.1f} XP\n"
            )

        text += "\n"

    # =====================================================
    # РУХ СФЕР
    # =====================================================

    text += (
        "🎯 <b>Рух сфер</b>\n\n"
    )

    any_activity = False

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

        any_activity = True

        text += (
            f"{emoji} "
            f"нараховано: <b>+{earned:.1f}</b> XP"
        )

        if penalty > 0:

            text += (
                f" | стягнуто: "
                f"<b>−{penalty:.1f}</b> XP"
            )

        text += "\n"

    if not any_activity:

        text += (
            "Сфери сьогодні не змінювалися.\n"
        )

    text += "\n"

    # =====================================================
    # ПІДСУМОК XP
    # =====================================================

    total_earned = sum(
        earned_by_sphere.values()
    )

    total_penalty = sum(
        penalties_by_sphere.values()
    )

    text += (
        "📊 <b>Загальний рух</b>\n\n"
        f"✨ Нараховано: <b>+{total_earned:.1f} XP</b>\n"
        f"⚠️ Стягнуто: <b>−{total_penalty:.1f} XP</b>\n\n"
    )

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
# НАДСИЛАННЯ ЩОДЕННИХ ПІДСУМКІВ
# =========================================================

def send_daily_summaries():

    """
    Формує та надсилає ранковий підсумок
    кожному гравцеві.

    Викликається scheduler.py о 07:00
    за київським часом.
    """

    from services.database import get_all_players

    print(
        "🌅 Починаю формування щоденних підсумків..."
    )

    players = get_all_players()

    if not players:

        print(
            "🌲 Гравців для підсумку не знайдено."
        )

        return

    sent = 0
    failed = 0

    # Імпортуємо bot тут, а не на початку,
    # щоб уникнути циклічних імпортів.

    from services.config import bot

    for player in players:

        try:

            user_id = str(
                player.get(
                    "user_id"
                )
            )

            if not user_id:
                continue

            text = make_player_summary(
                user_id
            )

            bot.send_message(
                int(user_id),
                text,
                parse_mode="HTML"
            )

            sent += 1

            print(
                f"✅ Підсумок відправлено "
                f"user_id={user_id}"
            )

        except Exception as error:

            failed += 1

            print(
                f"❌ Не вдалося відправити "
                f"підсумок user_id="
                f"{player.get('user_id')}: "
                f"{error}"
            )

    print(
        f"🌅 Підсумки завершено. "
        f"Відправлено: {sent}, "
        f"помилок: {failed}"
    )
