import random

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

from services.activity_utils import (
    add_xp_to_character,
    update_statistics,
    get_sphere_name
)


print("🏁 Реєструємо завершення експедицій...")


# =========================================================
# XP ЕКСПЕДИЦІЇ
# =========================================================
#
# За кожні повні 30 хвилин активного часу:
# загін приносить 5 XP.
#
# =========================================================

XP_PER_30_MINUTES = 5


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

        if item_data.get(
            "rarity"
        ) == rarity

    ]

    if not available_items:

        return None

    return random.choice(
        available_items
    )


# =========================================================
# ПОШУК ПРЕДМЕТІВ
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
# ДОДАТИ ПРЕДМЕТИ В РЮКЗАК
# =========================================================

def add_items_to_inventory(
    player,
    found_items
):

    inventory = player.get(
        "inventory"
    ) or []

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
    level_up_data
):

    # -----------------------------------------------------
    # НУЛЬ XP
    # -----------------------------------------------------

    if total_xp <= 0:

        return (
            "✨ За цей час загін не встиг "
            "здобути достатньо досвіду "
            "для нарахування XP."
        )

    if not spheres:

        return (
            f"✨ <b>Досвід експедиції:</b>\n"
            f"• 🧙‍♂️ Герой: +{total_xp:g} XP"
        )

    # -----------------------------------------------------
    # XP СФЕРАМ
    # -----------------------------------------------------

    xp_per_sphere = (
        total_xp
        / len(spheres)
    )

    lines = [
        "✨ <b>Досвід експедиції:</b>",
        f"• 🧙‍♂️ Герой: +{total_xp:g} XP"
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

    # -----------------------------------------------------
    # LEVEL UP
    # -----------------------------------------------------

    player_level_ups = (
        level_up_data.get(
            "player",
            []
        )
        if level_up_data
        else []
    )

    sphere_level_ups = (
        level_up_data.get(
            "spheres",
            []
        )
        if level_up_data
        else []
    )

    if player_level_ups:

        lines.append("")

        for level_up in player_level_ups:

            lines.append(
                "🌟 "
                f"<b>Рівень героя підвищено "
                f"до {level_up['new_level']}!</b>"
            )

    if sphere_level_ups:

        lines.append("")

        lines.append(
            "🌟 <b>Підвищення рівня сфер:</b>"
        )

        already_shown = set()

        for level_up in sphere_level_ups:

            key = level_up.get(
                "key"
            )

            if key in already_shown:

                continue

            already_shown.add(
                key
            )

            lines.append(
                f"• {level_up['emoji']} "
                f"<b>{level_up['name']}</b> → "
                f"рівень "
                f"<b>{level_up['new_level']}</b>"
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

    # =====================================================
    # ЗАХИСТ
    # =====================================================

    if not player:

        bot.send_message(
            message.chat.id,
            (
                "🐜 <b>Генерал Мураха:</b>\n\n"
                "Не вдалося знайти твій табір."
            ),
            parse_mode="HTML"
        )

        return

    # =====================================================
    # ОТРИМУЄМО АКТИВНУ ЕКСПЕДИЦІЮ
    # =====================================================

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
                "Час відправити когось "
                "на пошуки пригод."
            ),
            parse_mode="HTML",
            reply_markup=get_quests_menu()
        )

        return

    # =====================================================
    # РОЗРАХУНОК АКТИВНОГО ЧАСУ
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

    # =====================================================
    # НАГОРОДИ XP
    # =====================================================
    #
    # ЄДИНА СИСТЕМА:
    #
    # level
    # level_xp
    # level_max_xp
    #
    # + сфери:
    #
    # lvl
    # xp
    # max_xp
    #
    # НІЯКОГО xp_total.
    #
    # =====================================================

    level_up_data = add_xp_to_character(
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
    # СТАТИСТИКА
    # =====================================================

    update_statistics(
        player,
        expeditions_completed=1
    )

    statistics = player.get(
        "statistics"
    ) or {}

    # =====================================================
    # ОЧИЩАЄМО ЕКСПЕДИЦІЮ
    # =====================================================

    player["expeditions"] = []

    player["inventory"] = inventory

    # =====================================================
    # ЗНАЧЕННЯ ДЛЯ SUPABASE
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
            statistics
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
                "🐜 <b>Генерал Мураха:</b>\n\n"

                "Загін уже повернувся до табору, "
                "але журнал експедиції відмовляється "
                "підкорятися.\n\n"

                "⚠️ Результати не були збережені "
                "в базі даних.\n\n"

                "Експедицію не було остаточно "
                "закрито, тому спробуй натиснути "
                "«🏁 Завершити експедицію» ще раз."
            ),
            parse_mode="HTML",
            reply_markup=get_quests_menu()
        )

        return

    # =====================================================
    # ФОРМАТУЄМО ЧАС
    # =====================================================

    time_text = format_expedition_time(
        active_seconds
    )

    # =====================================================
    # ФОРМАТУЄМО ЗНАХІДКИ
    # =====================================================

    found_text = format_found_items(
        found_items
    )

    # =====================================================
    # ФОРМАТУЄМО XP
    # =====================================================

    xp_text = format_xp_report(
        total_xp,
        spheres,
        level_up_data
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
            "але повернулися з новими "
            "враженнями та досвідом.\n\n"
        )

    # =====================================================
    # XP
    # =====================================================

    report += (
        f"{xp_text}\n\n"
    )

    # =====================================================
    # ФІНАЛ
    # =====================================================

    report += (
        "🐜 Генерал струшує пил із карти, "
        "акуратно згортає її та додає:\n\n"

        "«Експедицію завершено. "
        "Загін готовий до наступного наказу.»"
    )

    # =====================================================
    # ВІДПРАВЛЯЄМО ЗВІТ
    # =====================================================

    bot.send_message(
        message.chat.id,
        report,
        parse_mode="HTML",
        reply_markup=get_quests_menu()
    )
