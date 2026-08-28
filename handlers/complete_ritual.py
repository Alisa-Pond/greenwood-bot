from datetime import datetime
import random

from telebot import types

from services.config import bot
from services.database import get_player, update_player

from services.activity_utils import (
    get_title,
    get_xp,
    get_spheres,
    get_today,
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
# ДНІ ТИЖНЯ
# =========================================================

WEEKDAYS = [
    "пн",
    "вт",
    "ср",
    "чт",
    "пт",
    "сб",
    "нд",
]


# =========================================================
# 🎲 ROLL КІЛЬКОСТІ ЛУТУ ДЛЯ РИТУАЛУ
# =========================================================
#
# КОЖЕН РИТУАЛ МАЄ ВЛАСНИЙ ROLL.
#
# 85% → 0 предметів
# 10% → 1 предмет
# 5%  → 2 предмети
#
# ЦЕ НЕ ROLL КОНКРЕТНОГО ПРЕДМЕТА.
#
# Якщо випало:
#
# 0 → нічого більше не робимо
# 1 → один roll предмета через loot.py
# 2 → два незалежні rolls предмета через loot.py
#
# =========================================================

def roll_ritual_loot_amount():

    return random.choices(
        [0, 1, 2],
        weights=[85, 10, 5],
        k=1
    )[0]


# =========================================================
# ПЕРЕВІРКА ДНЯ РИТУАЛУ
# =========================================================

def ritual_is_for_today(ritual):

    # -----------------------------------------------------
    # ЩОДЕННИЙ РИТУАЛ
    # -----------------------------------------------------

    if ritual.get("daily") is True:

        return True

    days = ritual.get("days") or []

    if not isinstance(days, list):

        return False

    today = datetime.now().weekday()

    return (
        today in days
        or WEEKDAYS[today] in days
    )


# =========================================================
# ФОРМАТ РИТУАЛУ ДЛЯ ВІДОБРАЖЕННЯ
# =========================================================
#
# Формат:
#
# [Сфери] ; [Бали] ; [Дні] ; [Назва справи]
#
# =========================================================

def format_ritual(ritual):

    spheres = get_spheres(
        ritual
    )

    spheres_text = "".join(
        spheres
    )

    xp = get_xp(
        ritual
    )

    days = ritual.get(
        "days"
    ) or []

    # -----------------------------------------------------
    # ДНІ
    # -----------------------------------------------------

    if ritual.get("daily") is True:

        days_text = "щодня"

    elif isinstance(days, list):

        formatted_days = []

        for day in days:

            if isinstance(day, int):

                if 0 <= day < len(WEEKDAYS):

                    formatted_days.append(
                        WEEKDAYS[day]
                    )

            else:

                formatted_days.append(
                    str(day)
                )

        days_text = " ".join(
            formatted_days
        )

        if not days_text:

            days_text = "—"

    else:

        days_text = "—"

    title = get_title(
        ritual
    )

    return (
        f"{spheres_text} ; "
        f"{xp:g} ; "
        f"{days_text} ; "
        f"{title}"
    )


# =========================================================
# ВИБІР РИТУАЛУ
# =========================================================

@bot.message_handler(
    func=lambda message:
        message.text == "🔄 Провести ритуал"
)
def choose_ritual(message):

    user_id = str(
        message.from_user.id
    )

    player = get_player(
        user_id
    )

    rituals = player.get(
        "rituals"
    ) or []

    if not rituals:

        bot.send_message(
            message.chat.id,

            "🦇 <b>Марчелло🦇</b>\n"
            "🔄 <b>Жодного активного ритуалу.</b>\n\n"
            "Ліс сьогодні напрочуд тихий. 🌲",

            parse_mode="HTML",

            reply_markup=build_back_button(),
        )

        return

    # =====================================================
    # РИТУАЛИ, ЯКІ МОЖНА ВИКОНАТИ СЬОГОДНІ
    # =====================================================

    available = []

    for index, ritual in enumerate(rituals):

        if ritual_is_for_today(
            ritual
        ):

            available.append(
                (
                    index,
                    ritual
                )
            )

    if not available:

        bot.send_message(
            message.chat.id,

            "🦇 <b>Марчелло🦇</b>\n"
            "💤 <b>Сьогодні жоден ритуал "
            "не чекає на виконання.</b>\n\n",

            parse_mode="HTML",

            reply_markup=build_back_button(),
        )

        return

    # =====================================================
    # ПОКАЗУЄМО РИТУАЛИ
    # =====================================================

    text = (
        "🦇 <b>Марчелло🦇</b>\n"
        "« <b>Сьогоднішні ритуали:</b>\n\n"
    )

    for display_number, (
        ritual_index,
        ritual
    ) in enumerate(
        available,
        start=1
    ):

        text += (
            f"<b>{display_number}.</b> "
            f"{format_ritual(ritual)}\n"
        )

    text += (
        "\n✏️ Напиши номер ритуалу "
        "або декілька через кому.»\n« "
    )

    # =====================================================
    # КЛАВІАТУРА
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
        complete_ritual
    )


