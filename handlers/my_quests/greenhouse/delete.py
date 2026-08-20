from services.config import bot
from services.database import get_player, update_player
from keyboards import get_greenhouse_menu


print("⚙️ Завантажено видалення рослин...")


# ==================================================
# ПОЧАТОК ВИДАЛЕННЯ
# ==================================================

@bot.message_handler(
    func=lambda message: message.text == "🪓 Вирвати баобаб"
)
def start_delete_plant(message):

    user_id = str(message.from_user.id)
    player = get_player(user_id)

    plants = player.get("plants") or []

    if not plants:
        bot.send_message(
            message.chat.id,
            "🌲<b>Олівер:🌲</b>\n"
            " Тут нічого виривати. "
            "Спочатку посадити щось треба.",
            parse_mode="HTML",
            reply_markup=get_greenhouse_menu()
        )
        return


    text = (
        "🪓 <b>Олівер заходить до теплиці з лопатою.</b>\n\n"
        "🌲<b>Олівер:🌲</b>\n"
        " Ну добре. Що цього разу вириваємо з корінням?\n\n"
        "🌿 <b>Твої рослини:</b>\n\n"
    )


    for index, plant in enumerate(plants, start=1):

        title = plant.get("title", "Без назви")
        xp = plant.get("xp", 0)
        deadline = plant.get("deadline", "—")

        text += (
            f"<b>{index}.</b> 🌱 {title}\n"
            f"    └── ⭐ {xp} XP\n"
            f"    └── 📅 Дедлайн: {deadline}\n\n"
        )


    text += (
        "🌲<b>Олівер:🌲</b>\n"
        "Під яким номером баоба? \n\n"
        "Або натисни <b>🔙 Назад</b>, якщо передумав."
    )


    bot.send_message(
        message.chat.id,
        text,
        parse_mode="HTML"
    )

    bot.register_next_step_handler(
        message,
        process_delete_plant
    )


# ==================================================
# ОБРОБКА ВИБОРУ
# ==================================================

def process_delete_plant(message):

    if message.text == "🔙 Назад":

        bot.send_message(
            message.chat.id,
            "🌲<b>Олівер:🌲</b>\n"
            "Гаразд. Нехай росте.",
            parse_mode="HTML",
            reply_markup=get_greenhouse_menu()
        )

        return


    try:

        plant_number = int(message.text)

    except ValueError:

        bot.send_message(
            message.chat.id,
            "🌲<b>Олівер:🌲</b>\n"
            " Номер, кажу. Не заклинання.\n\n",
            parse_mode="HTML"
        )

        bot.register_next_step_handler(
            message,
            process_delete_plant
        )

        return


    user_id = str(message.from_user.id)
    player = get_player(user_id)

    plants = player.get("plants") or []


    if plant_number < 1 or plant_number > len(plants):

        bot.send_message(
            message.chat.id,
            "🌲<b>Олівер:🌲</b>\n"
            " Такої рослини тут немає." ,
            parse_mode="HTML"
        )

        bot.register_next_step_handler(
            message,
            process_delete_plant
        )

        return


    # ==================================================
    # ВИДАЛЕННЯ
    # ==================================================

    removed_plant = plants.pop(plant_number - 1)

    title = removed_plant.get(
        "title",
        "рослина без назви"
    )


    update_player(
        user_id,
        {
            "plants": plants
        }
    )


    bot.send_message(
        message.chat.id,
        f"🌱 <b>{title}</b> більше не росте у теплиці.\n\n"
        "🌲<b>Олівер:🌲</b>\n"
        "Не переживай, іноді треба звільнити землю для чогось кращого.\n\n"
        f"🌿 <b>Залишилось рослин:</b> {len(plants)}",

        parse_mode="HTML",
        reply_markup=get_greenhouse_menu()
    )
