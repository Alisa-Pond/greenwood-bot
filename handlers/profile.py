from services.config import bot
import traceback
from telebot import types
from database import get_player, clean_skin_tones
from keyboards import get_main_menu
print("⚙️ Реєструємо хендлер /start у profile.py...")
@bot.message_handler(commands=['start'])
def welcome(message):
    print(f"🚀 Спрацювала команда /start для користувача {message.from_user.id}")
    try:
        user_id = str(message.from_user.id)
        print("⏳ Викликаємо get_player...")
        player = get_player(user_id)
        print(f"✅ Гравець отриман/створений: {player}")

        msg_1 = (
            "🌲 <b>Вітаємо у Greenwood!</b> 🌳\n\n"
            "Магічний ліс відкриває свої таємниці... А я — 🪷 <b>Lilly Pond</b> 🪷, твій магічний провідник у цьому затишному світі. "
            "Я допомагатиму тобі перетворювати твої реальні досягнення на справжню силу персонажа!"
        )
        bot.send_message(message.chat.id, msg_1, parse_mode="HTML")
        
        msg_2 = (
            "🔮 <b>Як влаштований наш світ:</b>\n"
            "Твій персонаж розвиває 5 основних сфер життя. Кожна з них стартує з 1 рівня і потребує <b>10 XP</b> для першого підвищення левелу.\n\n"
            "💪 <b>Здоров'я</b> — yoga, тренування, корисна їжа і тд.\n"
            "🧠 <b>Мудрість</b> — читання, навчання, вивчення мов, кодинг і тд.\n"
            "🎨 <b>Творчість</b> — малювання, гра на інструментах, в'язання і тд.\n"
            "💵 <b>Фінанси</b> — робота, планування бюджету і тд.\n"
            "🤝 <b>Зв'язки</b> — спілкування з близькими, допомога, турбота про рослини чи тварин.\n\n"
            "🎯 <b>Розділ Мої Квести:</b>\n"
            "Це твоє магічне джерело мотивації! Тут ти можеш структурувати свої цілі: створювати 📜 <b>Сувої</b> для "
            "справ із дедлайнами, налаштовувати щоденні 🔄 <b>Ритуали</b> для корисних звичок на кожен день або саджати великі цілі в "
            "🌱 <b>Теплиці</b>."
        )
        bot.send_message(message.chat.id, msg_2, parse_mode="HTML", reply_markup=get_main_menu())
        print("✅ Повідомлення успішно відправлено в Telegram!")

    except Exception as e:
        print("❌ ПОМИЛКА ВСЕРЕДИНІ WELCOME:")
        print(traceback.format_exc())

# --- ОБРОБНИКИ КНОПОК ПЕРСОНАЖА ТА РЮКЗАКА ---

@bot.message_handler(func=lambda message: message.text == "🧙‍♂️ Персонаж")
def show_profile(message):
    user_id = str(message.from_user.id)
    current_player = get_player(user_id)
    
    status = f"🧙‍♂️ <b>Лист Персонажа (Рівень {current_player['level']})</b>\n"
    status += f"✨ Загальний досвід: {float(current_player['xp_total']):.1f} XP\n"
    status += "────────────────────\n"
    
    for key, sphere in current_player["spheres"].items():
        status += f"{sphere['name']}: Лвл {sphere['lvl']} ({float(sphere['xp']):.1f}/{float(sphere['max_xp']):.1f} XP)\n"
        
    bot.send_message(message.chat.id, status, parse_mode="HTML")


@bot.message_handler(func=lambda message: message.text == "🎒 Рюкзак")
def show_inventory(message):
    user_id = str(message.from_user.id)
    current_player = get_player(user_id)
    
    if not current_player.get("inventory"):
        bot.send_message(message.chat.id, "🎒 <b>Твій рюкзак порожній.</b>", parse_mode="HTML")
    else:
        items_counts = {}
        for item in current_player["inventory"]:
            items_counts[item] = items_counts.get(item, 0) + 1
        inv_text = "🎒 <b>Вміст твого рюкзака:</b>\n\n"
        for item, count in items_counts.items():
            inv_text += f"• {item} x{count}\n"
        bot.send_message(message.chat.id, inv_text, parse_mode="HTML")


# --- РЕЖИМ ДОДАВАННЯ СПРАВИ (ШВИДКИЙ ЗВІТ) ---

def process_activity(message):
    # Тимчасова функція-заглушка (якщо справжня функція нижче або в іншому файлі)
    if message.text == "🔙 Назад":
        bot.send_message(message.chat.id, "Повертаємось у головне меню.", reply_markup=get_main_menu())
    else:
        bot.send_message(message.chat.id, "Звіт прийнято!", reply_markup=get_main_menu())


@bot.message_handler(func=lambda message: message.text == "➕ Додати Справу")
def add_activity_start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(types.KeyboardButton("🧙‍♂️ Завершити звіт"), types.KeyboardButton("🔙 Назад"))
    
    guide = (
        "➕ <b>Режим магічного звіту активовано!</b>\n\n"
        "Запиши свої діяння (по одному в рядку) у форматі:\n"
        "<code>[Емодзі] [Бали від 4 до 14] [Опис справи]</code>\n\n"
        "✨ <b>Доступні сфери сили:</b>\n"
        "• 💪 — Здоров'я\n"
        "• 🧠 — Мудрість\n"
        "• 🎨 — Творчість\n"
        "• 💵 — Фінанси\n"
        "• 🤝 — Зв'язки\n"
    )
    msg = bot.send_message(message.chat.id, guide, parse_mode="HTML", reply_markup=markup)
    bot.register_next_step_handler(msg, process_activity)
