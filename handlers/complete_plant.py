from telebot import types

from services.config import bot
from services.database import get_player, update_player

from services.activity_utils import (
    get_title,
    get_xp,
    get_spheres,
    get_today,
    is_overdue,
    add_total_xp,
    add_xp_to_spheres,
    update_statistics,
    build_back_button,
)

from services.activity_loot import try_activity_loot


# =========================================================
# ВИБІР РОСЛИНИ
# =========================================================

@bot.message_handler(
    func=lambda message:
        message.text == "🌱 Завершити вирощування"
)
def choose_plant(message):

    user_id = str(
        message.from_user.id
    )

    player = get_player(
        user_id
    )

    plants = player.get(
        "plants"
    ) or []

    if not plants:

        bot.send_message(
            message.chat.id,

            "🌱 <b>У теплиці немає рослин.</b>\n\n"
            "Олівер дивиться на порожній ґрунт. 🌿",

            parse_mode="HTML",
            reply_markup=build_back_button(),
        )

        return

    # -----------------------------------------------------
    # КНОПКИ
    # -----------------------------------------------------

    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    for index, plant in enumerate(plants):

        overdue = (
            "⚠️ "
            if is_overdue(plant)
            else ""
        )

        markup.row(
            types.KeyboardButton(
                f"🌱 {overdue}{index + 1}. "
                f"{get_title(plant)}"
            )
        )

    markup.row(
        types.KeyboardButton("🔙 Назад")
    )

    msg = bot.send_message(
        message.chat.id,

        "🌿 <b>Яку рослину ти виростила?</b>\n\n"
        "Обери її зі списку:",

        parse_mode="HTML",
        reply_markup=markup,
    )

    bot.register_next_step_handler(
        msg,
        complete_plant
    )


# =========================================================
# ЗАВЕРШЕННЯ ВИРОЩУВАННЯ
# =========================================================

def complete_plant(message):

    if message.text == "🔙 Назад":

        from handlers.complete_activity import start_complete

        start_complete(message)

        return

    user_id = str(
        message.from_user.id
    )

    player = get_player(
        user_id
    )

    plants = player.get(
        "plants"
    ) or []

    # -----------------------------------------------------
    # ВИЗНАЧАЄМО НОМЕР
    # -----------------------------------------------------

    try:

        number = int(
            message.text
            .split(".")[0]
            .replace("🌱", "")
            .replace("⚠️", "")
            .strip()
        )

        selected_index = number - 1

    except (
        ValueError,
        IndexError
    ):

        selected_index = None

    # -----------------------------------------------------
    # ПЕРЕВІРКА
    # -----------------------------------------------------

    if (
        selected_index is None
        or not 0 <= selected_index < len(plants)
    ):

        bot.send_message(
            message.chat.id,

            "🌿 <b>Олівер піднімає брову.</b>\n\n"
            "«Цієї рослини в теплиці немає.»",

            parse_mode="HTML",
        )

        choose_plant(message)

        return

    plant = plants[
        selected_index
    ]

    title = get_title(
        plant
    )

    xp = get_xp(
        plant
    )

    spheres = get_spheres(
        plant
    )

    overdue = is_overdue(
        plant
    )

    # -----------------------------------------------------
    # XP
    # -----------------------------------------------------
    #
    # Штраф за прострочення обробляється
    # окремо.
    #
    # При виконанні рослини користувач
    # отримує прописаний XP.
    #

    add_total_xp(
        player,
        xp
    )

    add_xp_to_spheres(
        player,
        spheres,
        xp
    )

    # -----------------------------------------------------
    # ЛУТ
    # -----------------------------------------------------

    loot = try_activity_loot(
        player
    )

    # -----------------------------------------------------
    # АРХІВ
    # -----------------------------------------------------

    plant_archive = (
        player.get(
            "plant_archive"
        ) or []
    )

    completed_plant = dict(
        plant
    )

    completed_plant[
        "completed_date"
    ] = get_today()

    completed_plant[
        "earned_xp"
    ] = xp

    plant_archive.append(
        completed_plant
    )

    # -----------------------------------------------------
    # ВИДАЛЯЄМО З ТЕПЛИЦІ
    # -----------------------------------------------------

    plants.pop(
        selected_index
    )

    player[
        "plants"
    ] = plants

    player[
        "plant_archive"
    ] = plant_archive

    # -----------------------------------------------------
    # СТАТИСТИКА
    # -----------------------------------------------------

    update_statistics(
        player,
        plants_harvested=1
    )

    # -----------------------------------------------------
    # SUPABASE
    # -----------------------------------------------------

    update_player(
        user_id,
        {
            "xp_total": player["xp_total"],
            "spheres": player["spheres"],
            "plants": player["plants"],
            "plant_archive": player[
                "plant_archive"
            ],
            "statistics": player[
                "statistics"
            ],
            "inventory": player.get(
                "inventory"
            ) or [],
        }
    )

    # -----------------------------------------------------
    # ПОВІДОМЛЕННЯ
    # -----------------------------------------------------

    reward = plant.get(
        "reward",
        "твоя нагорода"
    )

    overdue_text = ""

    if overdue:

        overdue_text = (
            "\n⚠️ Рослина була прострочена, "
            "але повна нагорода за виконання повернута."
        )

    loot_text = ""

    if loot:

        loot_text = (
            f"\n🎁 Знайдено: "
            f"<b>{loot}</b>"
        )

    spheres_text = " ".join(
        spheres
    )

    bot.send_message(
        message.chat.id,

        "🌳 <b>Олівер оглядає "
        "вирощену рослину.</b>\n\n"

        f"🌱 <b>{title}</b>\n"
        f"⭐ Отримано: <b>{xp:.1f} XP</b>\n"
        f"🎯 Сфери: {spheres_text}\n"
        f"🎁 Нагорода: <b>{reward}</b>"

        f"{overdue_text}"
        f"{loot_text}\n\n"

        "🌿 Рослину переміщено до "
        "<b>Архіву теплиці</b>.",

        parse_mode="HTML",

        reply_markup=build_back_button(),
    )
