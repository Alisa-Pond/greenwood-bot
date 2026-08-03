import time
import logging
import traceback
import telebot
from telebot import types

from services.config import bot
from services.database import get_player
from services.utils import clean_skin_tones
from keyboards import get_main_menu

logger = logging.getLogger(__name__)

print("⚙️ Реєструємо хендлери профілю та меню...")

# --- КОМАНДА /START ---

@bot.message_handler(commands=['start'])
def welcome(message):
    print(f"🚀 Спрацювала команда /start для користувача {message.from_user.id}")
    try:
        user_id = str(message.from_user.id)
        player = get_player(user_id)
        
        # Повідомлення 1: Знайомство з Лілі Понд (Лор мавки/пліткарки)
        msg_1 = (
            "🌲 <b>Вітаю у Грінвуді!</b> 🌳\n\n"
            "Я - 🪷 <b>Lilly Pond</b> 🪷! Сиджу на лататті, "
            "гріюся на сонечку й збираю найгарячіші плітки цього магічного лісу. "
            "Кажуть, ти тут, щоб перетворити свої реальні справи на справжній левелап? "
            "Я вже рознесла про це всім місцевим духам! ✨"
        )
        bot.send_message(message.chat.id, msg_1, parse_mode="HTML")
        
        time.sleep(2)
        
        # Повідомлення 2: Правила світу та квести
        msg_2 = (
            "🔮 <b>Лови короткий розклад, як тут усе влаштовано:</b>\n\n"
            "Твій персонаж прокачує <b>5 сфер сили</b>. Усі починають з 1 рівня, "
            "і для першого стрибка вгору тобі знадобиться <b>10 XP</b>:\n\n"
            "💪 <b>Здоров'я</b> - тренування, йога, пробіжки та смачна корисна їжа.\n"
            "🧠 <b>Мудрість</b> - книги, навчання, мови та код.\n"
            "🎨 <b>Творчість</b> - малювання, музика, в'язання та нові ідеї.\n"
            "💵 <b>Фінанси</b> - робота, бюджет та фінансова дисципліна.\n"
            "🤝 <b>Зв'язки</b> - тепло з близькими, турбота про тварин та підтримка друзяк.\n\n"
            "🎯 <b>Розділ Мої Квести:</b>\n"
            "Тут твої секретні сувої та цілі! Згортай справи у 📜 <b>Сувої</b> з дедлайнами, "
            "закручуй 🔄 <b>Ритуали</b> на кожен день або вирощуй великі мрії в 🌱 <b>Теплиці</b>."
        )
        bot.send_message(message.chat.id, msg_2, parse_mode="HTML", reply_markup=get_main_menu())
        print("✅ Привітальне меню успішно надіслано!")

    except Exception as e:
        print("❌ ПОМИЛКА ВСЕРЕДИНІ WELCOME:")
        print(traceback.format_exc())


# --- ОБРОБНИКИ КНОПОК ПЕРСОНАЖА ТА РЮКЗАКА ---

@bot.message_handler(func=lambda message: message.text == "🧙‍♂️ Персонаж")
def show_profile(message):
    user_id = str(message.from_user.id)
    current_player = get_player(user_id)
    
    status = f"🧙‍♂️ <b>Лист Персонажа (Рівень {current_player.get('level', 1)})</b>\n"
    status += f"✨ Загальний досвід: {float(current_player.get('xp_total', 0)):.1f} XP\n"
    status += "────────────────────\n"
    
    spheres = current_player.get("spheres", {})
    for key, sphere in spheres.items():
        status += f"{sphere['name']}: Лвл {sphere['lvl']} ({float(sphere['xp']):.1f}/{float(sphere['max_xp']):.1f} XP)\n"
        
    bot.send_message(message.chat.id, status, parse_mode="HTML")


@bot.message_handler(func=lambda message: message.text == "🎒 Рюкзак")
def show_inventory(message):
    user_id = str(message.from_user.id)
    current_player = get_player(user_id)
    inventory = current_player.get("inventory", [])
    
    if not inventory:
        bot.send_message(message.chat.id, "🎒 <b>Твій рюкзак порожній. Час здобути трофеї!</b>", parse_mode="HTML")
    else:
        items_counts = {}
        for item in inventory:
            items_counts[item] = items_counts.get(item, 0) + 1
        
        inv_text = "🎒 <b>Вміст твого рюкзака:</b>\n\n"
        for item, count in items_counts.items():
            inv_text += f"• {item} x{count}\n"
        bot.send_message(message.chat.id, inv_text, parse_mode="HTML")


# --- РЕЖИМ ДОДАВАННЯ СПРАВИ (ШВИДКИЙ ЗВІТ) ---

@bot.message_handler(func=lambda message: message.text == "➕ Додати Справу")
def add_activity_start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(types.KeyboardButton("🔙 Назад"))
    
    guide = (
        "➕ <b>Режим магічного звіту активовано!</b>\n\n"
        "Напиши мені, що з того, що ти робиш у реалі, дає тобі силу!\n"
        "Записуй справи по одній у рядку в такому форматі:\n"
        "<code>[Емодзі] [Бали від 4 до 14] [Опис справи]</code>\n\n"
        "<i>Приклад:</i>\n"
        "<code>🧠 10 Прочитав 20 сторінок книги</code>\n"
        "<code>💪 8 Зробив ранкову зарядку</code>\n\n"
        "✨ <b>Доступні сфери сили:</b>\n"
        "• 💪 — Здоров'я\n"
        "• 🧠 — Мудрість\n"
        "• 🎨 — Творчість\n"
        "• 💵 — Фінанси\n"
        "• 🤝 — Зв'язки"
    )
    msg = bot.send_message(message.chat.id, guide, parse_mode="HTML", reply_markup=markup)
    bot.register_next_step_handler(msg, process_activity)


def process_activity(message):
    if message.text == "🔙 Назад":
        bot.send_message(
            message.chat.id, 
            "Повертаємось до головного меню!", 
            parse_mode="Markdown", 
            reply_markup=get_main_menu()
        )
        return

    # Повідомлення про успішне отримання (тут підключатиметься функція обробки XP з services/utils.py)
    bot.send_message(
        message.chat.id, 
        f"✨ <b>Запис прийнято!</b>\n\n'<i>{message.text}</i>'\n\nЛілі вже занотовує твої досягнення у магічний сувій!", 
        parse_mode="HTML", 
        reply_markup=get_main_menu()
    )
