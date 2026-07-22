import os
import json
import random
import time
import re
import traceback
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from threading import Thread

import telebot
from telebot import types
from flask import Flask, request
from supabase import create_client, Client

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

def clean_skin_tones(text_to_clean):
    if not text_to_clean:
        return ""
    
    # Словник рівності: перетворюємо всі кольорові варіації на базові жовті
    replacements = {
        "💪🏻": "💪", "💪🏼": "💪", "💪🏽": "💪", "💪🏾": "💪", "💪🏿": "💪",
        "🤝🏻": "🤝", "🤝🏼": "🤝", "🤝🏽": "🤝", "🤝🏾": "🤝", "🤝🏿": "🤝"
    }
    
    for tone, base in replacements.items():
        text_to_clean = text_to_clean.replace(tone, base)
        
    return text_to_clean

def get_player(user_id):
    """Отримує дані гравця з Supabase. Якщо гравця немає — створює його."""
    user_id = str(user_id)
    response = supabase.table("players").select("*").eq("user_id", user_id).execute()
    
    default_quests = {
        "scrolls": [],    # Одноразові та накопичувальні сувої
        "rituals": [],    # Щоденні ритуали
        "plants": []      # Магічне насіння в Теплиці = цілі
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
    markup.row(types.KeyboardButton("➕ Створити сувой"), types.KeyboardButton("✅ Виконати завдання"))
    markup.row(types.KeyboardButton("🔥 Спалити сувой"), types.KeyboardButton("🔙 Назад до квестів"))
    return markup

def get_rituals_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(types.KeyboardButton("➕ Створити ритуал"), types.KeyboardButton("✅ Виконати ритуал"))
    markup.row(types.KeyboardButton("🔥 Спалити ритуал"), types.KeyboardButton("🔙 Назад до квестів"))
    return markup

def get_greenhouse_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(types.KeyboardButton("🌱 Посадити насіння"), types.KeyboardButton("🌸 Квітка розквітла"))
    markup.row(types.KeyboardButton("🪾 Вирвати баобаб"), types.KeyboardButton("🔙 Назад до квестів"))
    return markup

# --- ВІТАЛЬНЕ ПОВІДОМЛЕННЯ ---

@bot.message_handler(commands=['start'])
def welcome(message):
    user_id = str(message.from_user.id)
    get_player(user_id)
    
    msg_1 = (
        "🌲 <b>Вітаємо у Greenwood!</b> 🌳\n\n"
        "Магічний ліс відкриває свои таємниці... А я — 🪷 <b>Lilly Pond</b> 🪷, твій магічний провідник у цьому затишному світі. "
        "Я допомагатиму тобі перетворювати твої реальні досягнення на справжню силу персонажа!"
    )
    bot.send_message(message.chat.id, msg_1, parse_mode="HTML")
    
    time.sleep(3)
    
    msg_2 = (
        "🔮 <b>Як влаштований наш світ:</b>\n"
        "Твій персонаж розвиває 5 основних сфер життя. Кожна з них стартує з 1 рівня і потребує <b>10 XP</b> для першого підвищення левелу.\n\n"
        "💪 <b>Здоров'я</b> — yoga, тренування, корисна їжа і тд.\n"
        "🧠 <b>Мудрість</b> — читання, навчання, вивчення мов, кодинг і тд.\n"
        "🎨 <b>Творчість</b> — малювання, гра на інструментах, в'язання і тд.\n"
        "💵 <b>Фінанси</b> — робота, планування бюджету і тд.\n"
        "🤝 <b>Зв'язки</b> — спілкування з близькими, допомога, турбота про рослин чи тварин.\n\n"
        "🎯 <b> Розділ  Мої Квести :</b>\n"
        "Це твоє магічне джерело мотивації! Тут ти можеш структурувати свої цілі: створювати <b>📜 Сувої</b> для"
        "справ із дедлайнами, налаштовувати щоденні <b>🔄 Ритуали</b> для корисних звичок на кожен день або саджати великі цілі в "
        "<b>🌱 Теплиці </b>."
    )
    bot.send_message(message.chat.id, msg_2, parse_mode="HTML", reply_markup=get_main_menu())

# --- ГОЛОВНИЙ ОБРОБНИК МЕНЮ ---

@bot.message_handler(content_types=['text'])
def handle_menu(message):
    user_id = str(message.from_user.id)
    
    if message.text == "🧙‍♂️ Персонаж":
        current_player = get_player(user_id)
        status = f" <b>Лист Персонажа (Рівень {current_player['level']})</b>\n"
        status += f" Загальний досвід: {float(current_player['xp_total']):.1f} XP\n"
        status += "────────────────────\n"
        
        for key, sphere in current_player["spheres"].items():
            status += f"{sphere['name']}: Лвл {sphere['lvl']} ({float(sphere['xp']):.1f}/{float(sphere['max_xp']):.1f} XP)\n"
            
        bot.send_message(message.chat.id, status, parse_mode="HTML")
        
    elif message.text == "🎒 Рюкзак":
        current_player = get_player(user_id)
        if not current_player["inventory"]:
            bot.send_message(message.chat.id, "🎒 <b>Твій рюкзак порожній.</b>", parse_mode="HTML")
        else:
            items_counts = {}
            for item in current_player["inventory"]:
                items_counts[item] = items_counts.get(item, 0) + 1
            inv_text = "🎒 <b>Вміст твого рюкзака:</b>\n\n"
            for item, count in items_counts.items():
                inv_text += f"• {item} x{count}\n"
            bot.send_message(message.chat.id, inv_text, parse_mode="HTML")
            
    elif message.text == "📜 Основний квест":
        bot.send_message(message.chat.id, "🔒 <b>Основний квест заблоковано.</b> ", parse_mode="HTML")
        
    # --- ГОЛОВНЕ МЕНЮ КВЕСТІВ ---
    elif message.text == "🎯 Мої Квести" or message.text == "🔙 Назад до квестів":
        player = get_player(user_id)
        
        # Поточна дата за Києвом (формат ДД.ММ)
        today_str = datetime.now(ZoneInfo("Europe/Kyiv")).strftime("%d.%m")
        
        scrolls = player["quests"].get("scrolls", [])
        active_scrolls = [s for s in scrolls if s["done_count"] < s["max_count"]]
        rituals = player["quests"].get("rituals", [])
        plants = player["quests"].get("plants", [])
        
        status_text = "🎯 <b>Магічний Органайзер Грінвуду</b>\n"
        status_text += "────────────────────\n\n"
        
        # === Блок Сувоїв ===
        status_text += "📜 <b>Активні сувої:</b>\n"
        if not active_scrolls:
            status_text += "• <i>Немає активних сувоїв</i>\n"
        else:
            for s in active_scrolls:
                fire = " 🔥" if s.get('deadline') == today_str else ""
                status_text += f"• {s['emoji']} {s['task']} ({s['done_count']}/{s['max_count']}) | до {s['deadline']}{fire}\n"
                
        status_text += "\n"
        
        # === Блок Ритуалів ===
        status_text += "🔄 <b>Активні ритуали на сьогодні:</b>\n"
        
        kyiv_days = {0: "пн", 1: "вт", 2: "ср", 3: "чт", 4: "пт", 5: "сб", 6: "нд"}
        today_day = kyiv_days[datetime.now(ZoneInfo("Europe/Kyiv")).weekday()]
        
        today_rituals = [r for r in rituals if today_day in r.get("days", [])]
        
        if not today_rituals:
            status_text += "• <i>На сьогодні немає активних ритуалів</i>\n"
        else:
            for r in today_rituals:
                status = "✅" if r.get("done_today", False) else "⏳"
                status_text += f"• {status} {r['emoji']} {r['task']}\n"
                
        status_text += "\n"

        # === Блок Рослин (Теплиці) ===
        status_text += "🌱 <b>Рослини в теплиці:</b>\n"
        if not plants:
            status_text += "• <i>Теплиця порожня</i>\n"
        else:
            for p in plants:
                fire = " 🔥" if p.get('deadline') == today_str else ""
                status_text += f"• {p['emoji']} {p['task']} | до {p['deadline']}{fire}\n"

        status_text += "\n────────────────────\n"
        status_text += "Обери розділ для керування:"

        bot.send_message(
            message.chat.id, 
            status_text, 
            parse_mode="HTML", 
            reply_markup=get_quests_menu()
        )
# --- КВІТКА РОЗКВІТЛА (ЗАВЕРШЕННЯ ЦІЛІ) ---
    elif message.text == "🌸 Квітка розквітла":
        player = get_player(user_id)
        plants = player["quests"].get("plants", [])

        if not plants:
            bot.send_message(message.chat.id, "🌲Лісовик🌲: У тебе в теплиці порожньо, нічому цвісти!", parse_mode="HTML")
            return

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for p in plants:
            markup.add(types.KeyboardButton(p['task']))
        markup.add(types.KeyboardButton("🔙 Назад до квестів"))

        msg = bot.send_message(
            message.chat.id, 
            "🌲Лісовик🌲: Охохо! Невже якась із рослин дала плоди? Обери, що саме розквітло:", 
            reply_markup=markup, 
            parse_mode="HTML"
        )
        bot.register_next_step_handler(msg, process_harvest_plant)

    # --- ВИРВАТИ БАОБАБ (СКАСУВАННЯ ЦІЛІ) ---
    elif message.text in ["🪓 Вирвати баобаб", "🌱 Вирвати баобаб"]:
        player = get_player(user_id)
        plants = player["quests"].get("plants", [])

        if not plants:
            bot.send_message(message.chat.id, "🌲Лісовик🌲: Тут немає ніяких баобабів, теплиця порожня!", parse_mode="HTML")
            return

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for p in plants:
            markup.add(types.KeyboardButton(p['task']))
        markup.add(types.KeyboardButton("🔙 Назад до квестів"))

        msg = bot.send_message(
            message.chat.id, 
            "🌲Лісовик🌲: Ех, закинув рослину і вона перетворилася на загарбницький баобаб? Обери, що треба вирвати з корінням:", 
            reply_markup=markup, 
            parse_mode="HTML"
        )
        bot.register_next_step_handler(msg, process_remove_plant)
    # --- СУВОЇ ЗАВДАНЬ ---
    elif message.text == "📜 Сувої завдань":
        player = get_player(user_id)
        scrolls = player["quests"].get("scrolls", [])
        active_scrolls = [s for s in scrolls if s["done_count"] < s["max_count"]]
        
        status_text = (
            "📜 <b>Книга Сувоїв Грінвуду</b>\n\n"
            "<b>🪷Лілі Понд🪷</b>: Використовуй сувої, аби запечатати обіцянку собі про виконання завдання. "
            "Вони ідеально підходять для справ із чітким дедлайном або кількома повтореннями.\n\n"
            "📌 <b>Твої активні сувої:</b>\n"
        )
        
        if not active_scrolls:
            status_text += "Твій стіл порожній. Час запечатати першу угоду!"
        else:
            for idx, s in enumerate(active_scrolls, 1):
                status_text += f"{idx}. {s['emoji']} <b>{s['task']}</b> — ({s['done_count']}/{s['max_count']}) | {float(s['xp_per_once']):.1f} XP за крок (⏰ Дедлайн: {s['deadline']})\n"
                
        status_text += "\n👇 <b>Обери магічну дію:</b>"
        bot.send_message(message.chat.id, status_text, parse_mode="HTML", reply_markup=get_scrolls_menu())

    elif message.text == "➕ Створити сувой":
        guide = (
            "✍️ <b>Запечатування нового сувою</b>\n\n"
            "<b>🪷Лілі Понд🪷</b>: Давай розправимо чистий пергамент! Будь ласка, напиши умови "
            "твого квесту одним рядком за цим магічним шаблоном:\n\n"
            "📖 [Емодзі сфери] [Кратність] [Бали за крок] [Дедлайн ДД.ММ] [Опис справи та Нагорода]\n"
            "• Емодзі сфери: 💪, 🧠, 🎨, 💵, 🤝\n"
            "• Кратність (кількість разів для виконання).\n"
            "• Бали за крок від 4 до 14.\n"
            "• Дедлайн у форматі ДД.ММ.\n"
            "• Опис або назва справи\n\n"
            "📌 Приклад:\n"
            "<code>🧠 3 10 22.07 Прочитати 50 сторінок книги (Нагорода: замовити нову сукню)</code>\n\n"
            "Напиши <code>🔙 Назад до квестів</code> для повернення."
        )
        msg = bot.send_message(message.chat.id, guide, parse_mode="HTML", reply_markup=types.ForceReply(selective=True))
        bot.register_next_step_handler(msg, process_create_scroll)
        
    elif message.text == "✅ Виконати завдання":
        player = get_player(user_id)
        scrolls = player["quests"].get("scrolls", [])
        active_scrolls = [s for s in scrolls if s["done_count"] < s["max_count"]]
        
        if not active_scrolls:
            bot.send_message(message.chat.id, "<b>🪷Лілі Понд🪷</b>: На твоїх полицях немає активних сувоїв для виконання.", parse_mode="HTML")
            return
            
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for s in active_scrolls:
            markup.add(types.KeyboardButton(s['task']))
        markup.add(types.KeyboardButton("🔙 Назад до квестів"))
        
        msg = bot.send_message(
            message.chat.id, 
            "<b>🪷Лілі Понд🪷</b>: Обери сувой, у якому ти сьогодні зробила крок вперед:", 
            reply_markup=markup, 
            parse_mode="HTML" 
        )
        bot.register_next_step_handler(msg, process_complete_scroll)

    elif message.text == "🔥 Спалити сувой":
        player = get_player(user_id)
        scrolls = player["quests"].get("scrolls", [])
        active_scrolls = [s for s in scrolls if s["done_count"] < s["max_count"]]
        
        if not active_scrolls:
            bot.send_message(message.chat.id, "<b>🪷Лілі Понд🪷</b>: Тобі нема чого спалювати, твій стіл порожній!", parse_mode="HTML")
            return
            
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for s in active_scrolls:
            markup.add(types.KeyboardButton(s['task']))
        markup.add(types.KeyboardButton("🔙 Назад до квестів"))
        
        msg = bot.send_message(
            message.chat.id, 
            "<b>🪷Лілі Понд🪷</b>: Який сувой ти хочеш спалити у синьому вогні без отримання досвіду?", 
            parse_mode="HTML", 
            reply_markup=markup
        )
        bot.register_next_step_handler(msg, process_delete_scroll)

    # --- ЩОДЕННІ РИТУАЛИ ---
    elif message.text == "🔄 Щоденні ритуали":
        player = get_player(user_id)
        rituals = player["quests"].get("rituals", [])
        
        kyiv_time = datetime.now(ZoneInfo("Europe/Kyiv"))
        kyiv_days = {0: "пн", 1: "вт", 2: "ср", 3: "чт", 4: "пт", 5: "сб", 6: "нд"}
        today_day = kyiv_days[kyiv_time.weekday()]
        today_date = kyiv_time.strftime("%d.%m")
        
        status_text = "🔄 <b>Твої магічні ритуали Грінвуду</b>\n"
        status_text += f"📅 Сьогодні: <b>{today_date}, {today_day}</b>\n" 
        status_text += "────────────────────\n\n"
        
        if not rituals:
            status_text += "✨ Ти ще не створила жодного щоденного ритуалу, твоя книга порожня."
        else:
            for r in rituals:
                is_active_today = today_day in r.get("days", [])
                
                if r.get("done_today", False):
                    status = "✅"
                elif is_active_today:
                    status = "⏳"
                else:
                    status = "💤"
                
                days_list = ", ".join(r.get("days", []))
                
                status_text += f"{status} {r['emoji']} <b>{r['task']}</b> ({float(r['xp']):.1f} XP)\n"
                status_text += f"    └── Дні: {days_list}\n\n"
                
        status_text += "────────────────────\n"
        status_text += "👇 <b>Обери магічну дію для ритуалів:</b>"
        bot.send_message(message.chat.id, status_text, parse_mode="HTML", reply_markup=get_rituals_menu())

    elif message.text == "➕ Створити ритуал":
        guide = (
            "✍️ <b>Створення щоденного ритуалу</b>\n\n"
            "<b>🪷Лілі Понд🪷</b>: Напиши умови одним рядком за цим шаблоном:\n\n"
            "📖 [💪, 🧠, 🎨, 💵, 🤝] [Бали (1-14)] [Дні] [Назва справи]\n"
            "• <b>Дні</b> перерахуй через кому (<code>пн,вт,ср,чт,пт,сб,нд</code>) або напиши <code>щодня</code>.\n\n"
            "📌 <b>Приклади:</b>\n"
            "<code>🧠 5 пн,ср,пт Читати книгу</code>\n"
            "<code>💪 8 щодня Ранкова руханка</code>\n"
        )
        
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("🔙 Назад до квестів"))
        
        msg = bot.send_message(message.chat.id, guide, parse_mode="HTML", reply_markup=markup)
        bot.register_next_step_handler(msg, process_create_ritual)

    elif message.text == "✅ Виконати ритуал":
        player = get_player(user_id)
        rituals = player["quests"].get("rituals", [])
        
        kyiv_day = ["пн", "вт", "ср", "чт", "пт", "сб", "нд"][datetime.now(ZoneInfo("Europe/Kyiv")).weekday()]
        available = [r for r in rituals if kyiv_day in r.get("days", []) and not r.get("done_today", False)]
        
        if not available:
            bot.send_message(
                message.chat.id, 
                "<b>🪷Лілі Понд🪷</b>: На сьогодні немає активних ритуалів, які б чекали виконання! Відпочивай або займайся іншими справами.", 
                parse_mode="HTML"
            )
            return
            
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for r in available:
            markup.add(types.KeyboardButton(r['task']))
        markup.add(types.KeyboardButton("🔙 Назад до квестів"))
        
        msg = bot.send_message(
            message.chat.id, 
            "<b>🪷Лілі Понд🪷</b>: Який із сьогоднішніх ритуалів ти завершила? Обери кнопку:", 
            reply_markup=markup, 
            parse_mode="HTML"
        )
        bot.register_next_step_handler(msg, process_complete_ritual)

    # --- ТЕПЛИЦЯ ---
    elif message.text in ["🌱 Теплиця Грінвуду", "🌱 Теплиця"]:
        player = get_player(user_id)
        plants = player["quests"].get("plants", [])
        
        status_text = "🌱 <b>Теплиця Грінвуду</b>\n"
        status_text += "────────────────────\n"
        status_text += (
            "<b>🌲Лісовик🌲</b>: Завітав до моєї теплиці? Поглянь на ці магічні насінини... "
            "Щоб кожна з них розквітла, потрібна чітка ціль (SMART) і дедлайн. "
            "Опиши її чітко, доглядай, а коли вона розквітне — збирай плоди!\n\n"
        )
        
        status_text += "🌱 <b>Твої поточні магічні рослини:</b>\n"
        if not plants:
            status_text += "<i>Поки що теплиця порожня. Час посадити перше насіння!</i>"
        else:
            for idx, p in enumerate(plants, 1):
                status_text += f"{idx}. {p['emoji']} <b>{p['task']}</b> — (Дедлайн: {p['deadline']})\n"
                
        bot.send_message(message.chat.id, status_text, parse_mode="HTML", reply_markup=get_greenhouse_menu())

