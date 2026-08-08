from telebot import types


# =========================
# Головне меню
# =========================

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


# =========================
# Меню "Мої квести"
# =========================

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


# =========================
# Сувої
# =========================

def get_scrolls_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    markup.row(
        types.KeyboardButton("➕ Створити сувій")
    )

    markup.row(
        types.KeyboardButton("🗑 Видалити сувій")
    )

    markup.row(
        types.KeyboardButton("📚 Архів сувоїв")
    )

    markup.row(
        types.KeyboardButton("🔙 Назад до квестів")
    )

    return markup


# =========================
# Ритуали
# =========================

def get_rituals_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    markup.row(
        types.KeyboardButton("➕ Створити ритуал")
    )

    markup.row(
        types.KeyboardButton("🗑 Видалити ритуал")
    )

    markup.row(
        types.KeyboardButton("📚 Архів ритуалів")
    )

    markup.row(
        types.KeyboardButton("🔙 Назад до квестів")
    )

    return markup


# =========================
# Теплиця
# =========================

def get_greenhouse_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    markup.row(
        types.KeyboardButton("🌱 Посадити рослину")
    )

    markup.row(
        types.KeyboardButton("🪴 Вирвати рослину")
    )

    markup.row(
        types.KeyboardButton("🔙 Назад до квестів")
    )

    return markup


# =========================
# Експедиції
# =========================

def get_expeditions_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    markup.row(
        types.KeyboardButton("🧭 Незабаром...")
    )

    markup.row(
        types.KeyboardButton("🔙 Назад до квестів")
    )

    return markup
