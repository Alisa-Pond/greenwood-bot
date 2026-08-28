import random

from services.config import bot
from services.database import get_player, update_player

from keyboards import (
    get_quests_menu,
    get_expedition_menu,
)

from handlers.my_quests.expedition.menu import (
    get_active_expedition
)

from handlers.my_quests.expedition.timer import (
    calculate_active_seconds,
    format_expedition_time
)

from services.activity_utils import (
    add_xp_to_character,
    update_statistics,
    send_level_up_notifications,
)

from services.conditions import (
    get_world_conditions,
)

from services.loot import (
    roll_loot_many,
    group_loot,
    format_loot_text,
    add_loot_to_inventory,
    get_item_name,
)


print("🏁 Реєструємо завершення експедицій...")


# =========================================================
# XP ЕКСПЕДИЦІЇ
# =========================================================
#
# За кожні ПОВНІ 30 хвилин активного часу:
#
# 30 хв  → 5 XP
# 60 хв  → 10 XP
# 90 хв  → 15 XP
# 120 хв → 20 XP
#
# Час привалу не враховується.
# =========================================================

XP_PER_30_MINUTES = 5


# =========================================================
# 🎲 ШАНС КІЛЬКОСТІ ЛУТУ
# =========================================================
#
# За кожні повні 30 хвилин робиться
# одна спроба отримати предмет.
#
# Зберігаємо стару загальну ймовірність
# випадіння луту з експедиції:
#
# 64% → 1 предмет
# 36% → 0 предметів
#
# ВАЖЛИВО:
#
# ЦЕ НЕ rarity roll.
#
# ЯКИЙ саме предмет випаде,
# визначає services/loot.py.
#
# loot.py сам враховує:
#
# - rarity
# - pool
# - день / ніч
# - повню
# - вагу предмета
# - доступні умови світу
#
# =========================================================

EXPEDITION_LOOT_CHANCE = 0.64


def roll_expedition_loot_amount():
    """
    Визначає кількість предметів,
    яку експедиція отримає за одну
    повну 30-хвилинну спробу.

    64% → 1 предмет
    36% → 0 предметів
    """

    if random.random() < EXPEDITION_LOOT_CHANCE:

        return 1

    return 0


# =========================================================
# КІЛЬКІСТЬ СПРОБ ЛУТУ
# =========================================================
#
# За кожні повні 30 хвилин:
#
# 1 окрема спроба.
#
# Наприклад:
#
# 29 хв  → 0 спроб
# 30 хв  → 1 спроба
# 60 хв  → 2 спроби
# 90 хв  → 3 спроби
#
# =========================================================

def find_expedition_items(
    active_seconds,
    world_conditions
):

    completed_periods = (
        int(active_seconds)
        // 1800
    )

    if completed_periods <= 0:

        return []

    found_items = []

    for _ in range(
        completed_periods
    ):

        loot_amount = (
            roll_expedition_loot_amount()
        )

        if loot_amount <= 0:

            continue

        rolled_items = roll_loot_many(
            loot_amount,
            world_conditions
        )

        if rolled_items:

            found_items.extend(
                rolled_items
            )

    return found_items


# =========================================================
# РОЗРАХУНОК XP
# =========================================================

def calculate_expedition_xp(
    active_seconds
):

    completed_periods = (
        int(active_seconds)
        // 1800
    )

    if completed_periods <= 0:

        return 0.0

    return float(
        completed_periods
        * XP_PER_30_MINUTES
    )


# =========================================================
# ФОРМУВАННЯ ЗНАХІДОК
# =========================================================
#
# Новий loot.py повертає ID предметів.
#
# Наприклад:
#
# [
#     "silver_algae",
#     "silver_algae",
#     "star_dust"
# ]
#
# group_loot() перетворює їх
# у структурований список для повідомлення.
#
# =========================================================

def format_found_items(
    found_items
):

    if not found_items:

        return None

    grouped = group_loot(
        found_items
    )

    return format_loot_text(
        grouped
    )


# =========================================================
# ФОРМУВАННЯ XP
# =========================================================

SPHERE_NAMES = {

    "health":
        "💪 Здоров'я",

    "wisdom":
        "🧠 Мудрість",

    "art":
        "🎨 Творчість",

    "finance":
        "💵 Фінанси",

    "relations":
        "🤝 Зв'язки",
}


