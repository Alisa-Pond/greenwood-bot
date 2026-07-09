import telebot
import json
from telebot import types
import os
import random
import time
import re
from threading import Thread
from flask import Flask

app = Flask('')

@app.route('/')
def home():
    return "Greenwood Chronicles is alive!"

def run_server():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# 🎫 ВСТАВ СВІЙ ТОКЕН СЮДИ
bot = telebot.TeleBot("import os
bot = telebot.TeleBot(os.environ.get("BOT_TOKEN", "no_local_token"))

DATA_FILE = "players_database.json"

def load_data():
    """Завантажує всю картотеку з файлу."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(data):
    """Зберігає всю картотеку у файл."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def create_new_player():
    """Повертає чистий шаблон гравця 1-го рівня."""
    return {
        "level": 1,
        "xp_total": 0.0,
        "inventory": [],
        "spheres": {
            "health": {"name": "Здоров'я", "emoji": "💪", "lvl": 1, "xp": 0.0, "max_xp": 10.0},
            "mind": {"name": "Мудрість", "emoji": "🧠", "lvl": 1, "xp": 0.0, "max_xp": 10.0},
            "art": {"name": "Творчість", "emoji": "🎨", "lvl": 1, "xp": 0.0, "max_xp": 10.0},
            "money": {"name": "Фінанси", "emoji": "💵", "lvl": 1, "xp": 0.0, "max_xp": 10.0},
            "links": {"name": "Зв'язки", "emoji": "🤝", "lvl": 1, "xp": 0.0, "max_xp": 10.0}
        }
    }

# Ігрова структура персонажа (досвід тепер може бути дробовим)
player = {
    "level": 1,
    "xp_total": 0.0,
    "inventory": [],
    "spheres": {
        "health": {"name": "💪 Здоров'я", "xp": 0.0, "max_xp": 10.0, "lvl": 1, "emoji": "💪"},
        "mind": {"name": "🧠 Мудрість", "xp": 0.0, "max_xp": 10.0, "lvl": 1, "emoji": "🧠"},
        "art": {"name": "🎨 Творчість", "xp": 0.0, "max_xp": 10.0, "lvl": 1, "emoji": "🎨"},
        "finance": {"name": "💵 Фінанси", "xp": 0.0, "max_xp": 10.0, "lvl": 1, "emoji": "💵"},
        "social": {"name": "🤝 Зв'язки", "xp": 0.0, "max_xp": 10.0, "lvl": 1, "emoji": "🤝"}
    }
}

# Шанс 0.2% на кожен артефакт (0.002)
LOOT_CHANCE = 0.002
POSSIBLE_LOOT = [
    "🧪 Настій Бадьорості",
    "📜 Стародавній Сувій",
    "💎 Кристал Натхнення",
    "🔑 Мідний Ключ"
]

def get_main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(types.KeyboardButton("🧙‍♂️ Персонаж"), types.KeyboardButton("🎒 Рюкзак"))
    markup.row(types.KeyboardButton("📜 Основний квест"), types.KeyboardButton("🎯 Мої Квести"))
    markup.row(types.KeyboardButton("➕ Додати Справу"))
    return markup

@bot.message_handler(commands=['start'])
def welcome(message):
    # Повідомлення 1: Привітання та знайомство з Лілі-Понд
    msg_1 = (
        "🌲 **Вітаємо у Greenwood Chronicles!** 🌲\n\n"
        "Магічний ліс відкриває свої таємниці... А я — **Lilly Pond**, твій магічний провідник у цьому затишному світі. "
        "Я допомагатиму тобі перетворювати твої реальні  досягнення на справжню силу персонажа!"
    )
    bot.send_message(message.chat.id, msg_1, parse_mode="Markdown")
    
    # Затримка 3 секунди
    time.sleep(3)
    
    # Повідомлення 2: Детальна інструкція та сфери життя
    msg_2 = (
        "🔮 **Як влаштований наш світ:**\n"
        "Твій персонаж розвиває 5 основних сфер життя. Кожна з них стартує з 1 рівня і потребує **10 XP** для першого підвищення левелу.\n\n"
        "💪 **Здоров'я** — йога, тренування, корисна їжа і тд.\n"
        "🧠 **Мудрість** — читання, навчання, вивчення мов, кодинг і тд.\n"
        "🎨 **Творчість** — малювання, гра на інструментах, в'язання і тд.\n"
        "💵 **Фінанси** — робота, планування бюджету і тд.\n"
        "🤝 **Зв'язки** — спілкування з близькими, допомога, турбота про рослин чи тварин.\n\n"
        "📥 **Як записати справу:** натисни кнопку нижче і надішли звіт, який починається з емодзі сфери та оцінки її складності **від 4 до 14 балів**.\n\n"
        
    )
    bot.send_message(message.chat.id, msg_2, parse_mode="Markdown", reply_markup=get_main_menu())

@bot.message_handler(content_types=['text'])
def handle_menu(message):
    global player
    
    if message.text == "🧙‍♂️ Персонаж":
        user_id = str(message.from_user.id)
        player = load_data().get(user_id, create_new_player())
        status = f"🧙‍♂️ **Лист Персонажа (Рівень {player['level']})**\n"
        status += f"✨ Загальний досвід: {player['xp_total']:.1f} XP\n"
        status += "────────────────────\n"
        for key, sphere in player["spheres"].items():
            status += f"{sphere['name']}: Лвл {sphere['lvl']} ({sphere['xp']:.1f}/{sphere['max_xp']:.1f} XP)\n"
        bot.send_message(message.chat.id, status, parse_mode="Markdown")
        
    elif message.text == "🎒 Рюкзак":
        if not player["inventory"]:
            bot.send_message(message.chat.id, "🎒 **Твій рюкзак порожній.")
        else:
            items_counts = {}
            for item in player["inventory"]:
                items_counts[item] = items_counts.get(item, 0) + 1
            inv_text = "🎒 **Вміст твого рюкзака:**\n\n"
            for item, count in items_counts.items():
                inv_text += f"• {item} x{count}\n"
            bot.send_message(message.chat.id, inv_text)
            
    elif message.text == "📜 Основний квест":
        bot.send_message(message.chat.id, "🔒 **Основний квест заблоковано.**\n\nНакопичуй магічний досвід, щоб відкрити наступні глави сюжету!")
        
    elif message.text == "🎯 Мої Квести":
        bot.send_message(message.chat.id, "🎯 **Твої власні цілі:**\n\nПоки що тут тихо. Наступним кроком ми реалізуємо систему створення твоїх особистих босів!")
        
    elif message.text == "➕ Додати Справу":
        guide = (
            "➕ **Режим магічного звіту активовано!**\n\n"
            "Запиши свої діяння (можна декілька, кожне з нового рядка) у форматі:\n"
            "`[Емодзі] [Бали від 4 до 14] [Опис справи]`\n\n"
            "✨ **Доступні сфери сили:**\n"
            "• 💪 — Здоров'я\n"
            "• 🧠 — Мудрість\n"
            "• 🎨 — Творчість\n"
            "• 💵 — Фінанси\n"
            "• 🤝 — Зв'язки\n\n"
            "🧙‍♂️ Коли завершиш, натисни кнопку нижче"
        )
        msg = bot.send_message(message.chat.id, guide, parse_mode="Markdown", reply_markup=types.ForceReply(selective=True))
        bot.register_next_step_handler(msg, process_activity)

def process_activity(message):
    user_id = str(message.from_user.id) # Беремо унікальний ID того, хто пише
    database = load_data()              # Завантажуємо всю картотеку з файлу
    
    # Якщо цього користувача ще немає в базі — створюємо для нього новий профіль
    if user_id not in database:
        database[user_id] = create_new_player()
        
    player = database[user_id]          # Тепер працюємо суто з цим гравцем!
    
    text = message.text.strip() if message.text else ""
    
    # Якщо користувач вирішив вийти з режиму додавання
    if text == "🧙‍♂️ Завершити ритуал":
        bot.send_message(
            message.chat.id, 
            "📜 *Ритуал завершено. Твої діяння записані в хроніки Грінвуду.*", 
            parse_mode="Markdown", 
            reply_markup=get_main_menu()
        )
        return

    if not text:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row(types.KeyboardButton("🧙‍♂️ Завершити ритуал"))
        msg = bot.send_message(message.chat.id, "Ой-йой, ти написав невидими чорнилами, спробуй ще раз", reply_markup=markup)
        bot.register_next_step_handler(msg, process_activity)
        return

    lines = text.split('\n')
    final_report = "📝 **Магічні підрахнуки 🧚‍♀️:**\n\n"
    lvl_up_text = ""
    any_success = False
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        detected_spheres = []
        for key, sphere in player["spheres"].items():
            if line.startswith(sphere["emoji"]) or (len(line) > 1 and line[1] == sphere["emoji"]):
                detected_spheres.append(key)
                
        if not detected_spheres:
            final_report += f"❌ `{line[:20]}...` — Ой-йой, до якої сфери варто віднести бали?.\n"
            continue

        match = re.search(r'\d+', line)
        if not match:
            final_report += f"❌ `{line[:20]}...` — На скільке важке було це закляття?\n"
            continue
            
        base_xp = int(match.group())
        
        if base_xp < 4 or base_xp > 14:
            final_report += f"❌ `{line[:20]}...` — Твої бали ({base_xp}) поза магічним лімітом (від 4 до 14).\n"
            continue

        any_success = True
        xp_per_sphere = base_xp / len(detected_spheres)
        
        clean_task = re.sub(r'^[^\w\s]+', '', line).strip()
        clean_task = re.sub(r'^\d+', '', clean_task).strip()
        if not clean_task: 
            clean_task = "Корисна дія"
            
        final_report += f"✨ *{clean_task}*:\n"
        
        for key in detected_spheres:
            sphere = player["spheres"][key]
            sphere["xp"] += xp_per_sphere
            player["xp_total"] += xp_per_sphere
            
            while sphere["xp"] >= sphere["max_xp"]:
                sphere["xp"] -= sphere["max_xp"]
                sphere["lvl"] += 1
                sphere["max_xp"] += 5.0
                lvl_up_text += f"⚡️ **РІВЕНЬ 📈 Ти стаєш краще з кожним днем:** Сфера {sphere['name']} піднялася до **{sphere['lvl']} рівня**! 🎉\n"
                
            final_report += f"  • {sphere['name']}  +{xp_per_sphere:.1f} XP\n"
        final_report += "\n"

    new_global_lvl = int(player["xp_total"] // 50) + 1
    if new_global_lvl > player["level"]:
        player["level"] = new_global_lvl
        lvl_up_text += f"\n🌟 **НОВИЙ РІВЕНЬ ГЕРОЯ!** Твій рівень оновився до **{new_global_lvl}**! 🧙‍♂️\n"

    if lvl_up_text:
        final_report += "────────────────────\n" + lvl_up_text

    if any_success:
        found_loot = []
        for loot_item in POSSIBLE_LOOT:
            if random.random() < LOOT_CHANCE:
                found_loot.append(loot_item)
                player["inventory"].append(loot_item)
        if found_loot:
            final_report += f"\n🎒 **НЕЙМОВІРНА УДАЧА!** {', '.join(found_loot)} додано в рюкзак!"

    final_report += "\n🔮 *Режим введення активний. Ти можеш надіслати ще справи або завершити ритуал.*"
    database[user_id] = player
    save_data(database)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(types.KeyboardButton("🧙‍♂️ Завершити ритуал"))
    
    msg = bot.send_message(message.chat.id, final_report, parse_mode="Markdown", reply_markup=markup)
    bot.register_next_step_handler(msg, process_activity)

Thread(target=run_server).start()
bot.polling(none_stop=True)
