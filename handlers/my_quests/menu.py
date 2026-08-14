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
# ПЕРЕВІРКА: ЧИ РИТУАЛ ВИКОНАНИЙ СЬОГОДНІ
# ==================================================

def ritual_completed_today(ritual, today):
    """
    Перевіряє, чи був ритуал виконаний сьогодні.

    Підтримує кілька можливих форматів збереження,
    щоб не ламати вже існуючі ритуали.
    """

    # --------------------------------------------------
    # Варіант 1: completed_today
    # --------------------------------------------------

    completed_today = ritual.get("completed_today")

    if completed_today is True:
        return True

    # --------------------------------------------------
    # Варіант 2: last_completed_date
    # --------------------------------------------------

    last_completed_date = ritual.get(
        "last_completed_date"
    )

    if last_completed_date:

        if isinstance(
            last_completed_date,
            str
        ):

            if last_completed_date == today.isoformat():
                return True

            if last_completed_date == today.strftime(
                "%d.%m.%Y"
            ):
                return True

            if last_completed_date == today.strftime(
                "%d.%m.%y"
            ):
                return True

    # --------------------------------------------------
    # Варіант 3: last_completed
    # --------------------------------------------------

    last_completed = ritual.get(
        "last_completed"
    )

    if last_completed:

        if isinstance(
            last_completed,
            str
        ):

            # ISO дата / datetime
            try:

                parsed_date = datetime.fromisoformat(
                    last_completed.replace(
                        "Z",
                        "+00:00"
                    )
                ).date()

                if parsed_date == today:
                    return True

            except (
                ValueError,
                TypeError
            ):

                pass

            # DD.MM.YYYY
            try:

                parsed_date = datetime.strptime(
                    last_completed,
                    "%d.%m.%Y"
                ).date()

                if parsed_date == today:
                    return True

            except (
                ValueError,
                TypeError
            ):

                pass

            # DD.MM.YY
            try:

                parsed_date = datetime.strptime(
                    last_completed,
                    "%d.%m.%y"
                ).date()

                if parsed_date == today:
                    return True

            except (
                ValueError,
                TypeError
            ):

                pass

    return False


# ==================================================
# МОЇ КВЕСТИ
# ==================================================

@bot.message_handler(
    func=lambda message: message.text == "📝 Мої квести"
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

    text = (
        "📝 <b>Твої активні квести Грінвуду</b>\n\n"

        f"📅 Сьогодні: <b>"
        f"{today.strftime('%d.%m.%Y')}, "
        f"{today_weekday}"
        f"</b>\n"

        "────────────────────\n\n"
    )


    # ==================================================
    # СУВОЇ
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

            # --------------------------------------------------
            # ВОГНИК ТІЛЬКИ ЯКЩО ДЕДЛАЙН СЬОГОДНІ
            # --------------------------------------------------

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

            text += (
                f"{marker}"
                f"<b>{title}</b> "
                f"({float(xp):.1f} XP)\n"

                f"    └── 📅 Дедлайн: "
                f"{deadline_text}\n\n"
            )

    else:

        text += (
            "    Поки що немає активних сувоїв.\n\n"
        )


    # ==================================================
    # РИТУАЛИ
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

            # --------------------------------------------------
            # ОБРОБКА ДНІВ
            # --------------------------------------------------

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

            # --------------------------------------------------
            # ВИЗНАЧАЄМО СТАТУС
            # --------------------------------------------------

            if ritual_completed_today(
                ritual,
                today
            ):

                marker = "✅"

            elif today_weekday in ritual_days:

                marker = "🔥"

            else:

                marker = "💤"

            days_display = ", ".join(
                ritual_days
            )

            text += (
                f"{marker} <b>{title}</b> "
                f"({float(xp):.1f} XP)\n"

                f"    └── 📅 Дні: "
                f"{days_display}\n\n"
            )

    else:

        text += (
            "    Поки що немає активних ритуалів.\n\n"
        )


    # ==================================================
    # ТЕПЛИЦЯ
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

            marker = "🌱"

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

            text += (
                f"{marker} <b>{title}</b> "
                f"({float(xp):.1f} XP)\n"

                f"    └── 📅 Дедлайн: "
                f"{deadline_text}\n\n"
            )

    else:

        text += (
            "    У теплиці поки нічого не росте.\n\n"
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
# НАЗАД
# ==================================================

@bot.message_handler(
    func=lambda message: message.text == "🔙 Назад"
)
def back_from_quests(message):

    from keyboards import get_main_menu

    bot.send_message(
        message.chat.id,
        "🌲 <b>Повертаємось до головної галявини.</b>",
        parse_mode="HTML",
        reply_markup=get_main_menu()
    )
