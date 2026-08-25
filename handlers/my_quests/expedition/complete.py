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
    send_level_up_notifications
)


print("🏁 Реєструємо завершення експедицій...")


# =========================================================
# XP ЕКСПЕДИЦІЇ
# =========================================================
#
# За кожні ПОВНІ 30 хвилин активного часу:
#
# 30 хв → 5 XP
# 60 хв → 10 XP
# 90 хв → 15 XP
# 120 хв → 20 XP
#
# Час привалу не враховується.
# =========================================================

XP_PER_30_MINUTES = 5


# =========================================================
# ЙМОВІРНОСТІ ЛУТУ
# =========================================================
#
# За кожні повні 30 хвилин робиться
# одна спроба знайти предмет.
#
# 45% → common
# 15% → rare
# 4%  → very_rare
# 36% → нічого
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
# ВИПАДКОВИЙ ПРЕДМЕТ
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

        if not item_name:

            continue

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
    spheres
):

    if total_xp <= 0:

        return (
            "✨ За цей час загін не встиг "
            "здобути достатньо досвіду "
            "для нарахування XP.\n\n"

            "Потрібно щонайменше "
            "<b>30 хвилин активної експедиції</b>."
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
# ІНФОРМАЦІЯ ПРО РІВНІ
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
                "🐜 <b>Генерал Мураха:</b>\n\n"
                "Не вдалося знайти журнал персонажа."
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
    # АКТИВНИЙ ЧАС
    # =====================================================
    #
    # ВАЖЛИВО:
    #
    # Не беремо просто expedition["active_seconds"],
    # тому що під час активної експедиції там може
    # бути збережений старий час.
    #
    # calculate_active_seconds() додає поточну
    # активну сесію.
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
    # XP ПЕРСОНАЖУ + СФЕРАМ
    # =====================================================
    #
    # НЕ використовуємо xp_total.
    #
    # add_xp_to_character() змінює:
    #
    # level
    # level_xp
    # level_max_xp
    # spheres
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
    #
    # statistics НЕ видаляємо.
    #
    # Вона потрібна самері та іншій статистиці.
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

    player["expeditions"] = []

    player["inventory"] = inventory

    # =====================================================
    # ПІДГОТОВКА ДАНИХ ДО SUPABASE
    # =====================================================
    #
    # Тут НАРОЧНО немає:
    #
    # ❌ xp_total
    #
    # Є тільки поля, які реально існують
    # у твоїй поточній таблиці.
    # =====================================================

    update_data = {

        "level": player.get(
            "level",
            1
        ),

        "level_xp": float(
            player.get(
                "level_xp",
                0
            ) or 0
        ),

        "level_max_xp": float(
            player.get(
                "level_max_xp",
                10
            ) or 10
        ),

        "spheres": player.get(
            "spheres",
            {}
        ),

        "inventory": player.get(
            "inventory",
            []
        ),

        "expeditions": [],

        "statistics": statistics
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

                "Загін повернувся до табору, "
                "але виникла проблема із журналом "
                "експедиції.\n\n"

                "⚠️ Результати експедиції "
                "не вдалося надійно зберегти.\n\n"

                "Я НЕ завершив запис експедиції "
                "в пам'яті табору. Спробуй ще раз."
            ),
            parse_mode="HTML",
            reply_markup=get_expedition_menu(
                expedition
            )
        )

        return

    # =====================================================
    # ФОРМУЄМО РЕЗУЛЬТАТ
    # =====================================================

    time_text = format_expedition_time(
        active_seconds
    )

    found_text = format_found_items(
        found_items
    )

    xp_text = format_xp_report(
        total_xp,
        spheres
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
    # ФІНАЛЬНА ФРАЗА
    # =====================================================

    report += (
        "🐜 Генерал струшує пил із карти, "
        "акуратно згортає її та додає:\n\n"

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
    # ОКРЕМІ ПОВІДОМЛЕННЯ LEVEL UP
    # =====================================================
    #
    # Вони використовують готову систему
    # activity_utils.py.
    #
    # Основний звіт уже містить коротку інформацію
    # про level up, а тут надсилається повне
    # сюжетне повідомлення Марчелло.
    # =====================================================

    send_level_up_notifications(
        message.chat.id,
        level_up_data
    )
