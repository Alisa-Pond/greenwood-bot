import telebot
import json
from telebot import types
import os
import random
import time
import re
import traceback
from threading import Thread
from flask import Flask, request
from supabase import create_client, Client
from datetime import datetime
from zoneinfo import ZoneInfo
import logging

telebot.logger.setLevel(logging.DEBUG)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

app = Flask('')

@app.route('/')
def home():
    return "Greenwood Chronicles is alive!"

BOT_TOKEN = os.environ.get("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("❌ ПОМИЛКА: Render не передав BOT_TOKEN! Перевір налаштування Environment Variables!")

bot = telebot.TeleBot(BOT_TOKEN)

def get_player(user_id):
    """Отримує дані гравця з Supabase. Якщо гравця немає — створює його."""
    user_id = str(user_id)
    response = supabase.table("players").select("*").eq("user_id", user_id).execute()
    
    default_quests = {
        "scrolls": [],    # Одноразові та накопичувальні сувої
        "rituals": [],    # Щоденні ритуали
        "plants": []      # Магічне насіння в Теплиці
    }
    
    if response.data and len(response.data) > 0:
        player = response.data[0]
        updated = False
        if "quests" not in player:
            player["quests"] = default_quests
            updated = True
        else:
            for key in ["scrolls", "rituals", "plants"]:
                if key not in player["quests"]:
                    player["quests"][key] = []
                    updated = True
        if updated:
            update_player(user_id, player)
        return player
    
    new_player = {
        "user_id": user_id,
        "level": 1,
        "xp_total": 0.0,
        "inventory": [],
        "spheres": {
            "health": {"name": "💪 Здоров'я", "emoji": "💪", "lvl": 1, "xp": 0.0, "max_xp": 10.0},
            "wisdom": {"name": "🧠 Мудрість", "emoji": "🧠", "lvl": 1, "xp": 0.0, "max_xp": 10.0},
            "art": {"name": "🎨 Творчість", "emoji": "🎨", "lvl": 1, "xp": 0.0, "max_xp": 10.0},
            "finance": {"name": "💵 Фінанси", "emoji": "💵", "lvl": 1, "xp": 0.0, "max_xp": 10.0},
            "relations": {"name": "🤝 Зв'язки", "emoji": "🤝", "lvl": 1, "xp": 0.0, "max_xp": 10.0}
        },
        "quests": default_quests
    }
    
    supabase.table("players").insert(new_player).execute()
    return new_player

def update_player(user_id, player_data):
    """Оновлює дані гравця в базі Supabase."""
    user_id = str(user_id)
    supabase.table("players").update(player_data).eq("user_id", user_id).execute()

LOOT_CHANCE = 0.003
POSSIBLE_LOOT = [
    "🧪 Настій Бадьорості",
    "📜 Стародавній Сувій",
    "💎 Кристал Натхнення",
    "🔑 Мідний Ключ"
]

# --- КЛАВІАТУРИ МЕНЮ ---

def get_main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(types.KeyboardButton("🧙‍♂️ Персонаж"), types.KeyboardButton("🎒 Рюкзак"))
    markup.row(types.KeyboardButton("📜 Основний квест"), types.KeyboardButton("🎯 Мої Квести"))
    markup.row(types.KeyboardButton("➕ Додати Справу"))
    return markup

def get_quests_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(types.KeyboardButton("📜 Сувої завдань"), types.KeyboardButton("🔄 Щоденні ритуали"))
    markup.row(types.KeyboardButton("🌱 Теплиця Грінвуду"))
    markup.row(types.KeyboardButton("🔙 Назад"))
    return markup

def get_scrolls_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(types.KeyboardButton("➕ Створити сувой"), types.KeyboardButton("✅ Позначити виконаним"))
    markup.row(types.KeyboardButton("🗑️ Спалити сувой"), types.KeyboardButton("🔙 Назад до квестів"))
    return markup

def get_rituals_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(types.KeyboardButton("➕ Створити ритуал"), types.KeyboardButton("✅ Виконати ритуал"))
    markup.row(types.KeyboardButton("🔥 Спалити ритуал"), types.KeyboardButton("🔙 Назад до квестів"))
    return markup

def get_greenhouse_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(types.KeyboardButton("🌱 Посадити насіння"), types.KeyboardButton("🌸 Квітка розквітла"))
    markup.row(types.KeyboardButton("🪾 Вирвати бур'ян"), types.KeyboardButton("🔙 Назад до квестів"))
    return markup

# --- ВІТАЛЬНЕ ПОВІДОМЛЕННЯ ---

@bot.message_handler(commands=['start'])
def welcome(message):
    user_id = str(message.from_user.id)
    get_player(user_id)
    
    msg_1 = (
        "🪷 **Вітаємо у Greenwood Chronicles!** 🪷\n\n"
        "Магічний ліс відкриває свої таємниці... А я — 🪷Lilly Pond🪷, твій магічний провідник у цьому затишному світі. "
        "Я допомагатиму тобі перетворювати твої реальні досягнення на справжню силу персонажа!"
    )
    bot.send_message(message.chat.id, msg_1, parse_mode="Markdown")
    
    time.sleep(3)
    
    msg_2 = (
        "🔮 **Як влаштований наш світ:**\n"
        "Твій персонаж розвиває 5 основних сфер життя. Кожна з них стартує з 1 рівня і потребує **10 XP** для першого підвищення левелу.\n\n"
        "💪 **Здоров'я** — yoga, тренування, корисна їжа і тд.\n"
        "🧠 **Мудрість** — читання, навчання, вивчення мов, кодинг і тд.\n"
        "🎨 **Творчість** — малювання, гра на інструментах, в'язання і тд.\n"
        "💵 **Фінанси** — робота, планування бюджету і тд.\n"
        "🤝 **Зв'язки** — спілкування з близькими, допомога, турбота про рослин чи тварин.\n\n"
        "📥 **Як записати справу:** натисни кнопку нижче і надішли звіт, який починається з емодзі сфери та оцінки її складності **від 4 до 14 балів**.\n\n"
    )
    bot.send_message(message.chat.id, msg_2, parse_mode="Markdown", reply_markup=get_main_menu())

# --- ГОЛОВНИЙ ОБРОБНИК МЕНЮ ---

@bot.message_handler(content_types=['text'])
def handle_menu(message):
    user_id = str(message.from_user.id)
    
    if message.text == "🧙‍♂️ Персонаж":
        current_player = get_player(user_id)
        status = f"🧙‍♂️ **Лист Персонажа (Рівень {current_player['level']})**\n"
        status += f"✨ Загальний досвід: {float(current_player['xp_total']):.1f} XP\n"
        status += "────────────────────\n"
        
        for key, sphere in current_player["spheres"].items():
            status += f"{sphere['name']}: Лвл {sphere['lvl']} ({float(sphere['xp']):.1f}/{float(sphere['max_xp']):.1f} XP)\n"
            
        bot.send_message(message.chat.id, status, parse_mode="Markdown")
        
    elif message.text == "🎒 Рюкзак":
        current_player = get_player(user_id)
        if not current_player["inventory"]:
            bot.send_message(message.chat.id, "🎒 **Твій рюкзак порожній.**")
        else:
            items_counts = {}
            for item in current_player["inventory"]:
                items_counts[item] = items_counts.get(item, 0) + 1
            inv_text = "🎒 **Вміст твого рюкзака:**\n\n"
            for item, count in items_counts.items():
                inv_text += f"• {item} x{count}\n"
            bot.send_message(message.chat.id, inv_text, parse_mode="Markdown")
            
    elif message.text == "📜 Основний квест":
        bot.send_message(message.chat.id, "🔒 **Основний квест заблоковано.**\n\nНакопичуй магічний досвід, щоб відкрити наступні глави сюжету!")
        
    elif message.text == "🎯 Мої Квести" or message.text == "🔙 Назад до квестів":
        bot.send_message(
            message.chat.id, 
            "🎯 **Магічний Органайзер Грінвуду**\n\nОбери розділ, у якому ти хочеш навести лад:", 
            reply_markup=get_quests_menu()
        )
        
    elif message.text == "🔙 Назад":
        bot.send_message(
            message.chat.id, 
            "🚪 Ти повернувся", 
            reply_markup=get_main_menu()
        )

    # --- СУВОЇ ЗАВДАНЬ ---
   # --- СУВОЇ ЗАВДАНЬ ---
    elif message.text == "📜 Сувої завдань":
        player = get_player(user_id)
        scrolls = player["quests"].get("scrolls", [])
        active_scrolls = [s for s in scrolls if s["done_count"] < s["max_count"]]
        
        status_text = (
            "📜 **Книга Сувоїв Грінвуду**\n\n"
            "✨ **Лілі Понд:** *«Привіт, люба! Сувої — це твої особисті середньострокові квести. "
            "Вони ідеально підходять для планування справ, які мають чіткий дедлайн та потребують "
            "кількох повторень (наприклад, три тренування на тиждень або вивчення теми за 5 сесій).\n\n"
            "Кожен сувой запечатує твою обіцянку собі. Ти сама визначаєш складність (бали XP за кожен крок) "
            "та реальну приємну нагороду, яку отримаєш, коли сувой згорить від повністю виконаної роботи!»*\n\n"
            "────────────────────\n"
            "📌 **Твої активні сувої:**\n"
        )
        
        if not active_scrolls:
            status_text += "_Твій стіл порожній. Час запечатати першу угоду!_"
        else:
            for idx, s in enumerate(active_scrolls, 1):
                status_text += f"{idx}. {s['emoji']} **{s['task']}** — ({s['done_count']}/{s['max_count']}) | {float(s['xp_per_once']):.1f} XP за крок (⏰ Дедлайн: {s['deadline']})\n"
                
        status_text += "\n👇 **Обери магічну дію:**"
        bot.send_message(message.chat.id, status_text, parse_mode="Markdown", reply_markup=get_scrolls_menu())

    elif message.text == "➕ Створити сувой":
        guide = (
            "✍️ **Запечатування нового сувою**\n\n"
            "✨ **Лілі Понд:** *«Давай розправимо чистий пергамент! Будь ласка, напиши мені умови "
            "твого квесту одним рядком за цим магічним шаблоном:»*\n\n"
            "📖 `[Емодзі сфери] [Кратність] [Бали за крок] [Дедлайн ДД.ММ] [Опис справи та твоя Нагорода]`\n\n"
            "────────────────────\n"
            "🧩 **Розшифровка елементів:**\n"
            "• **Емодзі сфери** — Обери сферу, яку прокачуєш (`💪`, `🧠`, `🎨`, `💵`, `🤝`).\n"
            "• **Кратність** — Скільки всього разів треба виконати справу (наприклад, `3` або `5`).\n"
            "• **Бали за крок** — Скільки XP ти отримуватимеш за кожен пройдений крок (від `4` до `14`).\n"
            "• **Дедлайн** — Дата, до якої квест має бути завершений (у форматі `ДД.ММ`).\n"
            "• **Опис справи** — Що саме ти робиш і яку реальну нагороду даруєш собі в кінці.\n\n"
            "📌 **Приклад для копіювання:**\n"
            "`🧠 3 10 22.07 Прочитати 50 сторінок книги (Нагорода: замовити нову сукню)`\n\n"
            "*(Якщо передумала, просто напиши `🔙 Назад до квестів`)*"
        )
        msg = bot.send_message(message.chat.id, guide, parse_mode="Markdown", reply_markup=types.ForceReply(selective=True))
        bot.register_next_step_handler(msg, process_create_scroll)
    elif message.text == "✅ Позначити виконаним":
        player = get_player(user_id)
        scrolls = player["quests"].get("scrolls", [])
        active_scrolls = [s for s in scrolls if s["done_count"] < s["max_count"]]
        
        if not active_scrolls:
            bot.send_message(message.chat.id, "✨ **Лілі Понд:** *«На твоїх полицях немає активних сувоїв для виконання.»*")
            return
            
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for s in active_scrolls:
            markup.add(types.KeyboardButton(s['task']))
        markup.add(types.KeyboardButton("🔙 Назад до квестів"))
        
        msg = bot.send_message(message.chat.id, "✨ **Лілі Понд:** *«Обери сувой, у якому ти сьогодні зробила крок вперед:»*", reply_markup=markup)
        bot.register_next_step_handler(msg, process_complete_scroll)

    elif message.text == "🗑️ Спалити сувой":
        player = get_player(user_id)
        scrolls = player["quests"].get("scrolls", [])
        active_scrolls = [s for s in scrolls if s["done_count"] < s["max_count"]]
        
        if not active_scrolls:
            bot.send_message(message.chat.id, "✨ **Лілі Понд:** *«Тобі нема чого спалювати, твій стіл чистий!»*")
            return
            
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for s in active_scrolls:
            markup.add(types.KeyboardButton(s['task']))
        markup.add(types.KeyboardButton("🔙 Назад до квестів"))
        
        msg = bot.send_message(message.chat.id, "✨ **Лілі Понд:** *«Який сувой ти хочеш спалити у синьому вогні без отримання досвіду?»*", reply_markup=markup)
        bot.register_next_step_handler(msg, process_delete_scroll)

    # --- ЩОДЕННІ РИТУАЛИ ---
    elif message.text == "🔄 Щоденні ритуали":
        player = get_player(user_id)
        rituals = player["quests"].get("rituals", [])
        
        status_text = "🔄 **Твої щоденні ритуали на сьогодні:**\n"
        status_text += "────────────────────\n"
        
        if not rituals:
            status_text += "✨ Ти ще не створив жодного щоденного ритуалу."
        else:
            for r in rituals:
                status = "✅" if r.get("done_today", False) else " "
                status_text += f"[{status}] {r['emoji']} **{r['task']}** ({float(r['xp']):.1f} XP)\n"
                
        status_text += "\n👇 **Обери магічну дію для ритуалів:**"
        bot.send_message(message.chat.id, status_text, parse_mode="Markdown", reply_markup=get_rituals_menu())

    # --- ТЕПЛИЦЯ ---
    elif message.text == "🏡 Теплиця Грінвуду":
        player = get_player(user_id)
        plants = player["quests"].get("plants", [])
        
        status_text = "🏡 **Теплиця Грінвуду**\n"
        status_text += "────────────────────\n"
        status_text += "👴 **Лісовик:** *«О, завітав-таки до моєї теплиці, юний магу! Поглянь на ці магічні насінини втрачених квітів Грінвуду... Щоб кожна з них проросла і розквітла, тобі знадобиться 5 елементів сили — твоя чітка ціль (SMART). Пам'ятай: насіння не зійде, якщо твоя мета розмита чи не має дедлайну! Опиши її чітко, доглядай, а коли вона розквітне в реальності — повертайся сюди і збирай плоди своєї магії!»*\n\n"
        
        status_text += "🌱 **Твої поточні магічні рослини:**\n"
        if not plants:
            status_text += "_Поки що теплиця порожня. Час посадити перше насіння!_"
        else:
            for idx, p in enumerate(plants, 1):
                status_text += f"{idx}. {p['emoji']} **{p['task']}** — [Нагорода: {float(p['xp']):.1f} XP] (Дедлайн: {p['deadline']})\n"
                
        status_text += "\n👇 **Обери магічну дію для саду:**"
        bot.send_message(message.chat.id, status_text, parse_mode="Markdown", reply_markup=get_greenhouse_menu())

    # --- РЕЖИМ ДОДАВАННЯ СПРАВИ ---
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

# --- ЛОГІКА ДОДАВАННЯ ЗВИЧАЙНИХ СПРАВ ТА СУВОЇВ ---

def process_activity(message):
    user_id = str(message.from_user.id) 
    player = get_player(user_id)          
    text = message.text.strip() if message.text else ""
    
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
        msg = bot.send_message(message.chat.id, "Ой-йой, ти написала невидимими чорнилами, спробуй ще раз", reply_markup=markup)
        bot.register_next_step_handler(msg, process_activity)
        return

    lines = text.split('\n')
    final_report = "📝 **Магічні підрахунки від Лілі Понд 🧚‍♀️:**\n\n"
    lvl_up_text = ""
    any_success = False
    
    scrolls = player["quests"].get("scrolls", [])
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        detected_spheres = []
        for key, sphere in player["spheres"].items():
            if line.startswith(sphere["emoji"]) or (len(line) > 1 and line[1] == sphere["emoji"]):
                detected_spheres.append(key)
                
        if not detected_spheres:
            final_report += f"❌ `{line[:20]}...` — До якої сфери варто віднести ці бали?.\n"
            continue

        match = re.search(r'\d+', line)
        if not match:
            final_report += f"❌ `{line[:20]}...` — Наскільки важким було це закляття?\n"
            continue
            
        base_xp = int(match.group())
        
        if base_xp < 4 or base_xp > 14:
            final_report += f"❌ `{line[:20]}...` — Твої бали ({base_xp}) поза магічним лімітом (вкажи від 4 до 14).\n"
            continue

        clean_task = re.sub(r'^[^\w\s]+', '', line).strip()
        clean_task = re.sub(r'^\d+', '', clean_task).strip()
        if not clean_task: 
            clean_task = "Корисна дія"

        any_success = True
        
        # Перевірка на сувой
        matched_scroll = None
        for s in scrolls:
            if s["task"].strip().lower() == clean_task.lower() and s["done_count"] < s["max_count"]:
                matched_scroll = s
                break
                
        if matched_scroll:
            matched_scroll["done_count"] += 1
            xp_per_sphere = float(matched_scroll["xp_per_once"]) / len(detected_spheres)
            
            final_report += f"📜 **Сувой: {matched_scroll['task']}** ({matched_scroll['done_count']}/{matched_scroll['max_count']}):\n"
            if matched_scroll["done_count"] == matched_scroll["max_count"]:
                final_report += "🎉 *Сувой виконано повністю! Отримай свою реальну нагороду!*\n"
        else:
            xp_per_sphere = base_xp / len(detected_spheres)
            final_report += f"✨ *{clean_task}*:\n"
        
        for key in detected_spheres:
            sphere = player["spheres"][key]
            sphere["xp"] = float(sphere["xp"]) + xp_per_sphere
            player["xp_total"] = float(player["xp_total"]) + xp_per_sphere
            
            while sphere["xp"] >= float(sphere["max_xp"]):
                sphere["xp"] -= float(sphere["max_xp"])
                sphere["lvl"] += 1
                sphere["max_xp"] += 5.0
                lvl_up_text += f"⚡️ **РІВЕНЬ 📈:** Сфера {sphere['name']} піднялася до **{sphere['lvl']} рівня**! 🎉\n"
                
            final_report += f"  • {sphere['name']}  +{xp_per_sphere:.1f} XP\n"
        final_report += "\n"

    new_global_lvl = int(float(player["xp_total"]) // 50) + 1
    if new_global_lvl > int(player["level"]):
        player["level"] = new_global_lvl
        lvl_up_text += f"\n🌟 **НОВИЙ РІВЕНЬ ГЕРОЯ!** Рівень оновлено до **{new_global_lvl}**! 🧙‍♂️\n"

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

    final_report += "\n🔮 *Я готова записувати твої наступні звершення або завершимо ритуал.*"
    
    update_player(user_id, player)
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(types.KeyboardButton("🧙‍♂️ Завершити ритуал"))
    
    msg = bot.send_message(message.chat.id, final_report, parse_mode="Markdown", reply_markup=markup)
    bot.register_next_step_handler(msg, process_activity)

# --- ЛОГІКА РОБОТИ ІЗ СУВОЯМИ ---

def process_create_scroll(message):
    user_id = str(message.from_user.id)
    text = message.text.strip() if message.text else ""
    
    if text == "🔙 Назад до квестів":
        bot.send_message(message.chat.id, "Створення скасовано, повертаємось.", reply_markup=get_scrolls_menu())
        return

    match = re.match(r"^([^\w\s])\s+(\d+)\s+(\d+)\s+(\d{2}\.\d{2})\s+(.+)$", text)
    
    if not match:
        msg = bot.send_message(
            message.chat.id, 
            "✨ **Лілі Понд:** *«Ой, щось пішло не так із чорнилом. Спробуй ще раз за моїм шаблоном або напиши `🔙 Назад до квестів`, щоб скасувати:* \n`[Емодзі] [Кратність] [Бали] [Дедлайн ДД.ММ] [Опис]`»",
            parse_mode="Markdown"
        )
        bot.register_next_step_handler(msg, process_create_scroll)
        return
        
    emoji, max_count, xp_per_once, deadline, task_desc = match.groups()
    max_count = int(max_count)
    xp_per_once = int(xp_per_once)
    task_desc = task_desc.strip()
    
    if xp_per_once < 4 or xp_per_once > 14:
        msg = bot.send_message(message.chat.id, "✨ **Лілі Понд:** *«Пам'ятай, що магічний ліміт балів за одне виконання має бути від 4 до 14! Спробуй ще раз ввести умови:»*")
        bot.register_next_step_handler(msg, process_create_scroll)
        return

    player = get_player(user_id)
    
    scrolls = player["quests"].get("scrolls", [])
    if any(s["task"].lower() == task_desc.lower() and s["done_count"] < s["max_count"] for s in scrolls):
        msg = bot.send_message(message.chat.id, f"✨ **Лілі Понд:** *«У твоїх хроніках уже є активний сувой з назвою \"{task_desc}\". Придумай іншу назву або заверши попередній квест!»*")
        bot.register_next_step_handler(msg, process_create_scroll)
        return

    new_scroll = {
        "emoji": emoji,
        "max_count": max_count,
        "done_count": 0,
        "xp_per_once": float(xp_per_once),
        "deadline": deadline,
        "task": task_desc
    }
    
    player["quests"]["scrolls"].append(new_scroll)
    update_player(user_id, player)
    
    bot.send_message(
        message.chat.id, 
        f"✨ **Лілі Понд:** *«Прекрасно! Новий сувой успішно запечатано у твою книгу квестів. Я нагадуватиму тобі про нього!»*\n\n{emoji} **{task_desc}**\n• Повторень: **{max_count}**\n• Сила кроку: **{xp_per_once} XP**\n• Термін: до **{deadline}**",
        parse_mode="Markdown",
        reply_markup=get_scrolls_menu()
    )

def process_complete_scroll(message):
    user_id = str(message.from_user.id)
    text = message.text.strip() if message.text else ""
    
    if text == "🔙 Назад до квестів":
        bot.send_message(message.chat.id, "Повертаємось.", reply_markup=get_scrolls_menu())
        return
        
    task_clean = text.strip()
    player = get_player(user_id)
    scrolls = player["quests"].get("scrolls", [])
    
    found_scroll = None
    for s in scrolls:
        if s["task"].strip().lower() == task_clean.lower() and s["done_count"] < s["max_count"]:
            found_scroll = s
            break
            
    if not found_scroll:
        bot.send_message(message.chat.id, "✨ **Лілі Понд:** *«Я не знайшла такого активного сувою у твоїх записах. Спробуй обрати з кнопок на клавіатурі!»*", reply_markup=get_scrolls_menu())
        return
        
    found_scroll["done_count"] += 1
    xp_to_add = found_scroll["xp_per_once"]
    
    sphere_key = None
    for key, sphere in player["spheres"].items():
        if sphere["emoji"] == found_scroll["emoji"]:
            sphere_key = key
            break
            
    lvl_up_text = ""
    if sphere_key:
        sphere = player["spheres"][sphere_key]
        sphere["xp"] = float(sphere["xp"]) + xp_to_add
        player["xp_total"] = float(player["xp_total"]) + xp_to_add
        
        while sphere["xp"] >= float(sphere["max_xp"]):
            sphere["xp"] -= float(sphere["max_xp"])
            sphere["lvl"] += 1
            sphere["max_xp"] += 5.0
            lvl_up_text += f"\n⚡️ **РІВЕНЬ📈:** Сфера {sphere['name']} піднялася до **{sphere['lvl']} рівня**! 🎉"
            
        new_global_lvl = int(float(player["xp_total"]) // 50) + 1
        if new_global_lvl > int(player["level"]):
            player["level"] = new_global_lvl
            lvl_up_text += f"\n🌟 **НОВИЙ РІВЕНЬ ГЕРОЯ!** Твій рівень зріс до **{new_global_lvl}**! 🧙‍♂️"
            
    report = f"✨ **Лілі Понд:** *«Чудовий крок! Записую прогрес у твій сувой!»*\n\n{found_scroll['emoji']} **{found_scroll['task']}** ({found_scroll['done_count']}/{found_scroll['max_count']})\n🔋 Отримано: **+{xp_to_add:.1f} XP**!"
    
    if found_scroll["done_count"] == found_scroll["max_count"]:
        report += f"\n\n🎉 **СУВОЙ ПОВНІСТЮ ЗАВЕРШЕНО!**\n✨ **Лілі Понд:** *«Ти впоралась! Не забудь забрати свою заслужену нагороду в реальному житті!»*"
        
    if lvl_up_text:
        report += "\n\n────────────────────" + lvl_up_text
        
    update_player(user_id, player)
    bot.send_message(message.chat.id, report, parse_mode="Markdown", reply_markup=get_scrolls_menu())

def process_delete_scroll(message):
    user_id = str(message.from_user.id)
    text = message.text.strip() if message.text else ""
    
    if text == "🔙 Назад до квестів":
        bot.send_message(message.chat.id, "Повертаємось.", reply_markup=get_scrolls_menu())
        return
        
    task_clean = text.strip()
    player = get_player(user_id)
    scrolls = player["quests"].get("scrolls", [])
    
    new_scrolls = [s for s in scrolls if not (s["task"].strip().lower() == task_clean.lower() and s["done_count"] < s["max_count"])]
    
    if len(scrolls) == len(new_scrolls):
        bot.send_message(message.chat.id, "✨ **Лілі Понд:** *«Хм, такого сувою немає на твоєму столі. Спробуй обрати з кнопок!»*", reply_markup=get_scrolls_menu())
        return
        
    player["quests"]["scrolls"] = new_scrolls
    update_player(user_id, player)
    
    bot.send_message(message.chat.id, "🔥 **Сувой безслідно згорів у синьому полум'ї.** Цього завдання більше не існує.", reply_markup=get_scrolls_menu())

# --- ВЕБХУКИ ТА СЕРВЕР ---

@app.route('/' + str(BOT_TOKEN), methods=['POST'])
def getMessage():
    try:
        json_string = request.stream.read().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "!", 200
    except Exception as e:
        print("❌ КРИТИЧНА ПОМИЛКА В ЛОГІЦІ БОТА:")
        print(traceback.format_exc())
        return "!", 200
        
if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url="https://greenwood-bot-yw5w.onrender.com/" + str(BOT_TOKEN))
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
