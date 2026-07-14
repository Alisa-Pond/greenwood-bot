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
    
    # Дефолтна структура для нових елементів квестів
    default_quests = {
        "scrolls": [],    # Одноразові та накопичувальні сувої
        "rituals": [],    # Щоденні ритуали
        "plants": []      # Магічне насіння в Теплиці
    }
    
    if response.data and len(response.data) > 0:
        player = response.data[0]
        # Авто-міграція: якщо у старого гравця ще немає цих полів, додаємо їх
        updated = False
        if "quests" not in player:
            player["quests"] = default_quests
            updated = True
        else:
            # Перестраховка для окремих підтипів
            for key in ["scrolls", "rituals", "plants"]:
                if key not in player["quests"]:
                    player["quests"][key] = []
                    updated = True
        if updated:
            update_player(user_id, player)
        return player
    
    # Створюємо нового гравця
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
    """Головне меню розділу Мої Квести"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(types.KeyboardButton("📜 Сувої завдань"), types.KeyboardButton("🔄 Щоденні ритуали"))
    markup.row(types.KeyboardButton("🏡 Теплиця Грінвуду"))
    markup.row(types.KeyboardButton("🔙"))
    return markup

def get_scrolls_menu():
    """Меню для взаємодії із Сувоями"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(types.KeyboardButton("➕ Створити сувой"), types.KeyboardButton("✅ Позначити виконаним"))
    markup.row(types.KeyboardButton("🗑️ Спалити сувой"), types.KeyboardButton("🔙 Назад до квестів"))
    return markup

def get_rituals_menu():
    """Меню для взаємодії з Ритуалами"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(types.KeyboardButton("➕ Створити ритуал"), types.KeyboardButton("✅ Виконати ритуал"))
    markup.row(types.KeyboardButton("🗑️ Спалити ритуал"), types.KeyboardButton("🔙 Назад до квестів"))
    return markup

def get_greenhouse_menu():
    """Меню для взаємодії з Теплицею"""
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(types.KeyboardButton("🌱 Посадити насіння"), types.KeyboardButton("🌸 Задокументувати цвітіння"))
    markup.row(types.KeyboardButton("🗑️ Вирвати бур'ян"), types.KeyboardButton("🔙 Назад до квестів"))
    return markup

# --- ВІТАЛЬНЕ ПОВІДОМЛЕННЯ ПРИ СТАРТІ ---

@bot.message_handler(commands=['start'])
def welcome(message):
    user_id = str(message.from_user.id)
    get_player(user_id)
    
    msg_1 = (
        "🌲 **Вітаємо у Greenwood Chronicles!** 🌲\n\n"
        "Магічний ліс відкриває свої таємниці... А я — **Lilly Pond**, твій магічний провідник у цьому затишному світі. "
        "Я допомагатиму тобі перетворювати твої реальні досягнення на справжню силу персонажа!"
    )
    bot.send_message(message.chat.id, msg_1, parse_mode="Markdown")
    
    time.sleep(2)
    
    msg_2 = (
        "🔮 **Як влаштований наш світ:**\n"
        "Твій персонаж розвиває 5 основних сфер життя. Кожна з них стартує з 1 рівня.\n\n"
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
    
    # --- МЕНЮ ПЕРСОНАЖА ТА ІНВЕНТАРЮ ---
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
        
    # --- НАВІГАЦІЯ РОЗДІЛУ "МОЇ КВЕСТИ" ---
    elif message.text == "🎯 Мої Квести" or message.text == "🔙 Назад до квестів":
        bot.send_message(
            message.chat.id, 
            "🎯 **Магічний Органайзер Грінвуду**\n\nОбери розділ, у якому ти хочеш навести лад:", 
            reply_markup=get_quests_menu()
        )
        
    elif message.text == "🔙 Назад":
        bot.send_message(
            message.chat.id, 
            "🚪 З поверненням.", 
            reply_markup=get_main_menu()
        )

    # --- РАЗОВІ СУВОЇ ЗАВДАНЬ ---
    elif message.text == "📜 Сувої завдань":
        player = get_player(user_id)
        scrolls = player["quests"].get("scrolls", [])
        
        # Відображаємо тільки невиконані сувої
        active_scrolls = [s for s in scrolls if s["done_count"] < s["max_count"]]
        
        status_text = "📜 **Твої активні сувої завдань:**\n"
        status_text += "────────────────────\n"
        
        if not active_scrolls:
            status_text += "✨ Твій стіл порожній. Усі сувої успішно закриті або ще не створені!"
        else:
            for idx, s in enumerate(active_scrolls, 1):
                status_text += f"{idx}. {s['emoji']} **{s['task']}** — ({s['done_count']}/{s['max_count']}) | {float(s['xp_per_once']):.1f} XP за крок (Дедлайн: {s['deadline']})\n"
                
        status_text += "\n👇 **Обери магічну дію для сувоїв:**"
        bot.send_message(message.chat.id, status_text, parse_mode="Markdown", reply_markup=get_scrolls_menu())

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

    # --- ТЕПЛИЦЯ (КОЛИШНІ БОСИ) ---
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

    # --- РЕЖИМ ДОДАВАННЯ СПРАВИ (ЗВИТ) ---
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

# --- ЛОГІКА ДОДАВАННЯ ЗВИЧАЙНИХ СПРАВ (БЕЗ ЗМІН) ---

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
            final_report += f"❌ `{line[:20]}...` — Твої бали ({base_xp}) поза магічним лімітом (вкажи від 4 до 14).\n"
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
            
            sphere["xp"] = float(sphere["xp"]) + xp_per_sphere
            player["xp_total"] = float(player["xp_total"]) + xp_per_sphere
            sphere["max_xp"] = float(sphere["max_xp"])
            
            while sphere["xp"] >= sphere["max_xp"]:
                sphere["xp"] -= sphere["max_xp"]
                sphere["lvl"] += 1
                sphere["max_xp"] += 5.0
                lvl_up_text += f"⚡️ **РІВЕНЬ 📈 Ти стаєш краще з кожним днем:** Сфера {sphere['name']} піднялася до **{sphere['lvl']} рівня**! 🎉\n"
                
            final_report += f"  • {sphere['name']}  +{xp_per_sphere:.1f} XP\n"
        final_report += "\n"

    new_global_lvl = int(float(player["xp_total"]) // 50) + 1
    if new_global_lvl > int(player["level"]):
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
    
    update_player(user_id, player)
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(types.KeyboardButton("🧙‍♂️ Завершити ритуал"))
    
    msg = bot.send_message(message.chat.id, final_report, parse_mode="Markdown", reply_markup=markup)
    bot.register_next_step_handler(msg, process_activity)

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
