from datetime import datetime

from services.config import bot
from services.database import get_player
from keyboards import get_quests_menu, get_greenhouse_menu

print("⚙️ Реєструємо меню теплиці...")


# ==================================================
# 🌱 ВІДКРИТТЯ ТЕПЛИЦІ
# ==================================================

@bot.message_handler(
    func=lambda message: message.text == "🌱 Теплиця"
)
def open_greenhouse(message):

    user_id = str(message.from_user.id)

    player = get_player(user_id)

    plants = player.get("plants") or []

    today = datetime.now()

    date_text = today.strftime("%d.%m.%Y")

    weekdays = {
        0: "понеділок",
        1: "вівторок",
        2: "середа",
        3: "четвер",
        4: "п'ятниця",
        5: "субота",
        6: "неділя"
    }

    weekday = weekdays[today.weekday()]

    text = (
        "🌱 <b>Теплиця Грінвуду</b>\n\n"
        f"📅 Сьогодні: <b>{date_text}, {weekday}</b>\n"
        "────────────────────\n\n"
    )

    if not plants:

        text += (
            "🌿 <i>У теплиці поки тихо.</i>\n\n"
            "Тут немає жодної активної рослини.\n"
            "Можливо, настав час посадити щось, "
            "що справді варте твого ґрунту? 🌱"
        )

    else:

        text += (
            f"🌿 <b>Активні рослини: {len(plants)}</b>\n\n"
        )

        for plant in plants:

            title = plant.get(
                "title",
                "Без назви"
            )

            spheres = plant.get(
                "spheres",
                []
            )

            xp = plant.get(
                "xp",
                0
            )

            deadline = plant.get(
                "deadline",
                "—"
            )

            reward = plant.get(
                "reward",
                "—"
            )

            sphere_text = "".join(
                sphere.get("emoji", "")
                if isinstance(sphere, dict)
                else str(sphere)
                for sphere in spheres
            )

            # Якщо дата дедлайну вже близько,
            # рослина отримує маленький знак уваги.
            try:

                deadline_date = datetime.strptime(
                    deadline,
                    "%d.%m.%y"
                ).date()

                days_left = (
                    deadline_date - today.date()
                ).days

                if days_left < 0:
                    status = "🥀"
                elif days_left == 0:
                    status = "🔥"
                elif days_left <= 3:
                    status = "⚠️"
                else:
                    status = "🌱"

            except Exception:

                status = "🌱"

            text += (
                f"{status} {sphere_text} "
                f"<b>{title}</b> "
                f"({float(xp):.1f} XP)\n"
                f"    └── 📅 Дедлайн: {deadline}\n"
                f"    └── 🎁 Нагорода: {reward}\n\n"
            )

    bot.send_message(
        message.chat.id,
        text,
        parse_mode="HTML",
        reply_markup=get_greenhouse_menu()
    )


# ==================================================
# 🔙 НАЗАД ДО МОЇХ КВЕСТІВ
# ==================================================

@bot.message_handler(
    func=lambda message: message.text == "🔙 Назад до квестів"
)
def back_from_greenhouse(message):

    bot.send_message(
        message.chat.id,
        "📝 <b>Повертаємось до твоїх квестів.</b>",
        parse_mode="HTML",
        reply_markup=get_quests_menu()
    )
