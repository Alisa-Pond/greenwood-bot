import random
from datetime import datetime, timezone

from services.config import bot
from services.database import get_player, update_player

from keyboards import get_quests_menu

from handlers.my_quests.expedition.menu import (
    get_active_expedition
)

from handlers.my_quests.expedition.timer import (
    calculate_active_seconds,
    format_expedition_time
)

from handlers.my_quests.expedition.items import (
    EXPEDITION_ITEMS
)


print("🏁 Реєструємо завершення експедицій...")


# =========================================================
# XP
# =========================================================

# За кожні повні 30 хвилин експедиції
# загін приносить 5 XP.
XP_PER_28_MINUTES = 5


# =========================================================
# ЙМОВІРНОСТІ ЛУТУ
# =========================================================

LOOT_CHANCES = {
    "common": 0.45,
    "rare": 0.15,
    "very_rare": 0.04
}


# =========================================================
# НАЗВИ СФЕР
# =========================================================

SPHERE_NAMES = {

    "health": "💪 Здоров'я",
    "wisdom": "🧠 Мудрість",
    "art": "🎨 Творчість",
    "finance": "💵 Фінанси",
    "relations": "🤝 Зв'язки"
}


# =========================================================
# ВИБІР ВИПАДКОВОГО ПРЕДМЕТА
# =========================================================

def get_random_item():

    roll = random.random()

    # -----------------------------------------------------
    # ДУЖЕ РІДКІСНИЙ
    # -----------------------------------------------------

    if roll < LOOT_CHANCES["very_rare"]:

        rarity = "very_rare"

    # -----------------------------------------------------
    # РІДКІСНИЙ
    # -----------------------------------------------------

    elif roll < (
        LOOT_CHANCES["very_rare"]
        + LOOT_CHANCES["rare"]
    ):

        rarity = "rare"

    # -----------------------------------------------------
    # ЗВИЧАЙНИЙ
    # -----------------------------------------------------

    elif roll < (
        LOOT_CHANCES["very_rare"]
        + LOOT_CHANCES["rare"]
        + LOOT_CHANCES["common"]
    ):

        rarity = "common"

    # -----------------------------------------------------
    # НІЧОГО
    # -----------------------------------------------------

    else:

        return None

    available_items = [
        item_id
        for item_id, item_data
        in EXPEDITION_ITEMS.items()
        if item_data.get("rarity") == rarity
    ]

    if not available_items:

        return None

    return random.choice(
        available_items
    )


# =========================================================
# ПОШУК АРТЕФАКТІВ
# =========================================================