elif message.text == "🌱 Посадити насіння":
        intro_text = (
            "🌲Лісовик🌲: Грррм... Хто це тут тупає по моєму священному моху? А, це ти... Знову прийшов щось саджати?\n\n"
            "Слухай сюди уважно! <b>Моя теплиця — це не смітник для дрібниць!</b>\n\n"
            "❌ Не смій саджати сюди всілякий дріб'язок на п'ять хвилин накшталт <i>\"помити посуд\"</i> чи <i>\"винести сміття\"</i>. Для цієї щоденної метушні у тебе є ритуали та сувої!\n"
            "❌ І навіть не думай заривати сюди дурні фантазії типу <i>\"стати володарем Всесвіту до завтра\"</i>! Твоє насіння просто вибухне від напруги і спалить мені весь ґрунт!\n\n"
            "Сюди ми саджаємо тільки <b>Справжні Магічні Рослини (SMART-цілі)</b> — щось вагоме, вимірюване і реальне!\n\n"
            "Перш ніж кинути зерня в землю, дай собі чесну відповідь:\n"
            "🌱 <b>Чіткість (S):</b> Що САМЕ це за рослина?\n"
            "📏 <b>Вимірність (M):</b> Який у неї буде плід? (Скільки сторінок, гривень, занять?)\n"
            "🪨 <b>Реальність (A):</b> Чи вистачить у тебе сил і ґрунту це витягнути?\n\n"
            "────────────────────\n"
            "✍️ <b>Кидай насіння в один рядок через похилу риску (<code>/</code>):</b>\n"
            "<b><code>Смайлик Сфери / Назва та плід / Дата (ДД.ММ)</code></b>\n\n"
            "Використовуй один зі смайликів сфери:\n"
            "💪 — Здоров'я | 🧠 — Мудрість | 🎨 — Творчість | 💵 — Фінанси | 🤝 — Зв'язки\n\n"
            "💬 <i>Приклади від мудрого Лісника:</i>\n"
            "• <code>🧠 / Прочитати 3 книги з магії (300 стор) / 15.11</code>\n"
            "• <code>💵 / Заощадити 5000 золотих / 01.12</code>\n"
            "• <code>💪 / Пройти 20 тренувань у залі / 30.10</code>"
        )
        
        # Створюємо кнопку скасування
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("🔙 Назад до квестів"))
        
        msg = bot.send_message(message.chat.id, intro_text, parse_mode="HTML", reply_markup=markup)
        bot.register_next_step_handler(msg, process_plant_creation)

    # --- РЕЖИМ ДОДАВАННЯ СПРАВИ ---
    elif message.text == "➕ Додати Справу":
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
# --- ЛОГІКА РОБОТИ ІЗ СУВОЯМИ ---

