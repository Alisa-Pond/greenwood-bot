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

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

def check_failed_deadlines():
    """Фонова перевірка протермінованих квестів о 00:01 за Києвом"""
    while True:
        try:
            # Перевіряємо час кожні 60 секунд
            kyiv_time = datetime.now(ZoneInfo("Europe/Kyiv"))
            
            # Спрацьовує рівно о 00:01 ночі
            if kyiv_time.hour == 0 and kyiv_time.minute == 1:
                # Шукаємо дедлайни, які закінчилися вчора
                yesterday_str = (kyiv_time - timedelta(days=1)).strftime("%d.%m")
                
                # Завантажуємо всіх гравців з Supabase
                response = supabase.table("players").select("*").execute()
                players = response.data if response.data else []
                
                for p_data in players:
                    user_id = p_data["user_id"]
                    hp_lost = 0
                    failed_tasks = []
                    
                    # 1. Перевірка Сувоїв
                    scrolls = p_data["quests"].get("scrolls", [])
                    updated_scrolls = []
                    for s in scrolls:
                        if s["done_count"] < s["max_count"] and s["deadline"] == yesterday_str:
                            # Штраф: половина від XP за крок помножена на невиконані повторення
                            remaining_steps = s["max_count"] - s["done_count"]
                            penalty = int((float(s["xp_per_once"]) / 2) * remaining_steps)
                            hp_lost += penalty
                            failed_tasks.append(f"📜 {s['task']} (не завершено кроків: {remaining_steps})")
                        else:
                            updated_scrolls.append(s)
                    
                    # 2. Перевірка Теплиці (Рослин)
                    plants = p_data["quests"].get("plants", [])
                    updated_plants = []
                    for pl in plants:
                        if pl["deadline"] == yesterday_str:
                            # За зів'ялу рослину штраф — фіксовано половина її вартості
                            penalty = int(float(pl.get("xp", 20)) / 2)
                            hp_lost += penalty
                            failed_tasks.append(f"🌱 {pl['task']} (Зів'яла в теплиці)")
                        else:
                            updated_plants.append(pl)
                    
                    # Якщо є штрафи — оновлюємо гравця
                    if hp_lost > 0:
                        p_data["quests"]["scrolls"] = updated_scrolls
                        p_data["quests"]["plants"] = updated_plants
                        
                        # Знімаємо загальний XP персонажа (або ХП, якщо додаси окрему шкалу здоров'я)
                        p_data["xp_total"] = max(0.0, float(p_data["xp_total"]) - hp_lost)
                        
                        # Зберігаємо зміни в Supabase
                        update_player(user_id, p_data)
                        
                        # Надсилаємо магічне сповіщення в Телеграм
                        tasks_list = "\n".join(failed_tasks)
                        notification = (
                            f"🌌 <b>Нічний туман Грінвуду розсіявся...</b>\n\n"
                            f"На жаль, час для виконання деяких угод вичерпано:\n{tasks_list}\n\n"
                            f"💔 Твій персонаж втрачає <b>-{hp_lost:.1f} XP</b> через пропущені дедлайни. Будь обережнішою!"
                        )
                        try:
                            bot.send_message(user_id, notification, parse_mode="HTML")
                        except Exception:
                            pass # Якщо користувач заблокував бота
                            
            # Спимо хвилину, щоб не спамити базу перевірками в ту саму хвилину
            time.sleep(60)
        except Exception as e:
            print(f"Помилка у фоновому потоці дедлайнів: {e}")
            time.sleep(60)

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
        "plants": []      # Магічне насіння в Теплиці=цілі
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
    markup.row(types.KeyboardButton("🪾 Вирвати бур'ян"), types.KeyboardButton("🔙 Назад до квестів"))
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
        
    elif message.text == "🎯 Мої Квести" or message.text == "🔙 Назад до квестів":
        player = get_player(user_id)
        
        # Оновлюємо дату при КВЕНЧЕННІ кнопки (Київський час, формат ДД.ММ)
        today_str = datetime.now(ZoneInfo("Europe/Kyiv")).strftime("%d.%m")
        
        scrolls = player["quests"].get("scrolls", [])
        active_scrolls = [s for s in scrolls if s["done_count"] < s["max_count"]]
        rituals = player["quests"].get("rituals", [])
        plants = player["quests"].get("plants", [])
        
        status_text = "🎯 <b>Магічний Органайзер Грінвуду</b>\n"
        status_text += "────────────────────\n\n"
        
        # Блок Сувоїв
        status_text += "📜 <b>Активні сувої:</b>\n"
        if not active_scrolls:
            status_text += "• <i>Немає активних сувоїв</i>\n"
        else:
            for s in active_scrolls:
                fire = " 🔥" if s['deadline'] == today_str else ""
                status_text += f"• {s['emoji']} {s['task']} ({s['done_count']}/{s['max_count']}) | до {s['deadline']}{fire}\n"
                
        status_text += "\n"
        
        # === Блок Ритуалів у головному меню квестів ===
        status_text += "🔄 <b>Активні ритуали на сьогодні:</b>\n"
        
        # Визначаємо поточний день тижня за Києвом
        kyiv_days = {0: "пн", 1: "вт", 2: "ср", 3: "чт", 4: "пт", 5: "сб", 6: "нд"}
        today_day = kyiv_days[datetime.now(ZoneInfo("Europe/Kyiv")).weekday()]
        
        # Беремо тільки ті ритуали, які мають виконуватися саме сьогодні
        today_rituals = [r for r in rituals if today_day in r.get("days", [])]
        
        if not today_rituals:
            status_text += "• <i>На сьогодні немає активних ритуалів</i>\n"
        else:
            for r in today_rituals:
                status = "✅" if r.get("done_today", False) else "⏳"
                status_text += f"• {status} {r['emoji']} {r['task']}\n"
                
        status_text += "\n"
        
        # Блок Теплиці
        status_text += "🌱 <b>Рослини в теплиці:</b>\n"
        if not plants:
            status_text += "• <i>Теплиця порожня</i>\n"
        else:
            for p in plants:
                # Перевіряємо дедлайн для рослин
                fire = " 🔥" if p['deadline'] == today_str else ""
                status_text += f"• {p['emoji']} {p['task']} | до {p['deadline']}{fire}\n"
                
        status_text += "\n────────────────────"
        
        bot.send_message(
            message.chat.id, 
            status_text, 
            parse_mode="HTML",
            reply_markup=get_quests_menu()
        )
        
    elif message.text == "🔙 Назад":
        bot.send_message(
            message.chat.id, 
            "🚪 Закляття телепортації виконано", 
            reply_markup=get_main_menu()
        )

   # --- СУВОЇ ЗАВДАНЬ ---
    elif message.text == "📜 Сувої завдань":
        player = get_player(user_id)
        scrolls = player["quests"].get("scrolls", [])
        active_scrolls = [s for s in scrolls if s["done_count"] < s["max_count"]]
        
        status_text = (
            "📜 <b> Книга Сувоїв Грінвуду </b> \n\n"
            "<b>🪷Лілі Понд🪷</b>: Використовуй сувої, аби запечати обіцянку собі про виконання завдання.  "
            "Вони ідеально підходять для планування справ, які мають чіткий дедлайн та/або потребують "
            "кількох повторень.\n\n"
            "📌<b>Твої активні сувої: </b> \n"
        )
        
        if not active_scrolls:
            status_text += "Твій стіл порожній. Час запечатати першу угоду!"
        else:
            for idx, s in enumerate(active_scrolls, 1):
                status_text += f"{idx}. {s['emoji']} <b>{s['task']}</b>— ({s['done_count']}/{s['max_count']}) | {float(s['xp_per_once']):.1f} XP за крок (⏰ Дедлайн: {s['deadline']})\n"
                
        status_text += "\n👇 <b>Обери магічну дію:</b>"
        bot.send_message(message.chat.id, status_text, parse_mode="HTML", reply_markup=get_scrolls_menu())

    elif message.text == "➕ Створити сувой":
        guide = (
            "✍️ <b>Запечатування нового сувою</b>\n\n"
            "<b>🪷Лілі Понд🪷</b>: Давай розправимо чистий пергамент! Будь ласка, напиши мне умови "
            "твого квесту одним рядком за цим магічним шаблоном:\n\n"
            "📖 [Емодзі сфери] [Кратність] [Бали за крок] [Дедлайн ДД.ММ] [Опис справи та твоя Нагорода]\n"
            "• Емодзі сфери: `💪`, `🧠`, `🎨`, `💵`, `🤝`\n"
            "• Кратність (к-сть разів необхідно виконати до дедлайну).\n"
            "• Бали за крок від <u> 4 до 14 </u>.\n"
            "• Дедлайн у форматі ДД.ММ.\n"
            "• Опис або назва, можеш написати нагороду за виконання яку собі обіцяєш \n\n"
            "📌Приклад:\n"
            "`🧠 3 10 22.07 Прочитати 50 сторінок книги (Нагорода: замовити нову сукню)`\n\n"
            "Напиши `🔙 Назад до квестів` для повернення)"
        )
        msg = bot.send_message(message.chat.id, guide, parse_mode="HTML", reply_markup=types.ForceReply(selective=True))
        bot.register_next_step_handler(msg, process_create_scroll)
        
    elif message.text == "✅ Виконати завдання":
        player = get_player(user_id)
        scrolls = player["quests"].get("scrolls", [])
        active_scrolls = [s for s in scrolls if s["done_count"] < s["max_count"]]
        
        if not active_scrolls:
            bot.send_message(message.chat.id, "<b>🪷Лілі Понд🪷</b>: На твоїх полицях немає активних сувоїв для виконання.")
            return
            
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for s in active_scrolls:
            markup.add(types.KeyboardButton(s['task']))
        markup.add(types.KeyboardButton("🔙 Назад до квестів"))
        
        msg = bot.send_message(
            message.chat.id, 
            "<b>🪷Лілі Понд🪷</b>: Обери сувой, у якому ти сьогодні зробила крок вперед, ти також може позначити його виконати через ➕ Додати Справу основного меню, написавши тільки назву:", 
            reply_markup=markup, 
            parse_mode="HTML" 
        )
        bot.register_next_step_handler(msg, process_complete_scroll)

    elif message.text == "🔥 Спалити сувой":
        player = get_player(user_id)
        scrolls = player["quests"].get("scrolls", [])
        active_scrolls = [s for s in scrolls if s["done_count"] < s["max_count"]]
        
        if not active_scrolls:
            bot.send_message(message.chat.id, "<b>🪷Лілі Понд🪷</b>:  Тобі нема чого спалювати, твій стіл порожній! ")
            return
            
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for s in active_scrolls:
            markup.add(types.KeyboardButton(s['task']))
        markup.add(types.KeyboardButton("🔙 Назад до квестів"))
        
        msg = bot.send_message(message.chat.id, "<b>🪷Лілі Понд🪷</b>:  Який сувой ти хочеш спалити у синьому вогні без отримання досвіду? ", parse_mode="HTML", reply_markup=markup)
        bot.register_next_step_handler(msg, process_delete_scroll)

    # --- ЩОДЕННІ РИТУАЛИ ---
    elif message.text == "🔄 Щоденні ритуали":
        player = get_player(user_id)
        rituals = player["quests"].get("rituals", [])
        
        # Визначаємо поточний день тижня та дату за Києвом
        kyiv_time = datetime.now(ZoneInfo("Europe/Kyiv"))
        kyiv_days = {0: "нд", 1: "пн", 2: "вт", 3: "ср", 4: "чт", 5: "пт", 6: "сб"} if kyiv_time.weekday() == 6 else {0: "пн", 1: "вт", 2: "ср", 3: "чт", 4: "пт", 5: "сб", 6: "нд"}
        # Простіший варіант без зсувів, оскільки weekday() завжди 0-6 (пн-нд):
        kyiv_days = {0: "пн", 1: "вт", 2: "ср", 3: "чт", 4: "пт", 5: "сб", 6: "нд"}
        today_day = kyiv_days[kyiv_time.weekday()]
        today_date = kyiv_time.strftime("%d.%m") # Отримуємо дату у форматі 19.07
        
        status_text = "🔄 <b>Твої магічні ритуали Грінвуду</b>\n"
        status_text += f"Сьогодні: <b>{today_date}, {today_day}</b> \n" 
        
        if not rituals:
            status_text += "✨ Ти ще не створила жодного щоденного ритуалу, твоя книга порожня."
        else:
            for r in rituals:
                # Перевіряємо, чи цей ритуал запланований на сьогодні
                is_active_today = today_day in r.get("days", [])
                
                # Позначка статусу: якщо виконано — ✅, якщо ні — ⏳.
                # Якщо ритуал сьогодні відпочиває, покажемо сіре коло ⚪ (або залиш ⏳, як тобі більше подобається)
                if r.get("done_today", False):
                    status = "✅"
                elif is_active_today:
                    status = "⏳"
                else:
                    status = "💤" # Ритуал відпочиває сьогодні
                
                # Перетворюємо список днів у красивий рядок, наприклад: "пн, ср, пт"
                days_list = ", ".join(r.get("days", []))
                
                status_text += f"{status} {r['emoji']} <b>{r['task']}</b> ({float(r['xp']):.1f} XP)\n"
                status_text += f"   └──  Дні: {days_list}\n\n"
                
                # Усі ці три рядки мають бути з однаковим відступом (16 пробілів або 4 таби)
                status_text += f"{status} {r['emoji']} <b>{r['task']}</b> ({float(r['xp']):.1f} XP)\n"
                status_text += f"    └── 📅 Дні: {days_list}\n\n"
                
        # ⚠️ ЗВЕРНИ УВАГУ: цей рядок має стояти на рівні з "if not rituals:" (8 пробілів від краю файлу)!
        bot.send_message(message.chat.id, status_text, parse_mode="HTML", reply_markup=get_rituals_menu())

    elif message.text == "➕ Створити ритуал":
                
        bot.send_message(message.chat.id, status_text, parse_mode="HTML", reply_markup=get_rituals_menu())

    # 👇 ОСЬ ЦЕЙ НОВИЙ БЛОК МИ ВСТАВЛЯЄМО СЮДИ (ЗБЕРІГАЙ 4 ПРОБІЛИ ВІДСТУПУ ПОПЕРЕДУ elif):
    elif message.text == "➕ Створити ритуал":
        guide = (
            "✍️ <b>Створення щоденного ритуалу</b>\n\n"
            "<b>🪷Лілі Понд🪷</b>: Саме час для створення нового ритуалу! Напиши умови одним рядком за цим шаблоном:\n\n"
            "📖 [💪, 🧠, 🎨, 💵, 🤝] [Бали (1-14] [Дні] [Назва справи]\n"
            "• <b>Дні</b> перерахуй через кому (<code>пн,вт,ср,чт,пт,сб,нд</code>) або напиши <code>щодня</code>.\n\n"
            "📌 <b>Приклади:</b>\n"
            "<code>🧠 5 пн,ср,пт Читати книгу</code>\n"
            "<code>💪 8 щодня Ранкова руханка</code>»\n\n"
            "💬 <i>Якщо передумала, просто натисни кнопку назад на клавіатурі.</i>"
        )
        
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("🔙 Назад до квестів"))
        
        msg = bot.send_message(message.chat.id, guide, parse_mode="HTML", reply_markup=markup)
        bot.register_next_step_handler(msg, process_create_ritual)

    # --- ТЕПЛИЦЯ ---
    elif message.text == "🌱 Теплиця Грінвуду":
        player = get_player(user_id)
        plants = player["quests"].get("plants", [])
        
        status_text = "🌱 <b>Теплиця Грінвуду</b>\n"
        status_text += "────────────────────\n"
        status_text += "<b>🌲Лісовик🌲</b>:  О, завітав-таки до моєї теплиці, юний магу! Поглянь на ці магічні насінини втрачених квітів Грінвуду... Щоб кожна з них проросла і розквітла, тобі знадобиться 5 елементів сили — твоя чітка ціль (SMART). Пам'ятай: насіння не зійде, якщо твоя мета розмита чи не має дедлайну! Опиши її чітко, доглядай, а коли вона розквітне в реальності — повертайся сюди і збирай плоди своєї магії! \n\n"
        
        status_text += "🌱 <b>Твої поточні магічні рослини:</b>\n"
        if not plants:
            status_text += "_Поки що теплиця порожня. Час посадити перше насіння!_"
        else:
            for idx, p in enumerate(plants, 1):
                status_text += f"{idx}. {p['emoji']} <b>{p['task']}</b> — [Нагорода: {float(p['xp']):.1f} XP] (Дедлайн: {p['deadline']})\n"
                
        status_text += "\n👇 <b>Обери магічну дію для саду:</b>"
        bot.send_message(message.chat.id, status_text, parse_mode="HTML", reply_markup=get_greenhouse_menu())

    # --- РЕЖИМ ДОДАВАННЯ СПРАВИ ---
    elif message.text == "➕ Додати Справу":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row(types.KeyboardButton("🧙‍♂️ Завершити звіт"), types.KeyboardButton("🔙 Назад"))
        
        guide = (
            "➕ <b>Режим магічного звіту активовано!</b>\n\n"
            "Запиши свої діяння (можна декілька, кожне з нового рядка) у форматі:\n"
            "`[Емодзі] [Бали від 4 до 14] [Опис справи]`\n\n"
            "✨ <b>Доступні сфери сили:</b>\n"
            "• 💪 — Здоров'я\n"
            "• 🧠 — Мудрість\n"
            "• 🎨 — Творчість\n"
            "• 💵 — Фінанси\n"
            "• 🤝 — Зв'язки\n\n"
        )
        msg = bot.send_message(message.chat.id, guide, parse_mode="HTML", reply_markup=markup)
        bot.register_next_step_handler(msg, process_activity)

