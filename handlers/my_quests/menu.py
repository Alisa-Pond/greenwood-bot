from datetime import datetime

from services.config import bot
from services.database import get_player
from keyboards import get_quests_menu


print("⚙️ Реєструємо меню 'Мої квести'...")


# =========================================================
# ДНІ ТИЖНЯ
# =========================================================

WEEKDAYS = {
    0: "пн",
    1: "вт",
    2: "ср",
    3: "чт",
    4: "пт",
    5: "сб",
    6: "нд"
}


# =========================================================
# СФЕРИ
# =========================================================

SPHERE_EMOJIS = {
    "health": "💪",
    "wisdom": "🧠",
    "art": "🎨",
    "finance": "💵",
    "relations": "🤝"
}


# =========================================================
# ОТРИМАТИ СФЕРИ У ВИГЛЯДІ ЕМОДЗІ
# =========================================================

def get_sphere_emojis(quest):
    """
    Перетворює список сфер квесту
    на рядок з відповідними емодзі.

    Наприклад:
    ["health", "wisdom"] → "💪🧠"
    """

    spheres = quest.get("spheres") or []

    if not isinstance(spheres, list):
        return ""

    return "".join(
        SPHERE_EMOJIS.get(
            str(sphere),
            ""
        )
        for sphere in spheres
    )


# =========================================================
# ПЕРЕВІРКА ВИКОНАННЯ РИТУАЛУ СЬОГОДНІ
# =========================================================

def is_ritual_completed_today(ritual):
    """
    Перевіряє, чи був цей ритуал виконаний сьогодні.

    Підтримуються різні варіанти збереження
    історії виконання.
    """

    today = datetime.now().date()
    today_iso = today.isoformat()
    today_text = today.strftime("%d.%m.%Y")

    # -----------------------------------------------------
    # Варіант 1:
    # completed_today = True
    # -----------------------------------------------------

    if ritual.get("completed_today") is True:
        return True

    # -----------------------------------------------------
    # Варіант 2:
    # last_completed
    # -----------------------------------------------------

    last_completed = ritual.get(
        "last_completed"
    )

    if last_completed:

        if isinstance(last_completed, str):

            if (
                last_completed == today_iso
                or last_completed == today_text
                or last_completed.startswith(today_iso)
            ):
                return True

    # -----------------------------------------------------
    # Варіант 3:
    # completed_dates
    # -----------------------------------------------------

    completed_dates = ritual.get(
        "completed_dates"
    )

    if isinstance(completed_dates, list):

        for date_value in completed_dates:

            if not isinstance(date_value, str):
                continue

            if (
                date_value == today_iso
                or date_value == today_text
                or date_value.startswith(today_iso)
            ):
                return True

    # -----------------------------------------------------
    # Варіант 4:
    # completion_dates
    # -----------------------------------------------------

    completion_dates = ritual.get(
        "completion_dates"
    )

    if isinstance(completion_dates, list):

        for date_value in completion_dates:

            if not isinstance(date_value, str):
                continue

            if (
                date_value == today_iso
                or date_value == today_text
                or date_value.startswith(today_iso)
            ):
                return True

    # -----------------------------------------------------
    # Нічого не знайдено
    # -----------------------------------------------------

    return False


# =========================================================
# МОЇ КВЕСТИ
# =========================================================