# =========================================================
# ПАРСИНГ НОМЕРІВ РИТУАЛІВ
# =========================================================

def parse_ritual_numbers(text):

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

    # -----------------------------------------------------
    # ПРИБИРАЄМО ДУБЛІКАТИ
    # -----------------------------------------------------

    unique_numbers = []

    for number in numbers:

        if number not in unique_numbers:

            unique_numbers.append(
                number
            )

    return unique_numbers


# =========================================================
# ВИКОНАННЯ РИТУАЛУ / РИТУАЛІВ
# =========================================================

def complete_ritual(message):

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

    rituals = player.get(
        "rituals"
    ) or []

    # =====================================================
    # ОТРИМУЄМО НОМЕРИ
    # =====================================================

    selected_numbers = parse_ritual_numbers(
        message.text.strip()
    )

    if not selected_numbers:

        bot.send_message(
            message.chat.id,

            "🦇 <b>Марчелло🦇</b>\n"
            "« <b>Не вдалося розпізнати номери.</b>\n\n"
            "Напиши один номер або декілька через кому.\n"
            "Наприклад: <b>1, 2</b>»",

            parse_mode="HTML",
        )

        choose_ritual(
            message
        )

        return

    # =====================================================
    # ФОРМУЄМО ТОЙ САМИЙ СПИСОК,
    # ЯКИЙ БАЧИТЬ КОРИСТУВАЧ
    # =====================================================

    available = []

    for index, ritual in enumerate(rituals):

        if ritual_is_for_today(
            ritual
        ):

            available.append(
                (
                    index,
                    ritual
                )
            )

    # =====================================================
    # ПЕРЕВІРКА НОМЕРІВ
    # =====================================================

    invalid_numbers = [
        number
        for number in selected_numbers
        if not 1 <= number <= len(available)
    ]

    if invalid_numbers:

        bot.send_message(
            message.chat.id,

            "🦇 <b>Марчелло🦇</b>\n"
            "« <b>Не вдалося знайти "
            "один або декілька ритуалів.</b>\n\n"
            f"Доступні номери: "
            f"<b>1–{len(available)}</b>.\n\n"
            "Перевір номери та спробуй ще раз.»",

            parse_mode="HTML",
        )

        choose_ritual(
            message
        )

        return

    # =====================================================
    # ПЕРЕТВОРЮЄМО НОМЕР КОРИСТУВАЧА
    # НА РЕАЛЬНИЙ ІНДЕКС У rituals
    # =====================================================

    selected_indices = []

    for number in selected_numbers:

        ritual_index = available[
            number - 1
        ][0]

        selected_indices.append(
            ritual_index
        )

    # =====================================================
    # ДАНІ
    # =====================================================

    today = get_today()

    ritual_archive = (
        player.get(
            "ritual_archive"
        )
        or []
    )

    completed_rituals = []

    total_xp = 0.0

    total_completed = 0

    level_up_data_list = []

    # -----------------------------------------------------
    # УСІ ПРЕДМЕТИ, ОТРИМАНІ ЦИМ ВИКОНАННЯМ
    # -----------------------------------------------------

    loot_item_ids = []

    # =====================================================
    # 🌲 УМОВИ СВІТУ
    # =====================================================
    #
    # Визначаємо їх один раз на початку виконання.
    #
    # Саме ці умови передаємо в loot.py.
    #
    # Отже:
    #
    # 🌞 день
    # 🌙 ніч
    # 🌕 повня
    # 📖 активний квест
    # 📚 глава
    #
    # враховуються під час roll предмета.
    #
    # =====================================================

    world_conditions = get_world_conditions(
        player
    )

    # =====================================================
    # ОБРОБКА КОЖНОГО РИТУАЛУ
    # =====================================================

    for selected_index in selected_indices:

        ritual = rituals[
            selected_index
        ]

        # -------------------------------------------------
        # ПЕРЕВІРКА ДНЯ
        # -------------------------------------------------

        if not ritual_is_for_today(
            ritual
        ):

            continue

        # -------------------------------------------------
        # ПЕРЕВІРКА ПОВТОРНОГО ВИКОНАННЯ
        # -------------------------------------------------

        if ritual.get(
            "last_completed"
        ) == today:

            continue

        # -------------------------------------------------
        # ДАНІ РИТУАЛУ
        # -------------------------------------------------

        title = get_title(
            ritual
        )

        xp = get_xp(
            ritual
        )

        spheres = get_spheres(
            ritual
        )

        # -------------------------------------------------
        # XP ГЕРОЯ + XP СФЕР
        # -------------------------------------------------

        level_up_data = add_xp_to_character(
            player,
            spheres,
            xp
        )

        level_up_data_list.append(
            level_up_data
        )

        # =================================================
        # 🎲 ROLL КІЛЬКОСТІ ЛУТУ
        # =================================================
        #
        # КОЖЕН РИТУАЛ МАЄ ОКРЕМИЙ ROLL.
        #
        # Наприклад:
        #
        # Ритуал 1 → 1 предмет
        # Ритуал 2 → 0 предметів
        # Ритуал 3 → 2 предмети
        #
        # Загалом = 3 предмети.
        #
        # Кожен ритуал кидає свій незалежний roll.
        #
        # =================================================

        loot_amount = roll_ritual_loot_amount()

        # =================================================
        # 🎁 ВИБІР КОНКРЕТНИХ ПРЕДМЕТІВ
        # =================================================
        #
        # Якщо loot_amount == 1:
        # один roll предмета через loot.py.
        #
        # Якщо loot_amount == 2:
        # два rolls предмета через loot.py.
        #
        # Який саме предмет випаде,
        # визначається вагами в loot.py.
        #
        # Окремого roll_rarity() більше немає.
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

        completed_ritual = dict(
            ritual
        )

        completed_ritual[
            "completed_date"
        ] = today

        completed_ritual[
            "earned_xp"
        ] = xp

        ritual_archive.append(
            completed_ritual
        )

        # -------------------------------------------------
        # ОНОВЛЮЄМО РИТУАЛ
        # -------------------------------------------------

        ritual[
            "last_completed"
        ] = today

        rituals[
            selected_index
        ] = ritual

        # -------------------------------------------------
        # РЕЗУЛЬТАТ
        # -------------------------------------------------

        completed_rituals.append(
            {
                "title": title,
                "xp": xp,
                "spheres": spheres,
            }
        )

        total_xp += xp

        total_completed += 1

    # =====================================================
    # ЯКЩО ЖОДЕН РИТУАЛ НЕ БУВ ВИКОНАНИЙ
    # =====================================================

    if total_completed == 0:

        bot.send_message(
            message.chat.id,

            "🦇 <b>Марчелло🦇</b>\n"
            "<b>Жоден із вибраних ритуалів "
            "не вдалося провести.</b>\n\n"
            "Переконайся, що вони доступні сьогодні "
            "та чи не були вже виконані.",

            parse_mode="HTML",
        )

        choose_ritual(
            message
        )

        return

    # =====================================================
    # 🎒 ДОДАЄМО ЛУТ ДО ІНВЕНТАРЮ
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
    # ЗБЕРІГАЄМО ЗМІНИ
    # =====================================================

    player[
        "rituals"
    ] = rituals

    player[
        "ritual_archive"
    ] = ritual_archive

    # =====================================================
    # СТАТИСТИКА
    # =====================================================

    update_statistics(
        player,
        completed_rituals=total_completed
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

            "rituals": player.get(
                "rituals"
            ) or [],

            "ritual_archive": player.get(
                "ritual_archive"
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

    for level_up_data in level_up_data_list:

        send_level_up_notifications(
            message.chat.id,
            level_up_data
        )

    # =====================================================
    # ФІНАЛЬНЕ ПОВІДОМЛЕННЯ
    # =====================================================

    if total_completed == 1:

        result_text = (
            "🗯 <b>Ритуал проведено!</b>\n\n"
        )

    else:

        result_text = (
            "🗯 <b>Ритуали проведено!</b>\n\n"
        )

    for completed in completed_rituals:

        spheres_text = " ".join(
            completed["spheres"]
        )

        result_text += (
            f"🔄 <b>{completed['title']}</b>\n"
            f"⭐ Отримано: "
            f"<b>{completed['xp']:.1f} XP</b>\n"
            f"🎯 Сфери: {spheres_text}\n\n"
        )

    # =====================================================
    # 🎁 ЛУТ
    # =====================================================

    grouped_loot = group_loot(
        loot_item_ids
    )

    if grouped_loot:

        result_text += format_loot_text(
            grouped_loot
        )

        result_text += "\n"

    # =====================================================
    # АРХІВ
    # =====================================================

    result_text += (
        "🔄 Запис збережено"
            if total_completed > 1
            else "🔄 Запис збережено"
        )
    

    # =====================================================
    # СПОВІЩЕННЯ ПРО УСПІШНЕ ВИКОНАННЯ
    # =====================================================

    bot.send_message(
        message.chat.id,

        result_text,

        parse_mode="HTML",
    )

    # =====================================================
    # ПОВЕРТАЄМОСЯ В МЕНЮ
    # «✅ ВИКОНАТИ СПРАВУ»
    # =====================================================

    from handlers.complete_activity import start_complete

    start_complete(
        message
    )
