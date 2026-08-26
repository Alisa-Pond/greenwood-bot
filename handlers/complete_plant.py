import random

from telebot import types

from services.config import bot
from services.database import get_player, update_player

from services.activity_utils import (
    get_title,
    get_xp,
    get_spheres,
    get_today,
    is_overdue,
    add_xp_to_character,
    add_xp_to_spheres,
    update_statistics,
    build_back_button,
    send_level_up_notifications,
)

from services.world_conditions import (
    get_world_conditions,
)

from services.loot import (
    roll_loot_many,
    group_loot,
    format_loot_text,
)


print("🌱 Завантажено систему завершення вирощування...")


# =========================================================
# 🎲 ШАНС ВИПАДІННЯ ЛУТУ
# =========================================================
#
# Для рослини:
#
# 20% → 1 предмет
# 80% → 0 предметів
#
# ВАЖЛИВО:
#
# Тут ми визначаємо ТІЛЬКИ КІЛЬКІСТЬ ЛУТУ.
#
# ЯКИЙ саме предмет випаде,
# визначає loot.py окремим roll.
#
# =========================================================

PLANT_LOOT_CHANCE = 0.20


def roll_plant_loot_amount():
    """
    Кидає шанс на отримання луту від рослини.

    20% → 1 предмет
    80% → 0 предметів
    """

    if random.random() < PLANT_LOOT_CHANCE:

        return 1

    return 0


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

    # -----------------------------------------------------
    # ОТРИМУЄМО РОСЛИНУ
    # -----------------------------------------------------

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

    # =====================================================
    # XP ПЕРСОНАЖА
    # =====================================================

    character_level_ups = add_xp_to_character(
        player,
        xp
    )

    # =====================================================
    # XP СФЕР
    # =====================================================

    sphere_level_ups = add_xp_to_spheres(
        player,
        spheres,
        xp
    )

    # =====================================================
    # 🎲 ЛУТ
    # =====================================================
    #
    # КРОК 1:
    #
    # Визначаємо, чи випаде лут.
    #
    # 🌱 Рослина:
    #
    # 20% → 1 предмет
    # 80% → 0 предметів
    #
    # КРОК 2:
    #
    # Якщо предмет випав,
    # loot.py робить roll конкретного предмета.
    #
    # =====================================================

    loot_amount = roll_plant_loot_amount()

    grouped_loot = []

    if loot_amount > 0:

        # -------------------------------------------------
        # Отримуємо актуальні умови світу
        # -------------------------------------------------

        world_conditions = get_world_conditions(
            player
        )

        # -------------------------------------------------
        # Робимо roll конкретного предмета
        # -------------------------------------------------

        loot_item_ids = roll_loot_many(
            loot_amount,
            world_conditions
        )

        # -------------------------------------------------
        # Групуємо однакові предмети
        # -------------------------------------------------

        grouped_loot = group_loot(
            loot_item_ids
        )

        # -------------------------------------------------
        # Додаємо лут до інвентарю
        # -------------------------------------------------

        from services.loot import add_loot_to_inventory

        player[
            "inventory"
        ] = add_loot_to_inventory(
            player.get(
                "inventory"
            ) or [],
            loot_item_ids
        )

    # =====================================================
    # АРХІВ
    # =====================================================

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

    # =====================================================
    # ВИДАЛЯЄМО З ТЕПЛИЦІ
    # =====================================================

    plants.pop(
        selected_index
    )

    player[
        "plants"
    ] = plants

    player[
        "plant_archive"
    ] = plant_archive

    # =====================================================
    # СТАТИСТИКА
    # =====================================================

    update_statistics(
        player,
        plants_harvested=1
    )

    # =====================================================
    # SUPABASE
    # =====================================================

    update_player(
        user_id,
        {
            "level": player["level"],
            "level_xp": player["level_xp"],
            "level_max_xp": player["level_max_xp"],
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

    # =====================================================
    # ПОВІДОМЛЕННЯ ПРО ПІДВИЩЕННЯ
    # =====================================================

    send_level_up_notifications(
        bot,
        message.chat.id,
        character_level_ups,
        sphere_level_ups
    )

    # =====================================================
    # ПОВІДОМЛЕННЯ
    # =====================================================

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

    loot_text = format_loot_text(
        grouped_loot
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
