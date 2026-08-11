from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from services.database import get_player, update_player
from services.config import supabase, bot


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

    Наприклад:

    06:30 11.08 → ще доба 10.08
    07:00 11.08 → вже доба 11.08
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


def parse_date(value):
    """
    Підтримує:
    DD.MM.YY
    DD.MM.YYYY
    ISO datetime
    """

    if not value:
        return None

    if hasattr(value, "date"):
        try:
            return value.date()
        except Exception:
            pass

    value = str(value).strip()

    formats = [
        "%d.%m.%y",
        "%d.%m.%Y",
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f"
    ]

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue

    return None


# =========================================================
# СФЕРИ
# =========================================================

def normalize_spheres(item):
    """
    Повертає сфери у вигляді ключів:

    ["health", "art", "relations"]

    Підтримує:
    - health
    - 💪
    - список
    - старі формати
    """

    spheres = item.get("spheres")

    if not spheres:
        spheres = item.get("sphere")

    if not spheres:
        return []

    if isinstance(spheres, str):

        result = []

        for key, emoji in SPHERE_NAMES.items():

            if key in spheres:
                result.append(key)

            elif emoji in spheres:
                result.append(key)

        return list(dict.fromkeys(result))

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

                continue

            if sphere in SPHERE_NAMES:

                result.append(sphere)
                continue

            for key, emoji in SPHERE_NAMES.items():

                if sphere == emoji:
                    result.append(key)
                    break

        return list(dict.fromkeys(result))

    return []


# =========================================================
# ІСТОРІЯ
# =========================================================

def get_completed_history(player):
    """
    completed_history є ОКРЕМОЮ колонкою Supabase.

    Не беремо її з statistics.
    """

    history = player.get("completed_history")

    if not isinstance(history, list):
        return []

    return history


def save_completed_history(player, history):
    player["completed_history"] = history


# =========================================================
# ПЕРЕВІРКА ЧИ ШТРАФ ВЖЕ НАКЛАДАВСЯ
# =========================================================

def penalty_already_applied(
    history,
    activity_type,
    title,
    deadline
):
    """
    Не дозволяє стягувати один і той самий штраф
    повторно кожного ранку.

    Для ідентифікації використовуємо:
    тип + назву + дедлайн.
    """

    for entry in history:

        if entry.get("type") != "penalty":
            continue

        if entry.get("activity_type") != activity_type:
            continue

        if entry.get("title") != title:
            continue

        if entry.get("deadline") != deadline:
            continue

        return True

    return False


# =========================================================
# ШТРАФ
# =========================================================

def calculate_penalty(xp):
    """
    За пропущену справу стягується 2/3
    від зазначеної при створенні нагороди.
    """

    return xp * (2 / 3)


