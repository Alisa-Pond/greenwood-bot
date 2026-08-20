from datetime import datetime

from services.config import bot
from services.database import get_player
from keyboards import get_quests_menu, get_greenhouse_menu


print("⚙️ Реєструємо меню теплиці...")


# ==================================================
# Дні тижня
# ==================================================

WEEKDAYS_UA = {
    0: "пн",
    1: "вт",
    2: "ср",
    3: "чт",
    4: "пт",
    5: "сб",
    6: "нд"
}


# ==================================================
# ВІДКРИТТЯ ТЕПЛИЦІ
# ==================================================

@bot.message_handler(
    func=lambda message: message.text == "🌱 Теплиця"
)
def open_greenhouse(message):

    user_id = str(message.from_user.id)

    player = get_player(user_id)

    plants = player.get("plants") or []

    today = datetime.now()

    today_text = (
        f"{today.strftime('%d.%m.%Y')}, "
        f"{WEEKDAYS_UA[today.weekday()]}"
    )

    # ==================================================
    # Якщо рослин немає
    # ==================================================

    if not plants:

        text = (
            "🌿 <b>Твоя магічна теплиця</b>\n\n"
            f"📅 Сьогодні: <b>{today_text}</b>\n"
            "────────────────────\n\n"
            "🌲<b>Олівер:🌲</b>\n"
            "Маєш щось гідне вирощування? Зараз в теплиці жодного твого насіння"
        )

    else:

        text = (
            "🌿 <b>Активні рослини: "
            f"{len(plants)}</b>\n\n"
            f"📅 Сьогодні: <b>{today_text}</b>\n"
            "────────────────────\n\n"
        )

        for plant in plants:

            title = plant.get("title", "Без назви")
            xp = float(plant.get("xp", 0))
            deadline = plant.get("deadline", "—")
            reward = plant.get("reward", "—")

            spheres = plant.get("spheres", [])

            # Якщо spheres збережені як список назв сфер
            sphere_emojis = []

            sphere_emoji_map = {
                "health": "💪",
                "wisdom": "🧠",
                "art": "🎨",
                "finance": "💵",
                "relations": "🤝"
            }

            for sphere in spheres:

                if sphere in sphere_emoji_map:
                    sphere_emojis.append(
                        sphere_emoji_map[sphere]
                    )

                else:
                    # На випадок, якщо старий запис
                    # уже містить емодзі
                    sphere_emojis.append(str(sphere))

            sphere_text = "".join(sphere_emojis)

            if not sphere_text:
                sphere_text = "🌱"

            text += (
                f"🌱 {sphere_text} "
                f"<b>{title}</b> "
                f"({xp:.1f} XP)\n"
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
# НАЗАД ДО КВЕСТІВ
# ==================================================

@bot.message_handler(
    func=lambda message: message.text == "🔙 Назад до квестів"
)
def back_from_greenhouse(message):

    bot.send_message(
        message.chat.id,
        "📝 <b>Меню квестів</b>",
        parse_mode="HTML",
        reply_markup=get_quests_menu()
    )