def find_expedition_items(
    active_seconds
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

        item_id = get_random_item()

        if item_id:

            found_items.append(
                item_id
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
# XP СФЕРАМ
# =========================================================

def add_xp_to_spheres(
    player,
    spheres,
    total_xp
):

    if not spheres:

        return []

    if total_xp <= 0:

        return []

    player_spheres = player.get(
        "spheres",
        {}
    )

    if not isinstance(
        player_spheres,
        dict
    ):

        return []

    xp_per_sphere = (
        total_xp
        / len(spheres)
    )

    level_ups = []

    for sphere_key in spheres:

        sphere = player_spheres.get(
            sphere_key
        )

        if not sphere:

            continue

        sphere["xp"] = float(
            sphere.get(
                "xp",
                0
            )
        ) + xp_per_sphere

        # -------------------------------------------------
        # ПІДВИЩЕННЯ РІВНЯ
        # -------------------------------------------------

        while (
            sphere["xp"]
            >= sphere["max_xp"]
        ):

            sphere["xp"] -= (
                sphere["max_xp"]
            )

            sphere["lvl"] += 1

            sphere["max_xp"] = round(
                sphere["max_xp"] * 1.5,
                2
            )

            level_ups.append(
                sphere_key
            )

    return level_ups


# =========================================================
# ДОДАТИ ПРЕДМЕТИ В РЮКЗАК
# =========================================================

def add_items_to_inventory(
    player,
    found_items
):

    inventory = player.get(
        "inventory",
        []
    )

    if not isinstance(
        inventory,
        list
    ):

        inventory = []

    for item_id in found_items:

        item_data = EXPEDITION_ITEMS.get(
            item_id
        )

        if not item_data:

            continue

        item_name = item_data.get(
            "name"
        )

        if item_name:

            inventory.append(
                item_name
            )

    return inventory


# =========================================================
# ФОРМАТУВАННЯ ЗНАХІДОК
# =========================================================

def format_found_items(
    found_items
):

    if not found_items:

        return None

    counts = {}

    for item_id in found_items:

        item_data = EXPEDITION_ITEMS.get(
            item_id
        )

        if not item_data:

            continue

        item_name = item_data.get(
            "name"
        )

        if not item_name:

            continue

        counts[item_name] = (
            counts.get(
                item_name,
                0
            ) + 1
        )

    if not counts:

        return None

    lines = []

    for item_name, count in counts.items():

        lines.append(
            f"• {item_name} ×{count}"
        )

    return "\n".join(
        lines
    )


# =========================================================
# ФОРМАТУВАННЯ XP
# =========================================================

def format_xp_report(
    total_xp,
    spheres,
    level_ups
):

    if total_xp <= 0:

        return (
            "✨ За цей час загін не встиг "
            "здобути достатньо досвіду "
            "для нарахування XP."
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

    if level_ups:

        unique_level_ups = []

        for sphere in level_ups:

            if sphere not in unique_level_ups:

                unique_level_ups.append(
                    sphere
                )

        lines.append("")

        lines.append(
            "🌟 <b>Сфери підвищили рівень!</b>"
        )

        for sphere in unique_level_ups:

            lines.append(
                f"• {SPHERE_NAMES.get(sphere, sphere)}"
            )

    return "\n".join(
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

    player = get_player(
        user_id
    )

    expedition = get_active_expedition(
        player
    )

    # =====================================================
    # НЕМАЄ ЕКСПЕДИЦІЇ
    # =====================================================

    if not expedition:

        bot.send_message(
            message.chat.id,
            (
                "🐜 <b>Генерал Мураха:</b>\n\n"

                "Здається, жоден загін зараз "
                "не перебуває в експедиції.\n\n"

                "Карти порожні, компаси мовчать. "
                "Мабуть, час відправити когось "
                "на пошуки пригод."
            ),
            parse_mode="HTML",
            reply_markup=get_quests_menu()
        )

        return

    # =====================================================
    # РОЗРАХУНОК ЧАСУ
    # =====================================================

    active_seconds = calculate_active_seconds(
        expedition
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

    level_ups = add_xp_to_spheres(
        player,
        spheres,
        total_xp
    )

    # =====================================================
    # АРТЕФАКТИ
    # =====================================================

    found_items = find_expedition_items(
        active_seconds
    )

    inventory = add_items_to_inventory(
        player,
        found_items
    )

    # =====================================================
    # ЗАГАЛЬНИЙ XP
    # =====================================================

    current_total_xp = float(
        player.get(
            "xp_total",
            0
        ) or 0
    )

    player["xp_total"] = (
        current_total_xp
        + total_xp
    )

    # =====================================================
    # СТАТИСТИКА
    # =====================================================

    statistics = player.get(
        "statistics",
        {}
    )

    if not isinstance(
        statistics,
        dict
    ):

        statistics = {}

    statistics["expeditions_completed"] = (
        int(
            statistics.get(
                "expeditions_completed",
                0
            ) or 0
        )
        + 1
    )

    # =====================================================
    # ОЧИЩАЄМО АКТИВНУ ЕКСПЕДИЦІЮ
    # =====================================================

    player["expeditions"] = []

    player["inventory"] = inventory

    player["statistics"] = statistics

    # =====================================================
    # ЗБЕРІГАЄМО
    # =====================================================

    success = update_player(
        user_id,
        {
            "xp_total": player["xp_total"],
            "spheres": player["spheres"],
            "inventory": player["inventory"],
            "expeditions": player["expeditions"],
            "statistics": player["statistics"]
        }
    )

    # =====================================================
    # ПОМИЛКА ЗБЕРЕЖЕННЯ
    # =====================================================

    if not success:

        bot.send_message(
            message.chat.id,
            (
                "🐜 <b>Генерал Мураха:</b>\n\n"

                "Загін повернувся до табору, "
                "але виникла проблема із журналом "
                "експедиції.\n\n"

                "⚠️ Результати не були надійно "
                "збережені. Спробуй повторити "
                "завершення трохи пізніше."
            ),
            parse_mode="HTML"
        )

        return

    # =====================================================
    # ФОРМУЄМО ДОПОВІДЬ
    # =====================================================

    time_text = format_expedition_time(
        active_seconds
    )

    found_text = format_found_items(
        found_items
    )

    xp_text = format_xp_report(
        total_xp,
        spheres,
        level_ups
    )

    # =====================================================
    # ПОЧАТОК ДОПОВІДІ
    # =====================================================

    report = (
        "🐜 <b>ГЕНЕРАЛ МУРАХА ДОПОВІДАЄ!</b>\n\n"

        "Загін повернувся до Грінвуду.\n"
        "Усі мурахи на місці, спорядження "
        "перевірено, польові записи доставлено "
        "до штабу.\n\n"

        f"⏱️ <b>Час в експедиції:</b> "
        f"{time_text}\n\n"
    )

    # =====================================================
    # ЗНАХІДКИ
    # =====================================================

    if found_text:

        report += (
            "🔎 <b>Під час подорожі мурахи знайшли:</b>\n\n"
            f"{found_text}\n\n"

            "🎒 Усі знахідки передано "
            "до твого рюкзака.\n\n"
        )

    else:

        report += (
            "🔎 <b>Що знайшли мурахи:</b>\n\n"

            "Цього разу скрині Грінвуду "
            "залишилися мовчазними.\n\n"

            "Мурахи нічого не знайшли, "
            "але повернулися з новими враженнями "
            "та досвідом.\n\n"
        )

    # =====================================================
    # XP
    # =====================================================

    report += (
        f"{xp_text}\n\n"
    )

    # =====================================================
    # ФІНАЛЬНА ФРАЗА
    # =====================================================

    report += (
        "🐜 Генерал струшує пил із карти, "
        "акуратно згортає її та додає:\n\n"

        "«Експедицію завершено. "
        "Загін готовий до наступного наказу.»"
    )

    # =====================================================
    # ПОВЕРТАЄМО В МЕНЮ "МОЇ КВЕСТИ"
    # =====================================================

    bot.send_message(
        message.chat.id,
        report,
        parse_mode="HTML",
        reply_markup=get_quests_menu()
    )
