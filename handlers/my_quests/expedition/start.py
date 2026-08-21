from telebot import types


# =========================================================
# ГОЛОВНЕ МЕНЮ
# =========================================================

def get_main_menu():

    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    markup.row(
        types.KeyboardButton("🧙‍♂️ Персонаж"),
        types.KeyboardButton("🎒 Рюкзак")
    )

    markup.row(
        types.KeyboardButton("📖 Основний квест"),
        types.KeyboardButton("📝 Мої квести")
    )

    markup.row(
        types.KeyboardButton("✅ Виконати справу")
    )

    return markup


# =========================================================
# МЕНЮ "МОЇ КВЕСТИ"
# =========================================================

def get_quests_menu():

    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    markup.row(
        types.KeyboardButton("📜 Сувої"),
        types.KeyboardButton("🔄 Ритуали")
    )

    markup.row(
        types.KeyboardButton("🌱 Теплиця"),
        types.KeyboardButton("🧭 Експедиції")
    )

    markup.row(
        types.KeyboardButton("✅ Виконати справу")
    )

    markup.row(
        types.KeyboardButton("🔙 Назад")
    )

    return markup


# =========================================================
# СУВОЇ
# =========================================================

def get_scrolls_menu():

    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    markup.row(
        types.KeyboardButton("➕ Створити сувій"),
        types.KeyboardButton("🔥 Спалити сувій")
    )

    markup.row(
        types.KeyboardButton("📜 Виконати сувій")
    )

    markup.row(
        types.KeyboardButton("🔙 Назад до квестів")
    )

    return markup


# =========================================================
# РИТУАЛИ
# =========================================================

def get_rituals_menu():

    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    markup.row(
        types.KeyboardButton("➕ Створити ритуал"),
        types.KeyboardButton("🔥 Спалити ритуал")
    )

    markup.row(
        types.KeyboardButton("🔄 Провести ритуал")
    )

    markup.row(
        types.KeyboardButton("🔙 Назад до квестів")
    )

    return markup


# =========================================================
# ТЕПЛИЦЯ
# =========================================================

def get_greenhouse_menu():

    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    markup.row(
        types.KeyboardButton("🌱 Посадити рослину"),
        types.KeyboardButton("🪓 Вирвати баобаб")
    )

    markup.row(
        types.KeyboardButton("🌱 Завершити вирощування")
    )

    markup.row(
        types.KeyboardButton("📚 Архів теплиці")
    )

    markup.row(
        types.KeyboardButton("🔙 Назад до квестів")
    )

    return markup


# =========================================================
# ЕКСПЕДИЦІЇ
# =========================================================

def get_expedition_menu(active_expedition=None):

    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    # =====================================================
    # Є АКТИВНА ЕКСПЕДИЦІЯ
    # =====================================================

    if active_expedition:

        status = active_expedition.get(
            "status",
            "active"
        )

        # -------------------------------------------------
        # ЗАГІН НА ПРИВАЛІ
        # -------------------------------------------------

        if status == "paused":

            markup.row(
                types.KeyboardButton(
                    "▶️ Продовжити експедицію"
                )
            )

        # -------------------------------------------------
        # ЗАГІН ПРОДОВЖУЄ ЕКСПЕДИЦІЮ
        # -------------------------------------------------

        else:

            markup.row(
                types.KeyboardButton(
                    "🏕️ Зробити привал"
                )
            )

        # -------------------------------------------------
        # ЗАВЕРШЕННЯ
        # -------------------------------------------------

        markup.row(
            types.KeyboardButton(
                "🏁 Завершити експедицію"
            )
        )

    # =====================================================
    # НОВА ЕКСПЕДИЦІЯ
    # =====================================================

    else:

        # Тут навмисно НІЯКОЇ кнопки
        # "🐜 Відправити мурах в експедицію".
        #
        # Запуск нової експедиції тепер відбувається
        # безпосередньо через обробник "🧭 Експедиції".

        pass

    # =====================================================
    # НАЗАД
    # =====================================================

    markup.row(
        types.KeyboardButton(
            "🔙 Назад"
        )
    )

    return markup