@bot.message_handler(
    func=lambda message:
    message.text == "📝 Мої квести"
)
def open_my_quests(message):

    user_id = str(
        message.from_user.id
    )

    player = get_player(
        user_id
    )

    scrolls = player.get(
        "scrolls"
    ) or []

    rituals = player.get(
        "rituals"
    ) or []

    plants = player.get(
        "plants"
    ) or []

    today = datetime.now().date()

    today_weekday = WEEKDAYS[
        today.weekday()
    ]

    # =====================================================
    # ЗАГОЛОВОК
    # =====================================================

    text = (
        "📝 <b>Твої активні квести Грінвуду</b>\n\n"

        f"📅 Сьогодні: <b>"
        f"{today.strftime('%d.%m.%Y')}, "
        f"{today_weekday}"
        f"</b>\n"

        "────────────────────\n\n"
    )


    # =====================================================
    # 📜 СУВОЇ
    # =====================================================

    text += (
        "📜 <b>Сувої</b>\n\n"
    )

    if scrolls:

        for scroll in scrolls:

            if not isinstance(
                scroll,
                dict
            ):
                continue

            title = scroll.get(
                "title",
                scroll.get(
                    "name",
                    "Без назви"
                )
            )

            xp = scroll.get(
                "xp",
                0
            )

            deadline_text = scroll.get(
                "deadline",
                ""
            )

            # -------------------------------------------------
            # 🔥 Тільки якщо дедлайн сьогодні
            # -------------------------------------------------

            marker = ""

            try:

                deadline = datetime.strptime(
                    deadline_text,
                    "%d.%m.%y"
                ).date()

                if deadline == today:

                    marker = "🔥 "

            except (
                ValueError,
                TypeError
            ):

                pass

            # -------------------------------------------------
            # СФЕРИ
            # -------------------------------------------------

            sphere_emojis = get_sphere_emojis(
                scroll
            )

            sphere_prefix = ""

            if sphere_emojis:

                sphere_prefix = (
                    f"{sphere_emojis} "
                )

            # -------------------------------------------------
            # ВИВІД
            # -------------------------------------------------

            text += (
                f"{marker}"
                f"{sphere_prefix}"
                f"<b>{title}</b> "
                f"({float(xp):.1f} XP)\n"

                f"    └── 📅 Дедлайн: "
                f"{deadline_text}\n\n"
            )

    else:

        text += (
            "    Поки що немає "
            "активних сувоїв.\n\n"
        )


    # =====================================================
    # 🔄 РИТУАЛИ
    # =====================================================

    text += (
        "🔄 <b>Ритуали</b>\n\n"
    )

    if rituals:

        for ritual in rituals:

            if not isinstance(
                ritual,
                dict
            ):
                continue

            title = ritual.get(
                "title",
                ritual.get(
                    "name",
                    "Без назви"
                )
            )

            xp = ritual.get(
                "xp",
                0
            )

            days = ritual.get(
                "days",
                []
            )

            # -------------------------------------------------
            # НОРМАЛІЗАЦІЯ ДНІВ
            # -------------------------------------------------

            if isinstance(
                days,
                str
            ):

                if days.lower().strip() == "щодня":

                    ritual_days = [
                        "пн",
                        "вт",
                        "ср",
                        "чт",
                        "пт",
                        "сб",
                        "нд"
                    ]

                else:

                    ritual_days = [
                        day.strip().lower()
                        for day in days.split(",")
                        if day.strip()
                    ]

            elif isinstance(
                days,
                list
            ):

                ritual_days = [
                    str(day).strip().lower()
                    for day in days
                    if str(day).strip()
                ]

            else:

                ritual_days = []


            # -------------------------------------------------
            # СТАТУС РИТУАЛУ
            # -------------------------------------------------

            if today_weekday not in ritual_days:

                marker = "💤"

            elif is_ritual_completed_today(
                ritual
            ):

                marker = "✅"

            else:

                marker = "🔥"


            # -------------------------------------------------
            # СФЕРИ
            # -------------------------------------------------

            sphere_emojis = get_sphere_emojis(
                ritual
            )

            sphere_prefix = ""

            if sphere_emojis:

                sphere_prefix = (
                    f"{sphere_emojis} "
                )

            # -------------------------------------------------
            # ДНІ
            # -------------------------------------------------

            days_display = ", ".join(
                ritual_days
            )

            # -------------------------------------------------
            # ВИВІД
            # -------------------------------------------------

            text += (
                f"{marker} "
                f"{sphere_prefix}"
                f"<b>{title}</b> "
                f"({float(xp):.1f} XP)\n"

                f"    └── 📅 Дні: "
                f"{days_display}\n\n"
            )

    else:

        text += (
            "    Поки що немає "
            "активних ритуалів.\n\n"
        )


    # =====================================================
    # 🌱 ТЕПЛИЦЯ
    # =====================================================

    text += (
        "🌱 <b>Теплиця</b>\n\n"
    )

    if plants:

        for plant in plants:

            if not isinstance(
                plant,
                dict
            ):
                continue

            title = plant.get(
                "title",
                plant.get(
                    "name",
                    "Без назви"
                )
            )

            xp = plant.get(
                "xp",
                0
            )

            deadline_text = plant.get(
                "deadline",
                ""
            )

            # -------------------------------------------------
            # МАРКЕР РОСЛИНИ
            # -------------------------------------------------

            marker = "🌱"

            # -------------------------------------------------
            # ДЕДЛАЙН СЬОГОДНІ
            # -------------------------------------------------

            try:

                deadline = datetime.strptime(
                    deadline_text,
                    "%d.%m.%y"
                ).date()

                if deadline == today:

                    marker = "🔥"

            except (
                ValueError,
                TypeError
            ):

                pass

            # -------------------------------------------------
            # СФЕРИ
            # -------------------------------------------------

            sphere_emojis = get_sphere_emojis(
                plant
            )

            sphere_prefix = ""

            if sphere_emojis:

                sphere_prefix = (
                    f"{sphere_emojis} "
                )

            # -------------------------------------------------
            # ВИВІД
            # -------------------------------------------------

            text += (
                f"{marker} "
                f"{sphere_prefix}"
                f"<b>{title}</b> "
                f"({float(xp):.1f} XP)\n"

                f"    └── 📅 Дедлайн: "
                f"{deadline_text}\n\n"
            )

    else:

        text += (
            "    У теплиці поки "
            "нічого не росте.\n\n"
        )


    # =====================================================
    # ВІДПРАВКА
    # =====================================================

    bot.send_message(
        message.chat.id,

        text,

        parse_mode="HTML",

        reply_markup=get_quests_menu()
    )


# =========================================================
# 🔙 НАЗАД
# =========================================================

@bot.message_handler(
    func=lambda message:
    message.text == "🔙 Назад"
)
def back_from_quests(message):

    from keyboards import get_main_menu

    bot.send_message(
        message.chat.id,

        "🌲 <b>Повертаємось "
        "до головної галявини.</b>",

        parse_mode="HTML",

        reply_markup=get_main_menu()
    )