def process_create_scroll(message):
    user_id = str(message.from_user.id)
    text = message.text.strip() if message.text else ""
    
    if text == "🔙 Назад до квестів":
        bot.send_message(message.chat.id, "Створення скасовано, повертаємось.", reply_markup=get_scrolls_menu())
        return

    # Очищаємо вхідний текст від кольорів шкіри емодзі
    cleaned_text = clean_skin_tones(text)
    # Тепер магічний вираз дозволяє пробіли всередині переліку днів тижня!
    match = re.match(r"^([^\w\s]+)\s+(\d+)\s+([а-я,\sієґу]+)\s+(.+)$", cleaned_text, re.IGNORECASE)
    
    if not match:
        msg = bot.send_message(
            message.chat.id, 
            "✨ <b>🪷Лілі Понд🪷</b>: Ой, щось пішло не так із чорнилом. Спробуй ще раз за моїм шаблоном або напиши `🔙 Назад до квестів`, щоб скасувати: \n`[Емодзі] [Кратність] [Бали] [Дедлайн ДД.ММ] [Опис]`",
            parse_mode="HTML"
        )
        bot.register_next_step_handler(msg, process_create_scroll)
        return
        
    emoji, max_count, xp_per_once, deadline, task_desc = match.groups()
    max_count = int(max_count)
    xp_per_once = int(xp_per_once)
    task_desc = task_desc.strip()
    
    if xp_per_once < 4 or xp_per_once > 14:
        msg = bot.send_message(message.chat.id, "<b>🪷Лілі Понд🪷</b>: Пам'ятай, що магічний ліміт балів за одне виконання має бути від 4 до 14! Спробуй ще раз ввести умови:")
        bot.register_next_step_handler(msg, process_create_scroll)
        return

    player = get_player(user_id)
    
    scrolls = player["quests"].get("scrolls", [])
    if any(clean_skin_tones(s["task"]).lower() == task_desc.lower() and s["done_count"] < s["max_count"] for s in scrolls):
        msg = bot.send_message(message.chat.id, f"<b>🪷Лілі Понд🪷</b>:  У твоїх хроніках уже є активний сувой з назвою \"{task_desc}\". Придумай іншу назву або заверши попередній квест ")
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
        f"<b>🪷Лілі Понд🪷</b>: Новий сувой успішно запечатано у твою книгу квестів. Я нагадуватиму тобі про нього!\n\n{emoji} {task_desc}\n• Повторень: {max_count}\n• Сила кроку: {xp_per_once} XP\n• Термін: до {deadline}",
        parse_mode="HTML",
        reply_markup=get_scrolls_menu()
    )