def format_xp_report(
    total_xp,
    spheres
):

    if total_xp <= 0:

        return (
            "🐜 <b>Генерал Мураха доповідає! 🐜</b>\n"
            "« За цей час загін не встиг "
            "здобути достатньо досвіду "
            "для нарахування XP.\n\n"

            "Потрібно щонайменше "
            "<b>30 хвилин активної експедиції</b>.»"
        )

    if not spheres:

        return (
            "✨ <b>Досвід експедиції:</b>\n"
            f"• Персонаж: +{total_xp:g} XP"
        )

    xp_per_sphere = (
        total_xp
        / len(spheres)
    )

    lines = [
        "✨ <b>Досвід експедиції:</b>"
    ]

    for sphere in spheres:

        sphere_name = SPHERE_NAMES.get(
            sphere,
            sphere
        )

        lines.append(
            f"• {sphere_name}: "
            f"+{xp_per_sphere:g} XP"
        )

    return "\n".join(
        lines
    )


# =========================================================
# ІНФОРМАЦІЯ ПРО LEVEL UP
# =========================================================

def format_level_up_summary(
    level_up_data
):

    if not level_up_data:

        return None

    lines = []

    # -----------------------------------------------------
    # РІВЕНЬ ПЕРСОНАЖА
    # -----------------------------------------------------

    player_level_ups = (
        level_up_data.get(
            "player",
            []
        )
    )

    for level_up in player_level_ups:

        lines.append(
            "🌟 <b>Твій герой підвищив рівень!</b>\n"
            f"🧙‍♂️ Рівень "
            f"<b>{level_up['new_level']}</b>"
        )

    # -----------------------------------------------------
    # РІВНІ СФЕР
    # -----------------------------------------------------

    sphere_level_ups = (
        level_up_data.get(
            "spheres",
            []
        )
    )

    seen = set()

    for level_up in sphere_level_ups:

        key = level_up.get(
            "key"
        )

        if key in seen:

            continue

        seen.add(key)

        lines.append(
            f"✨ {level_up['emoji']} "
            f"<b>{level_up['name']}</b> "
            f"досягла рівня "
            f"<b>{level_up['new_level']}</b>!"
        )

    if not lines:

        return None

    return "\n\n".join(
        lines
    )


# =========================================================
# 🏁 ЗАВЕРШЕННЯ ЕКСПЕДИЦІЇ
# =========================================================

