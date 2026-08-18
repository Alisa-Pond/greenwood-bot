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

    # -----------------------------------------------------
    # ВИКОНАТИ СПРАВУ
    # -----------------------------------------------------

    markup.row(
        types.KeyboardButton("✅ Виконати справу")
    )

    # -----------------------------------------------------
    # НАЗАД
    # -----------------------------------------------------

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
        types.KeyboardButton("➕ Створити сувій")
    )

    markup.row(
        types.KeyboardButton("🔥 Спалити сувій")
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
        types.KeyboardButton("➕ Створити ритуал")
    )

    markup.row(
        types.KeyboardButton("🔥 Спалити ритуал")
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
        types.KeyboardButton("🌱 Посадити рослину")
    )

    markup.row(
        types.KeyboardButton("🪓 Вирвати баобаб")
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
    """
    Клавіатура Експедицій.

    Якщо експедиції немає:
        🐜 Відправити мурах в експедицію

    Якщо експедиція активна:
        🏕️ Зробити привал
        🏁 Завершити експедицію

    Якщо експедиція на привалі:
        ▶️ Продовжити експедицію
        🏁 Завершити експедицію

    У будь-якому стані:
        🔙 Назад
    """

    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    # =====================================================
    # НЕМАЄ АКТИВНОЇ ЕКСПЕДИЦІЇ
    # =====================================================

    if not active_expedition:

        markup.row(
            types.KeyboardButton(
                "🐜 Відправити мурах в експедицію"
            )
        )

    # =====================================================
    # Є АКТИВНА ЕКСПЕДИЦІЯ
    # =====================================================

    else:

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
    # НАЗАД
    # =====================================================

    markup.row(
        types.KeyboardButton(
            "🔙 Назад"
        )
    )

    return markup