def subtract_total_xp(player, xp):

    current = float(
        player.get("xp_total", 0)
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
    """
    Віднімає штраф із сфер.

    Якщо:
        12 XP штрафу
        3 сфери

    то:
        -4 XP з кожної.
    """

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


# =========================================================
# РИТУАЛИ
# =========================================================

def ritual_is_for_date(
    ritual,
    target_date
):
    """
    Перевіряє, чи мав ритуал виконуватися
    у конкретну добу.
    """

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


def ritual_was_completed(
    ritual,
    target_date
):
    """
    Перевіряє last_completed.

    complete_activity.py записує дату
    у форматі DD.MM.YYYY.
    """

    last_completed = ritual.get(
        "last_completed"
    )

    if not last_completed:
        return False

    completed_date = parse_date(
        last_completed
    )

    return completed_date == target_date


# =========================================================
# АРХІВ ВИКОНАНИХ СПРАВ
# =========================================================

def get_completed_from_archive(
    archive,
    target_date,
    activity_type
):
    """
    Витягує виконані справи з архіву
    за конкретну добу Грінвуду.
    """

    result = []

    if not isinstance(archive, list):
        return result

    for entry in archive:

        completed_date = parse_date(
            entry.get("completed_date")
        )

        if completed_date != target_date:
            continue

        result.append({
            "type": activity_type,
            "title": get_title(entry),
            "xp": get_xp(entry),
            "spheres": normalize_spheres(entry)
        })

    return result


# =========================================================
# ВИКОНАНІ СПРАВИ
# =========================================================

def get_completed_activities(
    player,
    target_date
):
    """
    Джерела:

    📜 scroll_archive
    🔄 ritual_archive
    🌱 plant_archive
    """

    completed = []

    completed.extend(
        get_completed_from_archive(
            player.get("scroll_archive") or [],
            target_date,
            "scroll"
        )
    )

    completed.extend(
        get_completed_from_archive(
            player.get("ritual_archive") or [],
            target_date,
            "ritual"
        )
    )

    completed.extend(
        get_completed_from_archive(
            player.get("plant_archive") or [],
            target_date,
            "plant"
        )
    )

    return completed


# =========================================================
# ШТРАФИ ЗА ПРОПУЩЕНІ СУВОЇ
# =========================================================

def process_missed_scrolls(
    player,
    current_date,
    history,
    penalties_by_sphere
):
    """
    Перевіряє активні сувої.

    Якщо дедлайн минув:
        штраф = 2/3 XP

    Після цього сувій видаляється
    з активних.
    """

    scrolls = player.get("scrolls") or []

    remaining_scrolls = []
    missed = []

    for scroll in scrolls:

        deadline_value = scroll.get(
            "deadline"
        )

        deadline = parse_date(
            deadline_value
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

        title = get_title(scroll)
        xp = get_xp(scroll)

        if penalty_already_applied(
            history,
            "scroll",
            title,
            str(deadline_value)
        ):

            continue

        penalty = calculate_penalty(xp)

        spheres = normalize_spheres(
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
                    penalties_by_sphere[sphere] += share

        history.append({
            "type": "penalty",
            "activity_type": "scroll",
            "title": title,
            "xp": xp,
            "penalty": penalty,
            "deadline": str(deadline_value),
            "date": current_date.isoformat()
        })

        missed.append({
            "type": "scroll",
            "title": title,
            "penalty": penalty
        })

    player["scrolls"] = remaining_scrolls

    return missed


# =========================================================
# ШТРАФИ ЗА ПРОПУЩЕНІ РОСЛИНИ
# =========================================================

def process_missed_plants(
    player,
    current_date,
    history,
    penalties_by_sphere
):
    """
    Рослина є довгостроковою ціллю,
    але має deadline.

    Якщо deadline минув:
        штраф = 2/3 XP

    Важливо:
    рослина НЕ видаляється після штрафу.

    Вона залишається активною, оскільки це
    довгострокова ціль.

    Повторного штрафу за той самий deadline
    не буде, оскільки запис потрапляє
    до completed_history.
    """

    plants = player.get("plants") or []

    missed = []

    for plant in plants:

        deadline_value = plant.get(
            "deadline"
        )

        deadline = parse_date(
            deadline_value
        )

        if deadline is None:
            continue

        if deadline >= current_date:
            continue

        title = get_title(plant)
        xp = get_xp(plant)

        if penalty_already_applied(
            history,
            "plant",
            title,
            str(deadline_value)
        ):
            continue

        penalty = calculate_penalty(xp)

        spheres = normalize_spheres(
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
                    penalties_by_sphere[sphere] += share

        history.append({
            "type": "penalty",
            "activity_type": "plant",
            "title": title,
            "xp": xp,
            "penalty": penalty,
            "deadline": str(deadline_value),
            "date": current_date.isoformat()
        })

        missed.append({
            "type": "plant",
            "title": title,
            "penalty": penalty
        })

    return missed


# =========================================================
# ПРОПУЩЕНІ РИТУАЛИ
# =========================================================

def process_missed_rituals(
    player,
    previous_date,
    history,
    penalties_by_sphere
):
    """
    Перевіряє ритуали попередньої доби.
    """

    rituals = player.get("rituals") or []

    missed = []

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

        title = get_title(ritual)
        xp = get_xp(ritual)

        deadline_key = (
            previous_date.isoformat()
        )

        if penalty_already_applied(
            history,
            "ritual",
            title,
            deadline_key
        ):
            continue

        penalty = calculate_penalty(xp)

        spheres = normalize_spheres(
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
                    penalties_by_sphere[sphere] += share

        history.append({
            "type": "penalty",
            "activity_type": "ritual",
            "title": title,
            "xp": xp,
            "penalty": penalty,
            "deadline": deadline_key,
            "date": previous_date.isoformat()
        })

        missed.append({
            "type": "ritual",
            "title": title,
            "penalty": penalty
        })

    return missed


# =========================================================
# ПОРЯДОК ДЕННИЙ
# =========================================================

def build_agenda(
    player,
    current_date
):
    """
    Формує список активних справ
    на поточну добу.
    """

    lines = []

    # -----------------------------------------------------
    # СУВОЇ
    # -----------------------------------------------------

    for scroll in player.get("scrolls") or []:

        title = get_title(scroll)
        xp = get_xp(scroll)

        deadline_value = scroll.get(
            "deadline"
        )

        deadline = parse_date(
            deadline_value
        )

        if deadline == current_date:

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

    for ritual in player.get("rituals") or []:

        if not ritual_is_for_date(
            ritual,
            current_date
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

    for plant in player.get("plants") or []:

        title = get_title(plant)
        xp = get_xp(plant)

        deadline_value = plant.get(
            "deadline"
        )

        deadline = parse_date(
            deadline_value
        )

        if deadline == current_date:

            icon = "🔥"

        else:

            icon = "🌱"

        lines.append(
            f"{icon} <b>{title}</b> "
            f"({xp:.1f} XP)"
        )

    return lines


# =========================================================
# ЗБЕРЕЖЕННЯ ПІДСУМКУ
# =========================================================

def save_summary_data(
    user_id,
    player
):
    """
    Оновлює тільки ті колонки,
    які реально використовуються summary.

    completed_history є окремою колонкою.
    """

    statistics = (
        player.get("statistics")
        or {}
    )

    current_date = get_greenwood_date()

    statistics[
        "last_summary_date"
    ] = current_date.isoformat()

    player["statistics"] = statistics

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

            "plants": player.get(
                "plants",
                []
            ),

            "completed_history": player.get(
                "completed_history",
                []
            ),

            "statistics": statistics
        }
    )


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
    # ІСТОРІЯ ШТРАФІВ
    # =====================================================

    history = get_completed_history(
        player
    )

    # =====================================================
    # ВИКОНАНІ СПРАВИ
    # =====================================================

    completed = get_completed_activities(
        player,
        previous_date
    )

    earned_by_sphere = {
        sphere: 0.0
        for sphere in SPHERE_NAMES
    }

    penalties_by_sphere = {
        sphere: 0.0
        for sphere in SPHERE_NAMES
    }

    completed_scrolls = []
    completed_rituals = []
    completed_plants = []

    for entry in completed:

        xp = entry["xp"]
        spheres = entry["spheres"]

        if spheres:

            share = xp / len(spheres)

            for sphere in spheres:

                if sphere in earned_by_sphere:

                    earned_by_sphere[
                        sphere
                    ] += share

        if entry["type"] == "scroll":

            completed_scrolls.append(
                (entry["title"], xp)
            )

        elif entry["type"] == "ritual":

            completed_rituals.append(
                (entry["title"], xp)
            )

        elif entry["type"] == "plant":

            completed_plants.append(
                (entry["title"], xp)
            )

    # =====================================================
    # ПРОПУЩЕНІ СПРАВИ
    # =====================================================

    missed = []

    # -----------------------------------------------------
    # Сувої
    # -----------------------------------------------------

    missed.extend(
        process_missed_scrolls(
            player,
            current_greenwood_date,
            history,
            penalties_by_sphere
        )
    )

    # -----------------------------------------------------
    # Рослини
    # -----------------------------------------------------

    missed.extend(
        process_missed_plants(
            player,
            current_greenwood_date,
            history,
            penalties_by_sphere
        )
    )

    # -----------------------------------------------------
    # Ритуали
    # -----------------------------------------------------

    missed.extend(
        process_missed_rituals(
            player,
            previous_date,
            history,
            penalties_by_sphere
        )
    )

    save_completed_history(
        player,
        history
    )

    # =====================================================
    # ЗБЕРІГАЄМО
    # =====================================================

    save_summary_data(
        user_id,
        player
    )

    # =====================================================
    # ФОРМУЄМО ТЕКСТ
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

    if not missed:

        text += (
            "Нічого. Ліс задоволений. 🌿\n\n"
        )

    else:

        for activity in missed:

            text += (
                f"❌ {activity['title']} "
                f"−{activity['penalty']:.1f} XP\n"
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

        earned = earned_by_sphere[sphere]
        penalty = penalties_by_sphere[sphere]

        if earned == 0 and penalty == 0:
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

            text += f"{line}\n"

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
    усім гравцям із таблиці players.

    Цю функцію викликає scheduler.py о 07:00.
    """

    print("🌅 Починаю формування щоденних підсумків...")

    try:

        response = (
            supabase
            .table("players")
            .select("user_id")
            .execute()
        )

        players = response.data or []

        print(
            f"👥 Знайдено гравців: {len(players)}"
        )

    except Exception as error:

        print(
            "❌ Не вдалося отримати список гравців "
            f"для щоденних підсумків: {error}"
        )

        return

    sent = 0
    failed = 0

    for player_row in players:

        user_id = str(
            player_row.get("user_id")
        )

        if not user_id:
            continue

        try:

            summary = make_player_summary(
                user_id
            )

            bot.send_message(
                int(user_id),
                summary,
                parse_mode="HTML"
            )

            sent += 1

            print(
                f"✅ Підсумок відправлено: {user_id}"
            )

        except Exception as error:

            failed += 1

            print(
                f"❌ Помилка підсумку "
                f"для {user_id}: {error}"
            )

    print(
        "🌅 Щоденні підсумки завершено. "
        f"Відправлено: {sent}, "
        f"помилок: {failed}"
    )
