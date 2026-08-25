from datetime import datetime
from zoneinfo import ZoneInfo


# =========================================================
# 🌲 УМОВИ СВІТУ ГРІНВУДУ
# =========================================================
#
# Цей файл визначає:
#
# 🌞 день
# 🌙 ніч
# 🌕 повня
# 📖 активну главу Основного квесту
# 📜 чи активний Основний квест
#
# Loot-система використовує ці умови,
# щоб визначити, які пули доступні.
#
# =========================================================


# =========================================================
# 🕰️ ЧАСОВИЙ ПОЯС
# =========================================================

GREENWOOD_TIMEZONE = ZoneInfo(
    "Europe/Kyiv"
)


# =========================================================
# 🌞 ДЕНЬ / 🌙 НІЧ
# =========================================================


DAY_START_HOUR = 9
NIGHT_START_HOUR = 21


def get_now():
    """
    Повертає поточний локальний час Грінвуду.
    """

    return datetime.now(
        GREENWOOD_TIMEZONE
    )


def is_day(now=None):
    """
    Перевіряє, чи зараз день.
    """

    if now is None:
        now = get_now()

    return (
        DAY_START_HOUR
        <= now.hour
        < NIGHT_START_HOUR
    )


def is_night(now=None):
    """
    Перевіряє, чи зараз ніч.
    """

    if now is None:
        now = get_now()

    return (
        now.hour >= NIGHT_START_HOUR
        or now.hour < DAY_START_HOUR
    )


def get_time_of_day(now=None):
    """
    Повертає:
        'day'
        або
        'night'
    """

    if is_night(now):
        return "night"

    return "day"


# =========================================================
# 🌕 ПОВНЯ
# =========================================================

# Відома дата повні:
# 2026-01-03 10:03 UTC
#
# Середня тривалість синодичного місяця:
# 29.530588853 доби
#
REFERENCE_FULL_MOON = datetime(
    2026,
    1,
    3,
    10,
    3
).replace(
    tzinfo=ZoneInfo("UTC")
)

LUNAR_CYCLE_DAYS = 29.530588853


def is_full_moon(now=None):
    """
    Перевіряє, чи сьогодні повня.

    Визначаємо повню з точністю до календарної доби
    за локальним часом Грінвуду.
    """

    if now is None:
        now = get_now()

    # Переводимо опорний час у той самий timezone
    # для коректного порівняння.

    reference = REFERENCE_FULL_MOON.astimezone(
        GREENWOOD_TIMEZONE
    )

    difference_days = (
        now - reference
    ).total_seconds() / 86400

    cycles = round(
        difference_days / LUNAR_CYCLE_DAYS
    )

    predicted_full_moon = (
        reference
        + __import__("datetime").timedelta(
            days=cycles * LUNAR_CYCLE_DAYS
        )
    )

    # Вважаємо повне місячне вікно
    # календарною добою.
    #
    # Тобто якщо точна повня припала
    # на сьогодні, умова активна весь день.

    return (
        predicted_full_moon.date()
        == now.date()
    )


# =========================================================
# 🌕 / 🌙 ТИП НОЧІ
# =========================================================

def is_full_moon_night(now=None):
    """
    Повня + ніч.

    Корисно для предметів, які можна отримати
    саме вночі під час повні.
    """

    if now is None:
        now = get_now()

    return (
        is_night(now)
        and is_full_moon(now)
    )


# =========================================================
# 📖 ОСНОВНИЙ КВЕСТ
# =========================================================

def get_main_quest(player):
    """
    Повертає дані Основного квесту гравця.

    Очікувана структура:

    {
        "chapter": 1,
        "completed": [],
        "current_task": null
    }

    Якщо дані відсутні або пошкоджені,
    повертаємо безпечне значення.
    """

    if not player:
        return {}

    main_quest = player.get(
        "main_quest",
        {}
    )

    if not isinstance(
        main_quest,
        dict
    ):
        return {}

    return main_quest


def get_current_chapter(player):
    """
    Повертає номер поточної глави.

    Наприклад:

        1
        2
        3

    Якщо глава не визначена,
    повертаємо None.
    """

    main_quest = get_main_quest(
        player
    )

    chapter = main_quest.get(
        "chapter"
    )

    try:

        if chapter is None:
            return None

        return int(
            chapter
        )

    except (
        TypeError,
        ValueError
    ):

        return None


def get_current_main_task(player):
    """
    Повертає поточне завдання Основного квесту.
    """

    main_quest = get_main_quest(
        player
    )

    return main_quest.get(
        "current_task"
    )


def has_active_main_quest(player):
    """
    Перевіряє, чи є зараз активне завдання
    Основного квесту.

    current_task != None
    означає, що квест зараз активний.
    """

    current_task = get_current_main_task(
        player
    )

    return (
        current_task is not None
    )


# =========================================================
# 📖 АКТИВНА ГЛАВА
# =========================================================

def is_chapter_active(
    player,
    chapter
):
    """
    Перевіряє, чи є в гравця
    активною конкретна глава.

    Наприклад:

        is_chapter_active(player, 1)

    """

    current_chapter = get_current_chapter(
        player
    )

    try:

        chapter = int(
            chapter
        )

    except (
        TypeError,
        ValueError
    ):

        return False

    return (
        current_chapter == chapter
        and has_active_main_quest(player)
    )