# --- ЛОГІКА ДОДАВАННЯ ЗВИЧАЙНИХ СПРАВ ТА СУВОЇВ ---

def process_activity(message):
    user_id = str(message.from_user.id) 
    player = get_player(user_id)          
    text = message.text.strip() if message.text else ""

    # Обробка кнопки Назад
    if text == "🔙 Назад":
        bot.send_message(
            message.chat.id, 
            "✨ Звіт скасовано. Повертаємось до лісу.", 
            reply_markup=get_main_menu()
        )
        return
        
    if text == "🧙‍♂️ Завершити ритуал":
        bot.send_message(
            message.chat.id, 
            "📜 <b>Ритуал завершено. Твої діяння записані в хроніки Грінвуду.</b>", 
            parse_mode="HTML", 
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
    final_report = "📝 <b>Магічні підрахунки від Лілі Понд 🧚‍♀️:</b>\n\n"
    lvl_up_text = ""
    any_success = False
    
    scrolls = player["quests"].get("scrolls", [])
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
   
        # Очищаємо весь рядок користувача від відтінків шкіри для перевірок
        cleaned_line = clean_skin_tones(line)

        # 👑 1. МАГІЧНИЙ РАДАР СУВОЇВ (Перевірка на просте введення назви)
        matched_scroll = None
        for s in scrolls:
            scroll_task = clean_skin_tones(s["task"]).strip().lower()
            user_text = cleaned_line.strip().lower()
            
            if (scroll_task == user_text or scroll_task in user_text or user_text in scroll_task) and s["done_count"] < s["max_count"]:
                matched_scroll = s
                break
        
        # Якщо знайшли сувой за прямою назвою, штучно підставляємо дані з нього!
        if matched_scroll:
            detected_spheres = []
            scroll_emoji = clean_skin_tones(matched_scroll["emoji"])
            for key, sphere in player["spheres"].items():
                if clean_skin_tones(sphere["emoji"]) == scroll_emoji:
                    detected_spheres.append(key)
                    break
            
            base_xp = int(float(matched_scroll["xp_per_once"]))
            clean_task = matched_scroll["task"]
            
        else:
            # 📜 2. СТАНДАРТНИЙ ПАРСИНГ (Якщо це звичайний звіт на кшталт "🎨 4 Пси")
            detected_spheres = []
            for key, sphere in player["spheres"].items():
                base_emoji = clean_skin_tones(sphere["emoji"])
                if cleaned_line.startswith(base_emoji) or (len(cleaned_line) > 1 and cleaned_line[1] == base_emoji):
                    detected_spheres.append(key)
                    
            if not detected_spheres:
                final_report += f"❌ <code>{line[:20]}...</code> — До якої сфери варто віднести ці бали?\n"
                continue

            match = re.search(r'\d+', line)
            if not match:
                final_report += f"❌ <code>{line[:20]}...</code> — Наскільки важким було це закляття?\n"
                continue
                
            base_xp = int(match.group())
            
            if base_xp < 4 or base_xp > 14:
                final_report += f"❌ <code>{line[:20]}...</code> — Твої бали ({base_xp}) поза магічним лімітом (4-14).\n"
                continue

            clean_task = re.sub(r'^[^\w\s]+', '', line).strip()
            clean_task = re.sub(r'^\d+', '', clean_task).strip()
            if not clean_task: 
                clean_task = "Корисна дія"

            # Перевіряємо, чи цей стандартний звіт підходить під якийсь сувой
            for s in scrolls:
                if clean_skin_tones(s["task"]).strip().lower() == clean_task.lower() and s["done_count"] < s["max_count"]:
                    matched_scroll = s
                    break

        # 🎯 3. НАРАХУВАННЯ ДОСВІДУ ТА ОНОВЛЕННЯ ПРОГРЕСУ (Спільне для обох шляхів)
        any_success = True
        
        if matched_scroll:
            matched_scroll["done_count"] += 1
            xp_per_sphere = float(matched_scroll["xp_per_once"]) / len(detected_spheres)
            
            final_report += f"📜 <b>Сувой:</b> {matched_scroll['task']} ({matched_scroll['done_count']}/{matched_scroll['max_count']}):\n"
            if matched_scroll["done_count"] == matched_scroll["max_count"]:
                final_report += "🎉 <i>Сувой виконано повністю! Отримай свою реальну нагороду!</i>\n"
        else:
            xp_per_sphere = base_xp / len(detected_spheres)
            final_report += f"✨ <i>{clean_task}</i>:\n"
        
        for key in detected_spheres:
            sphere = player["spheres"][key]
            sphere["xp"] = float(sphere["xp"]) + xp_per_sphere
            player["xp_total"] = float(player["xp_total"]) + xp_per_sphere
            
            while sphere["xp"] >= float(sphere["max_xp"]):
                sphere["xp"] -= float(sphere["max_xp"])
                sphere["lvl"] += 1
                sphere["max_xp"] += 5.0
                lvl_up_text += f"⚡️ <b>РІВЕНЬ 📈:</b> Сфера {sphere['name']} піднялася до <b>{sphere['lvl']} рівня</b>! 🎉\n"
                
            final_report += f"  • {sphere['name']} +{xp_per_sphere:.1f} XP\n"
        final_report += "\n"

    new_global_lvl = int(float(player["xp_total"]) // 50) + 1
    if new_global_lvl > int(player["level"]):
        player["level"] = new_global_lvl
        lvl_up_text += f"\n🌟 <b>НОВИЙ РІВЕНЬ ГЕРОЯ!</b> {new_global_lvl}! 🧙‍♂️\n"

    if lvl_up_text:
        final_report += "────────────────────\n" + lvl_up_text

    if any_success:
        found_loot = []
        for loot_item in POSSIBLE_LOOT:
            if random.random() < LOOT_CHANCE:
                found_loot.append(loot_item)
                player["inventory"].append(loot_item)
        if found_loot:
            final_report += f"\n🎒 <b>НЕЙМОВІРНА УДАЧА!</b> {', '.join(found_loot)} додано в рюкзак!"

    final_report += "\n🔮 Я готова записувати твої наступні звершення або завершимо ритуал."
    
    update_player(user_id, player)
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(types.KeyboardButton("🧙‍♂️ Завершити ритуал"))
    
    msg = bot.send_message(message.chat.id, final_report, parse_mode="HTML", reply_markup=markup)
    bot.register_next_step_handler(msg, process_activity)

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(types.KeyboardButton("🧙‍♂️ Завершити звіт"), types.KeyboardButton("🔙 Назад"))
    
    msg = bot.send_message(message.chat.id, "Записано! Щось ще?", reply_markup=markup)
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
    match = re.match(r"^([^\w\s])\s+(\d+)\s+(\d+)\s+(\d{2}\.\d{2})\s+(.+)$", cleaned_text)
    
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
    
    # Перевірка, чи не захотіла ти повернутися назад
    if text == "🔙 Назад до квестів" or text == "🔙 Назад":
        bot.send_message(message.chat.id, "Повертаємось до свитку ритуалів.", reply_markup=get_rituals_menu())
        return
        
    cleaned_text = clean_skin_tones(text)
    
    # Магічний регулярний вираз розбирає рядок на частини: [Емодзі] [Бали] [Дні] [Назва]
    match = re.match(r"^([^\w\s])\s+(\d+)\s+([а-я,ієґу]+)\s+(.+)$", cleaned_text, re.IGNORECASE)
    
    if not match:
        msg = bot.send_message(
            message.chat.id, 
            "<b>🪷Лілі Понд🪷</b>: «Ой, заклинання створення не спрацювало. Перевір формат і спробуй ще раз за шаблоном:\n<code>[Емодзі] [Бали] [Дні] [Назва]</code>»",
            parse_mode="HTML"
        )
        bot.register_next_step_handler(msg, process_create_ritual)
        return
        
    emoji, xp, days_raw, task_desc = match.groups()
    xp = int(xp)
    task_desc = task_desc.strip()
    days_raw = days_raw.lower().strip()
    
    # Перевірка ліміту балів
    if xp < 4 or xp > 14:
        msg = bot.send_message(message.chat.id, "<b>🪷Лілі Понд🪷</b>: «Сила ритуалу (бали) має бути в межах від 4 до 14! Спробуй ще раз з правильними балами:»")
        bot.register_next_step_handler(msg, process_create_ritual)
        return
        
    # Розбираємо дні тижня
    valid_days = ["пн", "вт", "ср", "чт", "пт", "сб", "нд"]
    if days_raw == "щодня":
        final_days = valid_days
    else:
        # Ділимо рядок по комі і прибираємо зайві пробіли
        final_days = [d.strip() for d in days_raw.split(",") if d.strip() in valid_days]
        if not final_days:
            msg = bot.send_message(message.chat.id, "<b>🪷Лілі Понд🪷</b>: «Я не змогла розпізнати дні тижня. Будь ласка, пиши скорочено через кому: пн, вт, ср, чт, пт, сб, нд. Спробуй знову:»")
            bot.register_next_step_handler(msg, process_create_ritual)
            return

    player = get_player(user_id)
    rituals = player["quests"].get("rituals", [])
    
    # Перевіряємо, чи немає вже ритуалу з такою ж назвою
    if any(clean_skin_tones(r["task"]).lower() == task_desc.lower() for r in rituals):
        msg = bot.send_message(message.chat.id, "<b>🪷Лілі Понд🪷</b>: «У твоїй книзі вже є ритуал з точно такою назвою. Дай йому трохи інше ім'я або опис:»")
        bot.register_next_step_handler(msg, process_create_ritual)
        return
        
    # Формуємо новий магічний ритуал
    new_ritual = {
        "emoji": emoji,
        "xp": float(xp),
        "days": final_days,
        "task": task_desc,
        "done_today": False
    }
    
    # Зберігаємо оновлені дані в базі
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
    
    # 👇 ОСЬ ЦЕЙ РЯДОК ЗАПУСКАЄ НАШ ТАЙМЕР В ОКРЕМУ МАГІЧНУ КІМНАТУ:
    Thread(target=check_failed_deadlines, daemon=True).start()
    
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