@bot.message_handler(
    func=lambda message:
        message.text == "🏁 Завершити експедицію"
)
def complete_expedition(message):

    user_id = str(
        message.from_user.id
    )

    # =====================================================
    # ОТРИМУЄМО ГРАВЦЯ
    # =====================================================

    player = get_player(
        user_id
    )

    if not player:

        bot.send_message(
            message.chat.id,

            (
                "🐜 <b>Генерал Мураха доповідає! 🐜</b>\n"
                "«Не вдалося знайти журнал персонажа.»"
            ),

            parse_mode="HTML"
        )

        return

    # =====================================================
    # АКТИВНА ЕКСПЕДИЦІЯ
    # =====================================================

    expedition = get_active_expedition(
        player
    )

    if not expedition:

        bot.send_message(
            message.chat.id,

            (
                "🐜 <b>Генерал Мураха доповідає! 🐜</b>\n"

                "«Здається, жоден загін зараз "
                "не перебуває в експедиції.\n\n"

                "Карти порожні, компаси мовчать. "
                "Мабуть, час відправити когось "
                "на пошуки пригод.»"
            ),

            parse_mode="HTML",

            reply_markup=get_quests_menu()
        )

        return

    # =====================================================
    # АКТИВНИЙ ЧАС
    # =====================================================

    active_seconds = (
        calculate_active_seconds(
            expedition
        )
    )

    # =====================================================
    # СФЕРИ
    # =====================================================

    spheres = expedition.get(
        "spheres",
        []
    )

    if not isinstance(
        spheres,
        list
    ):

        spheres = []

    # =====================================================
    # XP
    # =====================================================

    total_xp = calculate_expedition_xp(
        active_seconds
    )

    # =====================================================
    # XP ПЕРСОНАЖА + СФЕРАМ
    # =====================================================
    #
    # ВАЖЛИВО:
    #
    # Нова activity_utils.py використовує:
    #
    # add_xp_to_character(
    #     player,
    #     spheres,
    #     xp
    # )
    #
    # Вона сама додає XP:
    #
    # 1. персонажу
    # 2. сферам
    #
    # і повертає:
    #
    # {
    #     "player": [...],
    #     "spheres": [...]
    # }
    #
    # =====================================================

    level_up_data = add_xp_to_character(
        player,
        spheres,
        total_xp
    )

    # =====================================================
    # 🌲 УМОВИ СВІТУ
    # =====================================================

    world_conditions = get_world_conditions(
        player
    )

    # =====================================================
    # 🎁 ЛУТ
    # =====================================================
    #
    # За кожні повні 30 хвилин:
    #
    # 64% → 1 предмет
    # 36% → 0 предметів
    #
    # ЯКИЙ предмет випаде,
    # визначає services/loot.py.
    #
    # =====================================================

    found_items = find_expedition_items(
        active_seconds,
        world_conditions
    )

    # =====================================================
    # 🎒 ДОДАЄМО ЛУТ В ІНВЕНТАР
    # =====================================================

    inventory = add_loot_to_inventory(
        player.get(
            "inventory"
        ) or [],
        found_items
    )

    player[
        "inventory"
    ] = inventory

    # =====================================================
    # СТАТИСТИКА
    # =====================================================

    update_statistics(
        player,
        expeditions_completed=1
    )

    statistics = player.get(
        "statistics",
        {}
    )

    # =====================================================
    # ЗАВЕРШУЄМО ЕКСПЕДИЦІЮ
    # =====================================================

    player[
        "expeditions"
    ] = []

    # =====================================================
    # SUPABASE
    # =====================================================

    update_data = {

        "level":
            player.get(
                "level",
                1
            ),

        "level_xp":
            float(
                player.get(
                    "level_xp",
                    0
                ) or 0
            ),

        "level_max_xp":
            float(
                player.get(
                    "level_max_xp",
                    10
                ) or 10
            ),

        "spheres":
            player.get(
                "spheres",
                {}
            ),

        "inventory":
            player.get(
                "inventory",
                []
            ),

        "expeditions":
            [],

        "statistics":
            statistics,
    }

    # =====================================================
    # ЗБЕРІГАЄМО
    # =====================================================

    success = update_player(
        user_id,
        update_data
    )

    # =====================================================
    # ПОМИЛКА ЗБЕРЕЖЕННЯ
    # =====================================================

    if not success:

        bot.send_message(
            message.chat.id,

            (
                "🐜 <b>Генерал Мураха доповідає! 🐜</b>\n"

                "«Загін повернувся до табору, "
                "але виникла проблема із журналом "
                "експедиції.\n\n"

                "⚠️ Результати експедиції "
                "не вдалося надійно зберегти.\n\n"

                "Спробуй ще раз.»"
            ),

            parse_mode="HTML",

            reply_markup=get_expedition_menu(
                expedition
            )
        )

        return

    # =====================================================
    # ЧАС
    # =====================================================

    time_text = format_expedition_time(
        active_seconds
    )

    # =====================================================
    # ЗНАХІДКИ
    # =====================================================

    found_text = format_found_items(
        found_items
    )

    # =====================================================
    # XP
    # =====================================================

    xp_text = format_xp_report(
        total_xp,
        spheres
    )

    # =====================================================
    # ПОЧАТОК ДОПОВІДІ
    # =====================================================

    report = (
        "🐜 <b>Генерал Мураха доповідає! 🐜</b>\n"

        "«Загін повернувся до Грінвуду.\n"
        "Усі мурахи на місці, спорядження "
        "перевірено, польові записи доставлено "
        "до штабу.\n\n"

        f"⏱️ <b>Час в експедиції:</b> "
        f"{time_text}.\n\n"
    )

    # =====================================================
    # ЗНАХІДКИ
    # =====================================================

    if found_items:

        report += (
            "🔎 <b>Під час подорожі мурахи знайшли:</b>\n\n"

            f"{found_text}\n\n"

            "🎒 Усі знахідки передано "
            "до твого рюкзака.\n\n"
        )

    else:

        report += (
            "🔎 Цього разу таємниці Грінвуду "
            "залишилися мовчазними.\n\n"

            "Мурахи заглянули під кожен камінчик, розглянули кожен листочок на шляху проте нічого не знайшли. "

        )

    # =====================================================
    # XP
    # =====================================================

    report += (
        f"{xp_text}\n\n"
    )

    # =====================================================
    # LEVEL UP
    # =====================================================

    level_up_text = format_level_up_summary(
        level_up_data
    )

    if level_up_text:

        report += (
            f"{level_up_text}\n\n"
        )

    # =====================================================
    # ФІНАЛ
    # =====================================================

    report += (
        "\n\n"

        "«Експедицію завершено. "
        "Загін готовий до наступного наказу.»"
    )

    # =====================================================
    # НАДСИЛАЄМО ЗВІТ
    # =====================================================

    bot.send_message(
        message.chat.id,

        report,

        parse_mode="HTML",

        reply_markup=get_quests_menu()
    )

    # =====================================================
    # ПОВІДОМЛЕННЯ LEVEL UP
    # =====================================================

    send_level_up_notifications(
        message.chat.id,
        level_up_data
    )
