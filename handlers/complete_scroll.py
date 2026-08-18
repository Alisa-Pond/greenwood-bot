from datetime import datetime
from telebot import types

from services.config import bot
from services.database import get_player, update_player

from services.activity_utils import (
    get_title,
    get_xp,
    get_spheres,
    get_today,
    is_overdue,
    add_xp_to_player,
    add_xp_to_spheres,
    update_statistics,
    build_back_button,
    send_level_up_notifications,
)

from services.activity_loot import try_activity_loot


# =========================================================
# ДЕДЛАЙН ЗАКІНЧУЄТЬСЯ СЬОГОДНІ
# =========================================================

def deadline_is_today(scroll):

    deadline = scroll.get("deadline")

    if not deadline:
        return False

    value = str(deadline).strip()

    for fmt in (
        "%d.%m.%y",
        "%d.%m.%Y",
    ):

        try:

            deadline_date = datetime.strptime(
                value,
                fmt
            ).date()

            return (
                deadline_date
                == datetime.now().date()
            )

        except ValueError:

            continue

    return False


# =========================================================
# ФОРМАТУВАННЯ СУВОЮ
# =========================================================
#
# Формат:
#
# [Сфери] ; [Бали] ; [Дедлайн] ; [Назва справи]
#
# Наприклад:
#
# 💪🧠 ; 10 ; 18.08.26 ; Вивчити тему
#
# Якщо дедлайн сьогодні:
#
# 🔥💪🧠 ; 10 ; 18.08.26 ; Вивчити тему
#
# =========================================================

def format_scroll(scroll):

    spheres = get_spheres(scroll)

    spheres_text = "".join(
        spheres
    )

    if deadline_is_today(scroll):

        spheres_text = (
            "🔥" + spheres_text
        )

    xp = get_xp(scroll)

    deadline = (
        scroll.get("deadline")
        or "без дедлайну"
    )

    title = get_title(scroll)

    return (
        f"{spheres_text} ; "
        f"{xp:g} ; "
        f"{deadline} ; "
        f"{title}"
    )


# =========================================================
# ВИБІР СУВОЮ
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

    scrolls = (
        player.get("scrolls")
        or []
    )

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
    # СПИСОК СУВОЇВ
    # =====================================================

    text = (
        "📜 <b>Активні сувої</b>\n\n"
    )

    for index, scroll in enumerate(
        scrolls,
        start=1
    ):

        # Активні сувої показуються
        # звичайним текстом, без <code>

        text += (
            f"<b>{index}.</b> "
            f"{format_scroll(scroll)}\n"
        )

    text += (
        "\n🦇 <b>Марчелло:</b>\n"
        "«Назви номер сувою, який виконано.»\n\n"
        "Якщо виконано кілька одразу, "
        "вкажи їх через кому:\n"
        "<code>1, 3, 4</code>"
    )

    # =====================================================
    # КНОПКА НАЗАД
    # =====================================================

    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    markup.row(
        types.KeyboardButton(
            "🔙 Назад"
        )
    )

    msg = bot.send_message(
        message.chat.id,

        text,

        parse_mode="HTML",

        reply_markup=markup,
    )

    bot.register_next_step_handler(
        msg,
        complete_scroll
    )


# =========================================================
# ПАРСИНГ НОМЕРІВ
# =========================================================

def parse_scroll_numbers(text):

    # -----------------------------------------------------
    # Підтримуємо:
    #
    # 1
    # 1, 3, 4
    # 1 3 4
    # -----------------------------------------------------

    normalized = (
        text
        .replace(",", " ")
        .replace(";", " ")
    )

    parts = normalized.split()

    if not parts:

        raise ValueError(
            "Вкажи номер хоча б одного сувою."
        )

    numbers = []

    for part in parts:

        try:

            number = int(part)

        except ValueError:

            raise ValueError(
                "Номер сувою має бути цілим числом."
            )

        if number <= 0:

            raise ValueError(
                "Номер сувою має бути більшим за нуль."
            )

        if number not in numbers:

            numbers.append(number)

    return numbers


# =========================================================
# ВИКОНАННЯ СУВОЇВ
# =========================================================

