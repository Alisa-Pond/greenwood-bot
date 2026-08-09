from services.config import bot
from services.database import get_player, update_player
from keyboards import get_greenhouse_menu

print("⚙️ Завантажено архів теплиці...")


# =========================================================
# АРХІВ РОСЛИН
# =========================================================

@bot.message_handler(
    func=lambda message: message.text == "📚 Архів теплиці"
)
def open_plant_archive(message):

    user_id = str(message.from_user.id)

    player = get_player(user_id)

    archive = player.get("plant_archive") or []

    if not archive:

        bot.send_message(
            message.chat.id,
            "🌿 <b>Архів теплиці порожній.</b>\n\n"
            "Олівер уважно оглядає полиці й бурмоче:\n\n"
            "«Поки що тут нічого згадувати.\n"
            "Посади щось варте пам'яті, садівнице.» 🌱",
            parse_mode="HTML",
            reply_markup=get_greenhouse_menu()
        )

        return


    text = (
        "📚 <b>Архів теплиці Грінвуду</b>\n\n"
        "Тут зберігаються рослини, які ти виростила "
        "до кінця.\n\n"
        "────────────────────\n\n"
    )


    for index, plant in enumerate(archive, start=1):

        spheres = plant.get("spheres", [])

        sphere_text = "".join(
            sphere.get("emoji", "")
            for sphere in spheres
            if isinstance(sphere, dict)
        )

        if not sphere_text:
            sphere_text = plant.get("sphere_text", "🌿")


        title = plant.get(
            "title",
            "Без назви"
        )

        xp = plant.get(
            "xp",
            0
        )

        reward = plant.get(
            "reward",
            "Нагорода не зазначена"
        )

        completed_date = plant.get(
            "completed_date",
            "невідома дата"
        )


        text += (
            f"🌳 <b>{index}. {title}</b>\n"
            f"    └── 🎯 Сфери: {sphere_text}\n"
            f"    └── ⭐ Нагорода: {float(xp):.1f} XP\n"
            f"    └── 🎁 У реальному житті: {reward}\n"
            f"    └── 📅 Вирощено: {completed_date}\n\n"
        )


    bot.send_message(
        message.chat.id,
        text,
        parse_mode="HTML",
        reply_markup=get_greenhouse_menu()
    )
