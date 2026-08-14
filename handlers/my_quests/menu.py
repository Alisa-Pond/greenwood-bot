from datetime import datetime

from services.config import bot
from services.database import get_player
from keyboards import get_quests_menu


print("⚙️ Реєструємо меню 'Мої квести'...")


# ==================================================
# ДНІ ТИЖНЯ
# ==================================================

WEEKDAYS = {
    0: "пн",
    1: "вт",
    2: "ср",
    3: "чт",
    4: "пт",
    5: "сб",
    6: "нд"
}


# ==================================================
# СФЕРИ
# ==================================================

SPHERE_NAMES = {
    "health": "💪 Здоров'я",
    "wisdom": "🧠 Мудрість",
    "art": "🎨 Творчість",
    "finance": "💵 Фінанси",
    "relations": "🤝 Зв'язки"
}


# ==================================================
# ФОРМАТУВАННЯ СФЕР
# ==================================================

def format_spheres(spheres):
    """
    Перетворює список сфер у красивий текст.

    Наприклад:

    ["wisdom", "art"]

    →

    🧠 Мудрість • 🎨 Творчість
    """

    if not spheres:
        return "⚪ Без визначених сфер"

    formatted = []

    for sphere in spheres:

        sphere_key = str(
            sphere
        ).strip().lower()

        sphere_name = SPHERE_NAMES.get(
            sphere_key
        )

        if sphere_name:
            formatted.append(
                sphere_name
            )

        else:
            # Якщо в базі раптом зберігатиметься
            # невідома сфера, не ламаємо меню.
            formatted.append(
                str(sphere)
            )

    return " • ".join(
        formatted
    )


# ==================================================
# ПЕРЕВІРКА ДЕДЛАЙНУ
# ==================================================

def get_deadline_marker(
    deadline_text,
    default_marker
):
    """
    Визначає маркер квесту.

    Якщо дедлайн сьогодні:
        🔥

    Якщо дата некоректна або інша:
        переданий default_marker
    """

    try:

        deadline = datetime.strptime(
            str(deadline_text),
            "%d.%m.%y"
        ).date()

        today = datetime.now().date()

        if deadline == today:
            return "🔥"

    except (
        ValueError,
        TypeError
    ):
        pass

    return default_marker


# ==================================================
# МОЇ КВЕСТИ
# ==================================================

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

    # ==================================================
    # АКТИВНІ КВЕСТИ
    # ==================================================

    scrolls = player.get(
        "scrolls"
    ) or []

    rituals = player.get(
        "rituals"
    ) or []

    plants = player.get(
        "plants"
    ) or []

    # ==================================================
    # СЬОГОДНІ
    # ==================================================

    today = datetime.now().date()

    today_weekday = WEEKDAYS[
        today.weekday()
    ]

    text = (
        "📝 <b>Твої активні квести Грінвуду</b>\n\n"

        f"📅 Сьогодні: <b>"
        f"{today.strftime('%d.%m.%Y')}, "
        f"{today_weekday}</b>\n"

        "────────────────────\n\n"
    )


    # ==================================================
    # 📜 СУВОЇ
    # ==================================================

    text += (
        "📜 <b>Сувої</b>\n\n"
    )

    if scrolls:

        for scroll in scrolls:

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

            spheres = scroll.get(
                "spheres",
                []
            )

            # ------------------------------------------
            # Маркер дедлайну
            # ------------------------------------------

            marker = get_deadline_marker(
                deadline_text,
                "🔥"
            )

            # ------------------------------------------
            # Назва + XP
            # ------------------------------------------

            text += (
                f"{marker} <b>{title}</b> "
                f"({float(xp):.1f} XP)\n"
            )

            # ------------------------------------------
            # Сфери
            # ------------------------------------------

            text += (
                "    └── "
                f"{format_spheres(spheres)}\n"
            )

            # ------------------------------------------
            # Дедлайн
            # ------------------------------------------

            text += (
                "    └── 📅 Дедлайн: "
                f"{deadline_text}\n\n"
            )

    else:

        text += (
            "    Поки що немає "
            "активних сувоїв.\n\n"
        )


    # ==================================================
    # 🔄 РИТУАЛИ
    # ==================================================

    text += (
        "🔄 <b>Ритуали</b>\n\n"
    )

    if rituals:

        for ritual in rituals:

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

            spheres = ritual.get(
                "spheres",
                []
            )

            # ------------------------------------------
            # ДНІ
            # ------------------------------------------

            if isinstance(
                days,
                str
            ):

                if (
                    days.lower().strip()
                    == "щодня"
                ):

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

            # ------------------------------------------
            # Маркер
            # ------------------------------------------

            if (
                today_weekday
                in ritual_days
            ):

                marker = "🔥"

            else:

                marker = "💤"

            # ------------------------------------------
            # Дні для відображення
            # ------------------------------------------

            days_display = ", ".join(
                ritual_days
            )

            # ------------------------------------------
            # Назва + XP
            # ------------------------------------------

            text += (
                f"{marker} <b>{title}</b> "
                f"({float(xp):.1f} XP)\n"
            )

            # ------------------------------------------
            # Сфери
            # ------------------------------------------

            text += (
                "    └── "
                f"{format_spheres(spheres)}\n"
            )

            # ------------------------------------------
            # Дні
            # ------------------------------------------

            text += (
                "    └── 📅 Дні: "
                f"{days_display}\n\n"
            )

    else:

        text += (
            "    Поки що немає "
            "активних ритуалів.\n\n"
        )


    # ==================================================
    # 🌱 ТЕПЛИЦЯ
    # ==================================================

    text += (
        "🌱 <b>Теплиця</b>\n\n"
    )

    if plants:

        for plant in plants:

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

            spheres = plant.get(
                "spheres",
                []
            )

            # ------------------------------------------
            # Маркер дедлайну
            # ------------------------------------------

            marker = get_deadline_marker(
                deadline_text,
                "🌱"
            )

            # ------------------------------------------
            # Назва + XP
            # ------------------------------------------

            text += (
                f"{marker} <b>{title}</b> "
                f"({float(xp):.1f} XP)\n"
            )

            # ------------------------------------------
            # Сфери
            # ------------------------------------------

            text += (
                "    └── "
                f"{format_spheres(spheres)}\n"
            )

            # ------------------------------------------
            # Дедлайн
            # ------------------------------------------

            text += (
                "    └── 📅 Дедлайн: "
                f"{deadline_text}\n\n"
            )

    else:

        text += (
            "    У теплиці поки нічого "
            "не росте.\n\n"
        )


    # ==================================================
    # ВІДПРАВКА
    # ==================================================

    bot.send_message(
        message.chat.id,
        text,
        parse_mode="HTML",
        reply_markup=get_quests_menu()
    )


# ==================================================
# 🔙 НАЗАД
# ==================================================

@bot.message_handler(
    func=lambda message:
        message.text == "🔙 Назад"
)
def back_from_quests(message):

    from keyboards import get_main_menu

    bot.send_message(
        message.chat.id,
        (
            "🌲 <b>Повертаємось "
            "до головної галявини.</b>"
        ),
        parse_mode="HTML",
        reply_markup=get_main_menu()
    )