# =========================================================
# 🌲 УСІ ПОТОЧНІ УМОВИ
# =========================================================

def get_world_conditions(
    player,
    now=None
):
    """
    Повертає всі актуальні умови світу
    одним словником.

    Приклад:

    {
        "day": True,
        "night": False,
        "full_moon": False,
        "full_moon_night": False,
        "time_of_day": "day",
        "main_quest_active": True,
        "chapter": 1,
        "current_task": ...
    }

    Loot-система може використовувати
    цей словник для перевірки доступних пулів.
    """

    if now is None:
        now = get_now()

    day = is_day(
        now
    )

    night = is_night(
        now
    )

    full_moon = is_full_moon(
        now
    )

    main_quest_active = has_active_main_quest(
        player
    )

    chapter = get_current_chapter(
        player
    )

    current_task = get_current_main_task(
        player
    )

    return {

        # -------------------------------------------------
        # ЧАС
        # -------------------------------------------------

        "day": day,

        "night": night,

        "time_of_day": (
            "day"
            if day
            else "night"
        ),

        # -------------------------------------------------
        # МІСЯЦЬ
        # -------------------------------------------------

        "full_moon": full_moon,

        "full_moon_night": (
            full_moon
            and night
        ),

        # -------------------------------------------------
        # ОСНОВНИЙ КВЕСТ
        # -------------------------------------------------

        "main_quest_active": (
            main_quest_active
        ),

        "chapter": chapter,

        "current_task": current_task
    }


# =========================================================
# 🔍 ПЕРЕВІРКА УМОВИ
# =========================================================

def check_condition(
    condition,
    player,
    now=None
):
    """
    Перевіряє одну умову.

    Підтримувані умови:

        day
        night
        full_moon
        full_moon_night
        main_quest
        chapter_1
        chapter_2
        chapter_3
        ...

    """

    conditions = get_world_conditions(
        player,
        now
    )

    # -----------------------------------------------------
    # 🌞 ДЕНЬ
    # -----------------------------------------------------

    if condition == "day":

        return conditions[
            "day"
        ]

    # -----------------------------------------------------
    # 🌙 НІЧ
    # -----------------------------------------------------

    if condition == "night":

        return conditions[
            "night"
        ]

    # -----------------------------------------------------
    # 🌕 ПОВНЯ
    # -----------------------------------------------------

    if condition == "full_moon":

        return conditions[
            "full_moon"
        ]

    # -----------------------------------------------------
    # 🌕🌙 ПОВНЯ ВНОЧІ
    # -----------------------------------------------------

    if condition == "full_moon_night":

        return conditions[
            "full_moon_night"
        ]

    # -----------------------------------------------------
    # 📖 АКТИВНИЙ ОСНОВНИЙ КВЕСТ
    # -----------------------------------------------------

    if condition in (
        "main_quest",
        "main_quest_active"
    ):

        return conditions[
            "main_quest_active"
        ]

    # -----------------------------------------------------
    # 📚 ГЛАВА
    # -----------------------------------------------------

    if condition.startswith(
        "chapter_"
    ):

        chapter_text = (
            condition
            .replace(
                "chapter_",
                "",
                1
            )
        )

        try:

            chapter = int(
                chapter_text
            )

        except (
            TypeError,
            ValueError
        ):

            return False

        return is_chapter_active(
            player,
            chapter
        )

    # -----------------------------------------------------
    # ❌ НЕВІДОМА УМОВА
    # -----------------------------------------------------

    return False


# =========================================================
# 🧩 ПЕРЕВІРКА КІЛЬКОХ УМОВ
# =========================================================

def check_conditions(
    required_conditions,
    player,
    now=None
):
    """
    Перевіряє список умов.

    Усі умови повинні виконуватися.

    Наприклад:

        [
            "night",
            "full_moon"
        ]

    означає:

        🌙 ніч
        +
        🌕 повня

    """

    if not required_conditions:

        return True

    if isinstance(
        required_conditions,
        str
    ):

        required_conditions = [
            required_conditions
        ]

    for condition in required_conditions:

        if not check_condition(
            condition,
            player,
            now
        ):

            return False

    return True


# =========================================================
# 🧪 ДЛЯ ДЕБАГУ
# =========================================================

def debug_conditions(player):
    """
    Повертає зручний текст
    для перевірки умов під час розробки.
    """

    conditions = get_world_conditions(
        player
    )

    return (
        "🌲 Умови Грінвуду:\n\n"

        f"🌞 День: "
        f"{'так' if conditions['day'] else 'ні'}\n"

        f"🌙 Ніч: "
        f"{'так' if conditions['night'] else 'ні'}\n"

        f"🌕 Повня: "
        f"{'так' if conditions['full_moon'] else 'ні'}\n"

        f"🌕🌙 Повня вночі: "
        f"{'так' if conditions['full_moon_night'] else 'ні'}\n\n"

        f"📖 Основний квест: "
        f"{'активний' if conditions['main_quest_active'] else 'неактивний'}\n"

        f"📚 Глава: "
        f"{conditions['chapter']}\n"

        f"📜 Поточне завдання: "
        f"{conditions['current_task']}"
    )