def complete_scroll(message):

    # =====================================================
    # НАЗАД
    # =====================================================

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

    scrolls = (
        player.get("scrolls")
        or []
    )

    # =====================================================
    # ПЕРЕВІРКА НАЯВНОСТІ
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

    try:

        numbers = parse_scroll_numbers(
            message.text
        )

    except ValueError as error:

        bot.send_message(
            message.chat.id,

            "🦇 <b>Марчелло постукує пером "
            "по столу.</b>\n\n"

            f"❌ {error}\n\n"

            "Напиши номер сувою або кілька "
            "номерів через кому:\n\n"

            "<code>1</code>\n"
            "<code>1, 3, 4</code>",

            parse_mode="HTML",

            reply_markup=build_back_button(),
        )

        bot.register_next_step_handler(
            message,
            complete_scroll
        )

        return

    # =====================================================
    # ПЕРЕВІРЯЄМО НОМЕРИ
    # =====================================================

    invalid_numbers = [
        number
        for number in numbers
        if number > len(scrolls)
    ]

    if invalid_numbers:

        invalid_text = ", ".join(
            str(number)
            for number in invalid_numbers
        )

        bot.send_message(
            message.chat.id,

            "🦇 <b>Марчелло хмуриться.</b>\n\n"

            f"❌ Сувоїв з такими номерами немає: "
            f"<b>{invalid_text}</b>\n\n"

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
    # СОРТУЄМО ІНДЕКСИ У ЗВОРОТНОМУ ПОРЯДКУ
    # =====================================================
    #
    # Якщо вибрано:
    #
    # 1, 3
    #
    # спочатку видаляємо №3,
    # потім №1.
    #
    # Так індекси не зміщуються.
    #
    # =====================================================

    selected_indices = sorted(
        [number - 1 for number in numbers],
        reverse=True
    )

    # =====================================================
    # РЕЗУЛЬТАТИ
    # =====================================================

    completed_scrolls = []

    total_xp = 0.0

    all_level_ups = []

    all_sphere_level_ups = []

    all_loot = []

    # =====================================================
    # ОБРОБЛЯЄМО КОЖЕН СУВІЙ
    # =====================================================

    for selected_index in selected_indices:

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

        overdue = is_overdue(
            scroll
        )

        # -------------------------------------------------
        # XP ПЕРСОНАЖА
        # -------------------------------------------------

        character_level_ups = (
            add_xp_to_player(
                player,
                xp
            )
        )

        all_level_ups.extend(
            character_level_ups
        )

        # -------------------------------------------------
        # XP СФЕР
        # -------------------------------------------------

        sphere_level_ups = (
            add_xp_to_spheres(
                player,
                spheres,
                xp
            )
        )

        all_sphere_level_ups.extend(
            sphere_level_ups
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

        scroll_archive = (
            player.get(
                "scroll_archive"
            )
            or []
        )

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

        player[
            "scroll_archive"
        ] = scroll_archive

        # -------------------------------------------------
        # ЗБЕРІГАЄМО ДЛЯ ПОВІДОМЛЕННЯ
        # -------------------------------------------------

        completed_scrolls.append({
            "title": title,
            "xp": xp,
            "spheres": spheres,
            "overdue": overdue,
        })

        total_xp += xp

        # -------------------------------------------------
        # ВИДАЛЯЄМО СУВІЙ
        # -------------------------------------------------

        scrolls.pop(
            selected_index
        )

    # =====================================================
    # ОНОВЛЮЄМО АКТИВНІ СУВОЇ
    # =====================================================

    player[
        "scrolls"
    ] = scrolls

    # =====================================================
    # СТАТИСТИКА
    # =====================================================

    update_statistics(
        player,
        completed_scrolls=len(
            completed_scrolls
        )
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

    send_level_up_notifications(
        bot,
        message.chat.id,
        all_level_ups,
        all_sphere_level_ups
    )

    # =====================================================
    # ФОРМУЄМО РЕЗУЛЬТАТ
    # =====================================================

    result_text = (
        "🦇 <b>Марчелло ставить останню печатку.</b>\n\n"
    )

    if len(completed_scrolls) == 1:

        result_text += (
            "✨ <b>Сувій виконано!</b>\n\n"
        )

    else:

        result_text += (
            f"✨ <b>Виконано сувоїв: "
            f"{len(completed_scrolls)}</b>\n\n"
        )

    # =====================================================
    # СПИСОК ВИКОНАНИХ
    # =====================================================

    for scroll_data in reversed(
        completed_scrolls
    ):

        title = scroll_data[
            "title"
        ]

        xp = scroll_data[
            "xp"
        ]

        spheres = scroll_data[
            "spheres"
        ]

        overdue = scroll_data[
            "overdue"
        ]

        spheres_text = "".join(
            spheres
        )

        result_text += (
            f"📜 <b>{title}</b>\n"
            f"⭐ +<b>{xp:.1f} XP</b>\n"
            f"🎯 {spheres_text}\n"
        )

        if overdue:

            result_text += (
                "⚠️ Прострочений сувій\n"
            )

        result_text += "\n"

    # =====================================================
    # ЗАГАЛЬНИЙ XP
    # =====================================================

    if len(completed_scrolls) > 1:

        result_text += (
            f"⭐ <b>Разом: +{total_xp:.1f} XP</b>\n\n"
        )

    # =====================================================
    # ЛУТ
    # =====================================================

    if all_loot:

        result_text += (
            "🎁 <b>Знайдено:</b>\n"
        )

        for loot in all_loot:

            result_text += (
                f"• {loot}\n"
            )

        result_text += "\n"

    # =====================================================
    # АРХІВ
    # =====================================================

    result_text += (
        "📚 Виконані сувої переміщено "
        "до <b>Архіву Грінвуду</b>."
    )

    # =====================================================
    # ПОВІДОМЛЕННЯ
    # =====================================================

    bot.send_message(
        message.chat.id,

        result_text,

        parse_mode="HTML",

        reply_markup=build_back_button(),
    )