def process_complete_scroll(message):
    user_id = str(message.from_user.id)
    text = message.text.strip() if message.text else ""
    
    if text == "🔙 Назад до квестів":
        bot.send_message(message.chat.id, "Повертаємось.", reply_markup=get_scrolls_menu())
        return
        
    task_clean = clean_skin_tones(text.strip())
    player = get_player(user_id)
    scrolls = player["quests"].get("scrolls", [])
    
    found_scroll = None
    for s in scrolls:
        if clean_skin_tones(s["task"]).strip().lower() == task_clean.lower() and s["done_count"] < s["max_count"]:
            found_scroll = s
            break
            
    if not found_scroll:
        bot.send_message(message.chat.id, "✨ <b>🪷Лілі Понд🪷</b>: Я не знайшла такого активного сувою у твоїх записах. Спробуй обрати з кнопок на клавіатурі!", reply_markup=get_scrolls_menu())
        return
        
    found_scroll["done_count"] += 1
    xp_to_add = found_scroll["xp_per_once"]
    
    sphere_key = None
    scroll_emoji = clean_skin_tones(found_scroll["emoji"])
    for key, sphere in player["spheres"].items():
        if clean_skin_tones(sphere["emoji"]) == scroll_emoji:
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
            lvl_up_text += f"\n⚡️ <b>РІВЕНЬ📈</b>: Сфера {sphere['name']} піднялася до {sphere['lvl']} рівня! 🎉"
            
        new_global_lvl = int(float(player["xp_total"]) // 50) + 1
        if new_global_lvl > int(player["level"]):
            player["level"] = new_global_lvl
            lvl_up_text += f"\n🌟 <b>НОВИЙ РІВЕНЬ ГЕРОЯ!</b>: Твій рівень зріс до {new_global_lvl}! 🧙‍♂️"
            
    report = f"✨ <b>🪷Лілі Понд🪷</b>: Чудовий крок! Записую прогрес у твій сувой! \n\n{found_scroll['emoji']} {found_scroll['task']} ({found_scroll['done_count']}/{found_scroll['max_count']})\n🔋 Отримано: <b>+{xp_to_add:.1f} XP </b>!"
    
    if found_scroll["done_count"] == found_scroll["max_count"]:
        report += f"\n\n🎉 <b>СУВОЙ ПОВНІСТЮ ЗАВЕРШЕНО!</b>\n <b>🪷Лілі Понд🪷</b>:  Чудова робота! "
        
    if lvl_up_text:
        report += "\n\n────────────────────" + lvl_up_text
        
    update_player(user_id, player)
    bot.send_message(message.chat.id, report, parse_mode="HTML", reply_markup=get_scrolls_menu())

def process_delete_scroll(message):
    user_id = str(message.from_user.id)
    text = message.text.strip() if message.text else ""
    
    if text == "🔙 Назад до квестів":
        bot.send_message(message.chat.id, "Повертаємось.", reply_markup=get_scrolls_menu())
        return
        
    task_clean = clean_skin_tones(text.strip())
    player = get_player(user_id)
    scrolls = player["quests"].get("scrolls", [])
    
    new_scrolls = [s for s in scrolls if not (clean_skin_tones(s["task"]).strip().lower() == task_clean.lower() and s["done_count"] < s["max_count"])]
    
    if len(scrolls) == len(new_scrolls):
        bot.send_message(message.chat.id, "<b>🪷Лілі Понд🪷</b>:  Хм, такого сувою немає на твоєму столі. Спробуй обрати з кнопок! ", reply_markup=get_scrolls_menu())
        return
        
    player["quests"]["scrolls"] = new_scrolls
    update_player(user_id, player)
    
    bot.send_message(message.chat.id, "🔥 Сувой безслідно згорів у синьому полум'ї. Цього завдання більше не існує.", reply_markup=get_scrolls_menu())
def process_create_ritual(message):
    user_id = str(message.from_user.id)
    text = message.text.strip() if message.text else ""
    
    if text in ["🔙 Назад до квестів", "🔙 Назад"]:
        bot.send_message(message.chat.id, "Повертаємось до свитку ритуалів.", reply_markup=get_rituals_menu())
        return
        
    cleaned_text = clean_skin_tones(text)
    
    # Розбиваємо рядок по пробілах
    parts = cleaned_text.split()
    
    # Нам потрібно мінімум 4 частини: [Емодзі] [Бали] [Дні...] [Назва...]
    if len(parts) < 4:
        msg = bot.send_message(
            message.chat.id, 
            "<b>🪷Лілі Понд🪷</b>: «Ой, не вистачає деталей. Перевір формат і спробуй ще раз за шаблоном:\n<code>[Емодзі] [Бали] [Дні] [Назва]</code>»",
            parse_mode="HTML"
        )
        bot.register_next_step_handler(msg, process_create_ritual)
        return
        
    emoji = parts[0]
    
    # Перевіряємо бали
    try:
        xp = int(parts[1])
    except ValueError:
        msg = bot.send_message(
            message.chat.id, 
            "<b>🪷Лілі Понд🪷</b>: «Другим параметром мають бути цифри (бали від 4 до 14). Спробуй ще раз:»",
            parse_mode="HTML"
        )
        bot.register_next_step_handler(msg, process_create_ritual)
        return
        
    if xp < 4 or xp > 14:
        msg = bot.send_message(
            message.chat.id, 
            "<b>🪷Лілі Понд🪷</b>: Сила ритуалу має бути в межах від 4 до 14! Спробуй ще раз:", 
            parse_mode="HTML"
        ) 
        bot.register_next_step_handler(msg, process_create_ritual)
        return

    # Збираємо все, що йде ПІСЛЯ балів
    remaining_text = " ".join(parts[2:])
    valid_days = ["пн", "вт", "ср", "чт", "пт", "сб", "нд"]
    
    if remaining_text.lower().startswith("щодня"):
        final_days = valid_days
        task_desc = remaining_text[5:].strip()
    else:
        # Надійна розбірка днів (підтримує "пн,ср,пт", "пн, ср, пт", "пн ср пт")
        days_accumulated = []
        words = remaining_text.split()
        idx = 0
        
        for word in words:
            # Розбиваємо кожне слово по комах, якщо вони зклеєні (наприклад "пн,ср,пт")
            sub_tokens = [t.strip().lower() for t in word.split(",") if t.strip()]
            
            # Перевіряємо, чи всі елементи у слові є валідними днями
            if sub_tokens and all(t in valid_days for t in sub_tokens):
                for t in sub_tokens:
                    if t not in days_accumulated:
                        days_accumulated.append(t)
                idx += 1
            else:
                break # Зустріли назву справи!

        if not days_accumulated:
            msg = bot.send_message(
                message.chat.id, 
                "<b>🪷Лілі Понд🪷</b>: «Я не змогла розпізнати дні тижня (пн, вт...). Спробуй знову:»",
                parse_mode="HTML"
            )
            bot.register_next_step_handler(msg, process_create_ritual)
            return
            
        final_days = days_accumulated
        task_desc = " ".join(words[idx:]).strip()

    if not task_desc:
        msg = bot.send_message(
            message.chat.id, 
            "<b>🪷Лілі Понд🪷</b>: «А де ж сама назва ритуалу? Напиши умови ще раз, будь ласка:»",
            parse_mode="HTML"
        )
        bot.register_next_step_handler(msg, process_create_ritual)
        return

    player = get_player(user_id)
    rituals = player["quests"].get("rituals", [])
    
    if any(clean_skin_tones(r["task"]).lower() == task_desc.lower() for r in rituals):
        msg = bot.send_message(
            message.chat.id, 
            "<b>🪷Лілі Понд🪷</b>: «У твоїй книзі вже є ритуал з такою назвою. Дай йому трохи інше ім'я:»",
            parse_mode="HTML"
        )
        bot.register_next_step_handler(msg, process_create_ritual)
        return
        
    new_ritual = {
        "emoji": emoji,
        "xp": float(xp),
        "days": final_days,
        "task": task_desc,
        "done_today": False
    }
    
    player["quests"]["rituals"].append(new_ritual)
    update_player(user_id, player)
    
    bot.send_message(
        message.chat.id,
        f"✅ <b>Новий щоденний ритуал закарбовано!</b>\n\n"
        f"{emoji} <b>{task_desc}</b>\n"
        f"• Нагорода: +{xp} XP\n"
        f"• Дні виконання: {', '.join(final_days)}",
        parse_mode="HTML",
        reply_markup=get_rituals_menu()
    )
def process_complete_ritual(message):
    user_id = str(message.from_user.id)
    text = message.text.strip() if message.text else ""
    
    # 1. Якщо гравець натиснув кнопку скасування
    if text in ["🔙 Назад до квестів", "🔙 Назад", "/start"]:
        bot.send_message(message.chat.id, "Повертаємось до свитку ритуалів.", reply_markup=get_rituals_menu())
        return

    player = get_player(user_id)
    rituals = player["quests"].get("rituals", [])
    
    clean_input = clean_skin_tones(text).lower()
    
    # 2. Пошук ритуалу за назвою
    found = None
    for r in rituals:
        task_name = clean_skin_tones(r.get("task", "")).lower()
        if task_name == clean_input:
            found = r
            break
    
    # Якщо назва трохи відрізняється — шукаємо за входженням
    if not found:
        for r in rituals:
            task_name = clean_skin_tones(r.get("task", "")).lower()
            if task_name in clean_input or clean_input in task_name:
                found = r
                break
        
    if not found:
        bot.send_message(
            message.chat.id, 
            "<b>🪷Лілі Понд🪷</b>: «Хм, я не знайшла ритуалу з такою назвою у твоєму списку. Обирай із запропонованих кнопок нижче!»", 
            reply_markup=get_rituals_menu(),
            parse_mode="HTML"
        )
        return
        
    if found.get("done_today", False):
        bot.send_message(
            message.chat.id, 
            f"<b>🪷Лілі Понд🪷</b>: «Ритуал <b>{found['task']}</b> вже закарбований як виконаний на сьогодні!»", 
            reply_markup=get_rituals_menu(),
            parse_mode="HTML"
        )
        return
        
    # 3. Зараховуємо виконання
    found["done_today"] = True
    earned_xp = float(found.get("xp", 5.0))
    player["xp_total"] += earned_xp
    
    # Нараховуємо XP у відповідні сфери
    ritual_emoji = found.get("emoji", "")
    for char in ritual_emoji:
        if char in player.get("spheres", {}):
            player["spheres"][char] += earned_xp
            
    update_player(user_id, player)
    
    bot.send_message(
        message.chat.id, 
        f"✅ <b>Ритуал виконано!</b>\n\n"
        f"{ritual_emoji} <b>{found['task']}</b> успішно завершено!\n"
        f"✨ Тобі зараховано <b>+{earned_xp} XP</b> у загальний досвід!", 
        reply_markup=get_rituals_menu(),
        parse_mode="HTML"
    )
    def process_plant_creation(message):
    user_id = message.from_user.id
    text = message.text.strip()

    # Якщо натиснули кнопку скасування
    if text in ["🔙 Назад", "🔙 Назад до квестів", "/cancel"]:
        bot.send_message(message.chat.id, "🌲Лісовик🌲: Хм, ну й добре. Менше бур'янів у теплиці!", reply_markup=get_greenhouse_menu())
        return

    # Розділяємо рядок за допомогою риски /
    parts = [p.strip() for p in text.split("/")]

    if len(parts) != 3:
        msg = bot.send_message(
            message.chat.id,
            "🌲Лісовик🌲: Грррм! Ти взагалі мене слухав? <b>Треба рівно дві риски / !</b>\n\n"
            "Напиши у форматі: <code>Емодзі / Назва цілі / ДД.ММ</code>\n"
            "Спробуй ще раз або натисни кнопку повернення:",
            parse_mode="HTML"
        )
        bot.register_next_step_handler(msg, process_plant_creation)
        return

    raw_emoji, task, deadline = parts[0], parts[1], parts[2]

    # Чистимо тони шкіри
    emoji = raw_emoji
    for skin_tone, clean_emoji in replacements.items():
        emoji = emoji.replace(skin_tone, clean_emoji)

    valid_emojis = ["💪", "🧠", "🎨", "💵", "🤝"]
    if emoji not in valid_emojis:
        msg = bot.send_message(
            message.chat.id,
            "🌲Лісовик🌲: Що це за дивна магія? Використовуй тільки правильні смайлики: 💪, 🧠, 🎨, 💵, 🤝\nСпробуй ще раз:",
            parse_mode="HTML"
        )
        bot.register_next_step_handler(msg, process_plant_creation)
        return

    # Зберігаємо рослину
    player = get_player(user_id)
    if "plants" not in player["quests"]:
        player["quests"]["plants"] = []

    player["quests"]["plants"].append({
        "emoji": emoji,
        "task": task,
        "deadline": deadline
    })
    save_player(user_id, player)

    bot.send_message(
        message.chat.id, 
        f"🌲Лісовик🌲: Ну добре, закопали твоє зерно <b>{emoji} {task}</b>! Тепер поливай його своєю працею до {deadline}!", 
        parse_mode="HTML", 
        reply_markup=get_greenhouse_menu()
    )
# Функція для "Квітка розквітла"
def process_harvest_plant(message):
    user_id = message.from_user.id
    task_name = message.text.strip()

    if task_name in ["🔙 Назад", "🔙 Назад до квестів"]:
        bot.send_message(message.chat.id, "Повертаємось до теплиці.", reply_markup=get_greenhouse_menu())
        return

    player = get_player(user_id)
    plants = player["quests"].get("plants", [])

    # Шукаємо рослину за назвою
    plant_to_remove = None
    for p in plants:
        if p["task"] == task_name:
            plant_to_remove = p
            break

    if plant_to_remove:
        plants.remove(plant_to_remove)
        save_player(user_id, player)

        bot.send_message(
            message.chat.id,
            f"🌺 <b>ВРОЖАЙ ЗІБРАНО!</b> 🌺\n\n"
            f"🌲Лісовик🌲: Оце так диво! Твоя рослина <b>{plant_to_remove['emoji']} {plant_to_remove['task']}</b> розквітла прекрасним цвітом!\n"
            f"Ти отримуєш заслужену гордість та магічну енергію!",
            parse_mode="HTML",
            reply_markup=get_greenhouse_menu()
        )
    else:
        bot.send_message(message.chat.id, "🌲Лісовик🌲: Я не знайшов такої рослини. Спробуй ще раз з меню.", reply_markup=get_greenhouse_menu())


# Функція для "Вирвати баобаб"
def process_remove_plant(message):
    user_id = message.from_user.id
    task_name = message.text.strip()

    if task_name in ["🔙 Назад", "🔙 Назад до квестів"]:
        bot.send_message(message.chat.id, "Повертаємось до теплиці.", reply_markup=get_greenhouse_menu())
        return

    player = get_player(user_id)
    plants = player["quests"].get("plants", [])

    plant_to_remove = None
    for p in plants:
        if p["task"] == task_name:
            plant_to_remove = p
            break

    if plant_to_remove:
        plants.remove(plant_to_remove)
        save_player(user_id, player)

        bot.send_message(
            message.chat.id,
            f"🪓 <b>БАОБАБ ВИРВАНО!</b>\n\n"
            f"🌲Лісовик🌲: Хрусь! Вирвали <b>{plant_to_remove['task']}</b> з корінням. "
            f"Тепер цей ґрунт знову чистий для нових SMART-цілей!",
            parse_mode="HTML",
            reply_markup=get_greenhouse_menu()
        )
    else:
        bot.send_message(message.chat.id, "🌲Лісовик🌲: Я не знайшов такого баобаба.", reply_markup=get_greenhouse_menu())
        
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
