import random

from services.config import bot
from services.database import get_player, update_player

from services.activity_utils import (
    get_title,
    get_xp,
    get_spheres,
    get_today,
    is_overdue,
    add_xp_to_character,
    update_statistics,
    build_back_button,
    send_level_up_notifications,
)

from services.conditions import get_world_conditions

from services.loot import (
    roll_loot_many,
    add_loot_to_inventory,
    group_loot,
    format_loot_text,
)


# =========================================================
# 🎲 ROLL КІЛЬКОСТІ ЛУТУ ДЛЯ СУВОЮ
# =========================================================
#
# КОЖЕН СУВІЙ МАЄ ВЛАСНИЙ ROLL.
#
# 90% → 0 предметів
# 7%  → 1 предмет
# 3%  → 2 предмети
#
# ЦЕ НЕ ROLL КОНКРЕТНОГО ПРЕДМЕТА.
#
# Якщо випало:
#
# 0 → нічого більше не робимо
# 1 → один roll предмета через loot.py
# 2 → два rolls предмета через loot.py
#
# =========================================================

def roll_scroll_loot_amount():

    return random.choices(
        [0, 1, 2],
        weights=[90, 7, 3],
        k=1
    )[0]


# =========================================================
# ВИКОНАННЯ СУВОЮ
# =========================================================

@bot.message_handler(
    func=lambda message:
        message.text == "📜 Виконати сувій"
)
def choose_scroll(message):

    user_id = str(
        message.from_user.id
    )

    player = get_player(
        user_id
    )

    scrolls = player.get(
        "scrolls"
    ) or []

    # =====================================================
    # НЕМАЄ СУВОЇВ
    # =====================================================

    if not scrolls:

        bot.send_message(
            message.chat.id,

            "🦇 <b>Марчелло🦇</b>\n"
            "📜 <b>Жодного активного сувою.</b>\n\n",

            parse_mode="HTML",

            reply_markup=build_back_button(),
        )

        return

    # =====================================================
    # СПИСОК АКТИВНИХ СУВОЇВ
    # =====================================================

    scroll_text = (
        "🦇 <b>Марчелло🦇</b>\n"
        "📜 <b>Активні сувої:</b>\n\n"
    )

    # =====================================================
    # ВАЖЛИВО:
    #
    # display_number = номер, який бачить користувач
    # scroll_index = реальний індекс у scrolls
    #
    # Тому користувач завжди бачить:
    #
    # 1.
    # 2.
    # 3.
    # 4.
    #
    # навіть якщо реальні індекси:
    #
    # 0, 1, 3, 7
    # =====================================================

    for display_number, scroll in enumerate(
        scrolls,
        start=1
    ):

        # -------------------------------------------------
        # СФЕРИ
        # -------------------------------------------------

        spheres = get_spheres(
            scroll
        )

        spheres_text = "".join(
            spheres
        )

        # -------------------------------------------------
        # XP
        # -------------------------------------------------

        xp = get_xp(
            scroll
        )

        # -------------------------------------------------
        # ДЕДЛАЙН
        # -------------------------------------------------

        deadline = (
            scroll.get(
                "deadline"
            )
            or "без дедлайну"
        )

        # -------------------------------------------------
        # ПЕРЕВІРКА ПРОСТРОЧЕННЯ
        # -------------------------------------------------

        deadline_overdue = is_overdue(
            scroll
        )

        # -------------------------------------------------
        # ПЕРЕВІРКА:
        # ДЕДЛАЙН СЬОГОДНІ
        # -------------------------------------------------

        deadline_today = False

        parsed_deadline = scroll.get(
            "deadline"
        )

        if parsed_deadline:

            from services.activity_utils import parse_deadline

            deadline_date = parse_deadline(
                parsed_deadline
            )

            if deadline_date:

                from datetime import datetime

                today = datetime.now().date()

                deadline_today = (
                    deadline_date.date()
                    == today
                )

        # -------------------------------------------------
        # ВОГНИК
        # -------------------------------------------------
        #
        # 🔥 якщо дедлайн сьогодні
        #
        # ⚠️ якщо сувій вже прострочений
        #
        # -------------------------------------------------

        if deadline_overdue:

            deadline_icon = "⚠️ "

        elif deadline_today:

            deadline_icon = "🔥 "

        else:

            deadline_icon = ""

        # -------------------------------------------------
        # НАЗВА
        # -------------------------------------------------

        title = get_title(
            scroll
        )

        # -------------------------------------------------
        # ФОРМАТ
        # -------------------------------------------------

        scroll_text += (
            f"<b>{display_number}.</b> "
            f"{deadline_icon}"
            f"{spheres_text} ; "
            f"{xp:g} ; "
            f"{deadline} ; "
            f"{title}\n"
        )

    # =====================================================
    # ІНСТРУКЦІЯ
    # =====================================================

    scroll_text += (
        "\n"
        "✍️ <b>Напиши номер сувою, який виконано.</b>\n"
        "Можна виконати одразу кілька через кому:\n\n"
        "<code>1</code>\n"
        "або\n"
        "<code>1, 3, 4</code>"
    )

    msg = bot.send_message(
        message.chat.id,

        scroll_text,

        parse_mode="HTML",

        reply_markup=build_back_button(),
    )

    bot.register_next_step_handler(
        msg,
        complete_scroll
    )


