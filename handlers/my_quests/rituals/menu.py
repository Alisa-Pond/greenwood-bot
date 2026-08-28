from datetime import datetime

from services.config import bot
from services.database import get_player
from keyboards import get_quests_menu, get_rituals_menu


print("⚙️ Реєструємо меню ритуалів...")


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
# ВІДКРИТТЯ РИТУАЛІВ
# =========================================================

@bot.message_handler(
    func=lambda message: message.text == "🔄 Ритуали"
)
def open_rituals(message):

    user_id = str(message.from_user.id)

    player = get_player(user_id)

    rituals = player.get("rituals") or []

    today = datetime.now()

    today_name = WEEKDAYS[today.weekday()]
    today_date = today.strftime("%d.%m.%Y")

    # -----------------------------------------------------
    # Якщо ритуалів немає
    # -----------------------------------------------------

    if not rituals:

        text = (
            "🦇 <b>Марчелло🦇</b>\n"
            "«🔄 <b>Твої магічні ритуали Грінвуду</b>\n\n"
            f"📅 Сьогодні: <b>{today_date}, {today_name}</b>\n"
            "────────────────────\n\n"
            "🌙 Тут поки тихо...»\n\n"
        )

        bot.send_message(
            message.chat.id,
            text,
            parse_mode="HTML",
            reply_markup=get_rituals_menu()
        )

        return


    # -----------------------------------------------------
    # Заголовок
    # -----------------------------------------------------

    text = (
        "🦇 <b>Марчелло🦇</b>\n"
        "«🔄 <b>Твої магічні ритуали Грінвуду</b>\n"
        f"📅 Сьогодні: <b>{today_date}, {today_name}</b>\n"
        "────────────────────\n"
    )


    # -----------------------------------------------------
    # Виводимо ритуали
    # -----------------------------------------------------

    for ritual in rituals:

        # Захист від пошкодженого запису
        if not isinstance(ritual, dict):
            continue


        # -------------------------
        # Назва
        # -------------------------

        title = ritual.get(
            "title",
            ritual.get("name", "Без назви")
        )


        # -------------------------
        # XP
        # -------------------------

        xp = ritual.get("xp", 0)

        try:
            xp = float(xp)
        except (TypeError, ValueError):
            xp = 0.0


        # -------------------------
        # Сфери
        # -------------------------

        spheres = ritual.get("spheres", [])

        if isinstance(spheres, str):
            spheres = [spheres]


        sphere_emojis = []

        sphere_to_emoji = {
            "health": "💪",
            "wisdom": "🧠",
            "art": "🎨",
            "finance": "💵",
            "relations": "🤝"
        }


        for sphere in spheres:

            # Якщо у майбутньому ми збережемо
            # одразу emoji, це теж буде працювати
            if sphere in sphere_to_emoji:
                sphere_emojis.append(
                    sphere_to_emoji[sphere]
                )

            elif sphere in sphere_to_emoji.values():
                sphere_emojis.append(sphere)


        spheres_display = "".join(sphere_emojis)


        if not spheres_display:
            spheres_display = "✨"


        # -------------------------
        # Дні ритуалу
        # -------------------------

        days = ritual.get("days", [])

        if isinstance(days, str):

            if days.lower() == "щодня":
                days_display = "щодня"
                active_today = True

            else:
                days = [
                    day.strip().lower()
                    for day in days.split(",")
                    if day.strip()
                ]

                days_display = ", ".join(days)

                active_today = (
                    today_name in days
                )

        else:

            days = [
                str(day).strip().lower()
                for day in days
            ]

            if "щодня" in days:

                days_display = "щодня"
                active_today = True

            else:

                days_display = ", ".join(days)

                active_today = (
                    today_name in days
                )


        # -------------------------
        # Статус на сьогодні
        # -------------------------

        if active_today:
            status = "🔥"
        else:
            status = "💤"


        # -------------------------
        # Ритуал
        # -------------------------

        text += (
            f"\n{status} {spheres_display} "
            f"<b>{title}</b> ({xp:.1f} XP)\n"
            f"    └── 📅 Дні: {days_display}\n"
        )


    # -----------------------------------------------------
    # Пояснення статусів
    # -----------------------------------------------------

    text += (
        "\n────────────────────\n"
        "🔥 — ритуал прагне бути виконаним сьогодні.\n"
        "💤 — сьогодні цей ритуал спочиває. »"
    )


    bot.send_message(
        message.chat.id,
        text,
        parse_mode="HTML",
        reply_markup=get_rituals_menu()
    )


# =========================================================
# НАЗАД ДО МОЇХ КВЕСТІВ
# =========================================================

@bot.message_handler(
    func=lambda message: message.text == "🔙 Назад до квестів"
)
def back_from_rituals(message):

    bot.send_message(
        message.chat.id,
        "📝 <b>Мої квести</b>",
        parse_mode="HTML",
        reply_markup=get_quests_menu()
    )
