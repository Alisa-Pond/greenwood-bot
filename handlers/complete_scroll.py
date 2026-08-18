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

from services.activity_loot import try_activity_loot


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

            "📜 <b>Жодного активного сувою.</b>\n\n"
            "Марчелло поки не має чим тебе завантажити. 🦇",

            parse_mode="HTML",

            reply_markup=build_back_button(),
        )

        return

    # =====================================================
    # СПИСОК АКТИВНИХ СУВОЇВ
    # =====================================================

    scroll_text = (
        "📜 <b>Активні сувої:</b>\n\n"
    )

    for index, scroll in enumerate(scrolls):

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
        # ВОГНИК, ЯКЩО ДЕДЛАЙН СЬОГОДНІ
        # -------------------------------------------------

        deadline_overdue = is_overdue(
            scroll
        )

        # Перевіряємо саме дедлайн сьогодні.
        # is_overdue() повертає True лише після дедлайну,
        # тому окремо визначаємо дату дедлайну.

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

        fire = (
            "🔥 "
            if deadline_today
            else ""
        )

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
            f"{index + 1}. "
            f"{fire}"
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
        "Можна виконати одразу кілька:\n\n"
        "<code>1</code>\n"
        "або\n"
        "<code>1 3 4</code>"
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
# ОБРОБКА ВИБОРУ СУВОЇВ
# =========================================================

def complete_scroll(message):

    if message.text == "🔙 Назад":

        from handlers.complete_activity import start_complete

        start_complete(
            message
        )

        return

    user_id = str(
        message.from_user.id
    )

    player = get_player(
        user_id
    )

    scrolls = player.get(
        "scrolls"
    ) or []

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

    try:

        numbers = message.text.split()

        if not numbers:

            raise ValueError

        selected_indexes = []

        for number in numbers:

            if not number.isdigit():

                raise ValueError

            index = int(
                number
            ) - 1

            if not 0 <= index < len(scrolls):

                raise ValueError

            selected_indexes.append(
                index
            )

        # -------------------------------------------------
        # ЗАХИСТ ВІД ПОВТОРІВ
        # -------------------------------------------------

        if len(
            selected_indexes
        ) != len(
            set(selected_indexes)
        ):

            raise ValueError

    except (
        ValueError,
        AttributeError
    ):

        bot.send_message(
            message.chat.id,

            "🦇 <b>Марчелло піднімає брову.</b>\n\n"

            "Я не зміг зрозуміти номери сувоїв.\n\n"

            "Напиши, наприклад:\n"
            "<code>1</code>\n"
            "або\n"
            "<code>1 3 4</code>",

            parse_mode="HTML",

            reply_markup=build_back_button(),
        )

        bot.register_next_step_handler(
            message,
            complete_scroll
        )

        return

    # =====================================================
    # ОБРОБКА СУВОЇВ
    # =====================================================

    total_xp = 0.0

    completed_titles = []

    completed_count = 0

    all_sphere_level_ups = []

    all_character_level_ups = []

    all_loot = []

    scroll_archive = (
        player.get(
            "scroll_archive"
        )
        or []
    )

    # -----------------------------------------------------
    # ОБРОБЛЯЄМО ВІД БІЛЬШОГО ІНДЕКСУ ДО МЕНШОГО
    #
    # Щоб pop() не зміщував інші індекси.
    # -----------------------------------------------------

    for selected_index in sorted(
        selected_indexes,
        reverse=True
    ):

        scroll = scrolls[
            selected_index
        ]

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
        # XP ПЕРСОНАЖА
        # -------------------------------------------------

        level_up_data = add_xp_to_character(
            player,
            spheres,
            xp
        )

        # -------------------------------------------------
        # ЗБЕРІГАЄМО LEVEL UP
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

        # -------------------------------------------------
        # ЛУТ
        # -------------------------------------------------

        loot = try_activity_loot(
            player
        )

        if loot:

            all_loot.append(
                loot
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
        # ЗБЕРІГАЄМО ДАНІ
        # -------------------------------------------------

        total_xp += xp

        completed_titles.append(
            title
        )

        completed_count += 1

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
    #
    # ВАЖЛИВО:
    # send_level_up_notifications()
    # приймає ТІЛЬКИ:
    #
    # chat_id
    # level_up_data
    #
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

    loot_text = ""

    if all_loot:

        loot_text = (
            "\n🎁 <b>Знайдено:</b>\n"
            + "\n".join(
                f"• {loot}"
                for loot in all_loot
            )
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