# =========================================================
# ПАРСИНГ НОМЕРІВ СУВОЇВ
# =========================================================

def parse_scroll_numbers(text):

    if not text:
        return None

    parts = text.split(",")

    numbers = []

    for part in parts:

        part = part.strip()

        if not part:
            return None

        try:

            number = int(
                part
            )

        except (
            ValueError,
            TypeError
        ):

            return None

        if number <= 0:

            return None

        numbers.append(
            number
        )

    # =====================================================
    # ЗАХИСТ ВІД ДУБЛІВ
    # =====================================================

    if len(numbers) != len(set(numbers)):

        return None

    return numbers


# =========================================================
# ОБРОБКА ВИБОРУ СУВОЇВ
# =========================================================

def complete_scroll(message):

    # =====================================================
    # НАЗАД
    # =====================================================

    if message.text == "🔙 Назад":

        from handlers.complete_activity import start_complete

        start_complete(
            message
        )

        return

    # =====================================================
    # ОТРИМУЄМО ГРАВЦЯ
    # =====================================================

    user_id = str(
        message.from_user.id
    )

    player = get_player(
        user_id
    )

    scrolls = player.get(
        "scrolls"
    ) or []

    # =====================================================
    # НЕМАЄ СУВОЇВ
    # =====================================================

    if not scrolls:

        bot.send_message(
            message.chat.id,

            "📜 Активних сувоїв більше немає.",

            reply_markup=build_back_button(),
        )

        return

    # =====================================================
    # ОТРИМУЄМО НОМЕРИ
    # =====================================================

    selected_numbers = parse_scroll_numbers(
        message.text.strip()
    )

    # =====================================================
    # НЕВІРНИЙ ФОРМАТ
    # =====================================================

    if not selected_numbers:

        bot.send_message(
            message.chat.id,

            "🦇 <b>Марчелло🦇</b>\n"
            "Я не зміг зрозуміти номери сувоїв.\n",

            parse_mode="HTML",

            reply_markup=build_back_button(),
        )

        bot.register_next_step_handler(
            message,
            complete_scroll
        )

        return

    # =====================================================
    # ПЕРЕВІРКА НОМЕРІВ
    # =====================================================

    invalid_numbers = [
        number
        for number in selected_numbers
        if not 1 <= number <= len(scrolls)
    ]

    if invalid_numbers:

        bot.send_message(
            message.chat.id,

            "🦇 <b>Марчелло🦇</b>\n"
            f"Такого номера немає.\n"
            f"Доступні номери: "
            f"<b>1–{len(scrolls)}</b>.",

            parse_mode="HTML",

            reply_markup=build_back_button(),
        )

        bot.register_next_step_handler(
            message,
            complete_scroll
        )

        return

    # =====================================================
    # ПЕРЕТВОРЮЄМО НОМЕРИ КОРИСТУВАЧА
    # НА РЕАЛЬНІ ІНДЕКСИ
    # =====================================================

    selected_indexes = [
        number - 1
        for number in selected_numbers
    ]

    # =====================================================
    # ОБРОБКА СУВОЇВ
    # =====================================================

    total_xp = 0.0

    completed_titles = []

    completed_count = 0

    all_character_level_ups = []

    loot_item_ids = []

    scroll_archive = (
        player.get(
            "scroll_archive"
        )
        or []
    )

    # =====================================================
    # УМОВИ СВІТУ
    # =====================================================

    world_conditions = get_world_conditions(
        player
    )

    # =====================================================
    # ОБРОБЛЯЄМО ВІД БІЛЬШОГО ІНДЕКСУ ДО МЕНШОГО
    #
    # Це потрібно, тому що після pop()
    # індекси елементів, які залишилися,
    # змінюються.
    # =====================================================

    for selected_index in sorted(
        selected_indexes,
        reverse=True
    ):

        scroll = scrolls[
            selected_index
        ]

        # -------------------------------------------------
        # ДАНІ СУВОЮ
        # -------------------------------------------------

        title = get_title(
            scroll
        )

        xp = get_xp(
            scroll
        )

        spheres = get_spheres(
            scroll
        )

        # -------------------------------------------------
        # XP ПЕРСОНАЖА + СФЕР
        # -------------------------------------------------

        level_up_data = add_xp_to_character(
            player,
            spheres,
            xp
        )

        # -------------------------------------------------
        # LEVEL UP
        # -------------------------------------------------

        if level_up_data:

            if isinstance(
                level_up_data,
                list
            ):

                all_character_level_ups.extend(
                    level_up_data
                )

            else:

                all_character_level_ups.append(
                    level_up_data
                )

        # =================================================
        # 🎲 ROLL КІЛЬКОСТІ ЛУТУ
        # =================================================
        #
        # КОЖЕН СУВІЙ МАЄ ВЛАСНИЙ НЕЗАЛЕЖНИЙ ROLL.
        #
        # 90% → 0 предметів
        # 7%  → 1 предмет
        # 3%  → 2 предмети
        #
        # =================================================

        loot_amount = roll_scroll_loot_amount()

        # =================================================
        # 🎁 ВИБІР КОНКРЕТНИХ ПРЕДМЕТІВ
        # =================================================
        #
        # Якщо випав 1 або 2 предмети,
        # loot.py визначає конкретні предмети
        # за їхніми вагами.
        #
        # ОКРЕМОЇ СИСТЕМИ RARITY НЕТ.
        #
        # =================================================

        if loot_amount > 0:

            rolled_items = roll_loot_many(
                loot_amount,
                world_conditions
            )

            if rolled_items:

                loot_item_ids.extend(
                    rolled_items
                )

        # -------------------------------------------------
        # АРХІВ
        # -------------------------------------------------

        completed_scroll = dict(
            scroll
        )

        completed_scroll[
            "completed"
        ] = True

        completed_scroll[
            "completed_date"
        ] = get_today()

        completed_scroll[
            "earned_xp"
        ] = xp

        scroll_archive.append(
            completed_scroll
        )

        # -------------------------------------------------
        # ВИДАЛЯЄМО СУВІЙ
        # -------------------------------------------------

        scrolls.pop(
            selected_index
        )

        # -------------------------------------------------
        # СТАТИСТИКА
        # -------------------------------------------------

        total_xp += xp

        completed_titles.append(
            title
        )

        completed_count += 1

    # =====================================================
    # ДОДАЄМО ЛУТ ДО ІНВЕНТАРЮ
    # =====================================================

    player[
        "inventory"
    ] = add_loot_to_inventory(
        player.get(
            "inventory"
        ) or [],
        loot_item_ids
    )

    # =====================================================
    # ОНОВЛЮЄМО PLAYER
    # =====================================================

    player[
        "scrolls"
    ] = scrolls

    player[
        "scroll_archive"
    ] = scroll_archive

    # =====================================================
    # СТАТИСТИКА
    # =====================================================

    update_statistics(
        player,
        completed_scrolls=completed_count
    )

    # =====================================================
    # SUPABASE
    # =====================================================

    update_player(
        user_id,
        {
            "level": player.get(
                "level",
                1
            ),

            "level_xp": player.get(
                "level_xp",
                0.0
            ),

            "level_max_xp": player.get(
                "level_max_xp",
                10.0
            ),

            "spheres": player.get(
                "spheres"
            ) or {},

            "scrolls": player.get(
                "scrolls"
            ) or [],

            "scroll_archive": player.get(
                "scroll_archive"
            ) or [],

            "statistics": player.get(
                "statistics"
            ) or {},

            "inventory": player.get(
                "inventory"
            ) or [],
        }
    )

    # =====================================================
    # LEVEL UP
    # =====================================================

    if all_character_level_ups:

        for level_up_data in all_character_level_ups:

            send_level_up_notifications(
                message.chat.id,
                level_up_data
            )

    # =====================================================
    # СПИСОК ВИКОНАНИХ СУВОЇВ
    # =====================================================

    titles_text = "\n".join(
        f"📜 {title}"
        for title in reversed(
            completed_titles
        )
    )

    # =====================================================
    # ЛУТ
    # =====================================================

    grouped_loot = group_loot(
        loot_item_ids
    )

    loot_text = format_loot_text(
        grouped_loot
    )

    # =====================================================
    # РЕЗУЛЬТАТ
    # =====================================================

    bot.send_message(
        message.chat.id,

        "🦇 <b>Марчелло ставить останню печатку.</b>\n\n"

        f"✨ Виконано сувоїв: "
        f"<b>{completed_count}</b>\n\n"

        f"{titles_text}\n\n"

        f"⭐ Загалом отримано: "
        f"<b>{total_xp:.1f} XP</b>"

        f"{loot_text}\n\n"

        "📚 Виконані сувої переміщено "
        "до <b>Архіву Грінвуду</b>.",

        parse_mode="HTML",

        reply_markup=build_back_button(),
    )
