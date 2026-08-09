from telebot import types


# ==================================================
# ГОЛОВНЕ МЕНЮ
# ==================================================

def get_main_menu():

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

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


# ==================================================
# МЕНЮ "МОЇ КВЕСТИ"
# ==================================================

def get_quests_menu():

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    markup.row(
        types.KeyboardButton("📜 Сувої"),
        types.KeyboardButton("🔄 Ритуали")
    )

    markup.row(
        types.KeyboardButton("🌱 Теплиця"),
        types.KeyboardButton("🧭 Експедиції")
    )

    markup.row(
        types.KeyboardButton("🔙 Назад")
    )

    return markup


# ==================================================
# СУВОЇ
# ==================================================

def get_scrolls_menu():

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

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


# ==================================================
# РИТУАЛИ
# ==================================================

def get_rituals_menu():

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

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


# ==================================================
# ТЕПЛИЦЯ
# ==================================================

def get_greenhouse_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

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


# ==================================================
# ЕКСПЕДИЦІЇ
# ==================================================

def get_expeditions_menu():

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    markup.row(
        types.KeyboardButton("🧭 Незабаром...")
    )

    markup.row(
        types.KeyboardButton("🔙 Назад до квестів")
    )

    return markup
