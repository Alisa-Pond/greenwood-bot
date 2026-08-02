import telebot
from datetime import datetime
from zoneinfo import ZoneInfo
from telebot import types

from services.database import get_player, update_player
from keyboards import get_quests_menu, get_scrolls_menu, get_rituals_menu, get_greenhouse_menu  
import re
from services.config import bot

# --- ГОЛОВНЕ МЕНЮ КВЕСТІВ ---
print("⚙️ Модуль handlers/my_quests успішно імпортовано і завантажено!")

@bot.message_handler(func=lambda message: message.text in ["🎯 Мої Квести", "🔙 Назад до квестів"])
def show_quests_menu(message):
    user_id = str(message.from_user.id)
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

@bot.message_handler(func=lambda message: message.text == "🌸 Квітка розквітла")
def harvest_plant_start(message):
    user_id = str(message.from_user.id)
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
    # Зверни увагу: функція process_harvest_plant буде описана нижче у цьому ж файлі!
    bot.register_next_step_handler(msg, process_harvest_plant)


# --- ВИРВАТИ БАОБАБ (СКАСУВАННЯ ЦІЛІ) ---

@bot.message_handler(func=lambda message: message.text in ["🪓 Вирвати баобаб", "🌱 Вирвати баобаб"])
def remove_plant_start(message):
    user_id = str(message.from_user.id)
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
    # Зверни увагу: функція process_remove_plant буде описана нижче у цьому ж файлі!
    bot.register_next_step_handler(msg, process_remove_plant)



# --- СУВОЇ ЗАВДАНЬ ---

@bot.message_handler(func=lambda message: message.text == "📜 Сувої завдань")
def show_scrolls_menu(message):
    user_id = str(message.from_user.id)
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


@bot.message_handler(func=lambda message: message.text == "➕ Створити сувой")
def create_scroll_start(message):
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


@bot.message_handler(func=lambda message: message.text == "✅ Виконати завдання")
def complete_scroll_start(message):
    user_id = str(message.from_user.id)
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


@bot.message_handler(func=lambda message: message.text == "🔥 Спалити сувой")
def delete_scroll_start(message):
    user_id = str(message.from_user.id)
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

@bot.message_handler(func=lambda message: message.text == "🔄 Щоденні ритуали")
def show_rituals_menu(message):
    user_id = str(message.from_user.id)
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


@bot.message_handler(func=lambda message: message.text == "➕ Створити ритуал")
def create_ritual_start(message):
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


@bot.message_handler(func=lambda message: message.text == "✅ Виконати ритуал")
def complete_ritual_start(message):
    user_id = str(message.from_user.id)
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

@bot.message_handler(func=lambda message: message.text in ["🌱 Теплиця Грінвуду", "🌱 Теплиця"])
def show_greenhouse_menu(message):
    user_id = str(message.from_user.id)
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


@bot.message_handler(func=lambda message: message.text == "🌱 Посадити насіння")
def plant_seed_start(message):
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
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("🔙 Назад до квестів"))
    
    msg = bot.send_message(message.chat.id, intro_text, parse_mode="HTML", reply_markup=markup)
    bot.register_next_step_handler(msg, process_plant_creation)


# --- ЛОГІКА РОБОТИ ІЗ СУВОЯМИ ---

def process_create_scroll(message):
    user_id = str(message.from_user.id)
    text = message.text.strip() if message.text else ""
    
    if text == "🔙 Назад до квестів":
        bot.send_message(message.chat.id, "Створення скасовано, повертаємось.", reply_markup=get_scrolls_menu())
        return
# --- ОБРОБНИКИ ДЛЯ СУВОЇВ ---

def process_create_scroll(message):
    user_id = str(message.from_user.id)
    text = message.text.strip() if message.text else ""
    
    if text in ["🔙 Назад до квестів", "🔙 Назад"]:
        bot.send_message(message.chat.id, "Створення скасовано, повертаємось.", reply_markup=get_scrolls_menu())
        return

    cleaned_text = clean_skin_tones(text)
    # Магічний вираз дозволяє пробіли всередині переліку днів тижня
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
        msg = bot.send_message(message.chat.id, f"<b>🪷Лілі Понд🪷</b>:  У твоїх хроніках уже є активний сувой з назвою \"{task_desc}\". Придумай іншу назву або заверши попередній квест")
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
    
    if text in ["🔙 Назад до квестів", "🔙 Назад"]:
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
    
    if text in ["🔙 Назад до квестів", "🔙 Назад"]:
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


# --- ОБРОБНИКИ ДЛЯ РИТУАЛІВ ---

def process_create_ritual(message):
    user_id = str(message.from_user.id)
    text = message.text.strip() if message.text else ""
    
    if text in ["🔙 Назад до квестів", "🔙 Назад"]:
        bot.send_message(message.chat.id, "Повертаємось до свитку ритуалів.", reply_markup=get_rituals_menu())
        return
        
    cleaned_text = clean_skin_tones(text)
    parts = cleaned_text.split()
    
    if len(parts) < 4:
        msg = bot.send_message(
            message.chat.id, 
            "<b>🪷Лілі Понд🪷</b>: «Ой, не вистачає деталей. Перевір формат і спробуй ще раз за шаблоном:\n<code>[Емодзі] [Бали] [Дні] [Назва]</code>»",
            parse_mode="HTML"
        )
        bot.register_next_step_handler(msg, process_create_ritual)
        return
        
    emoji = parts[0]
    
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

    remaining_text = " ".join(parts[2:])
    valid_days = ["пн", "вт", "ср", "чт", "пт", "сб", "нд"]
    
    if remaining_text.lower().startswith("щодня"):
        final_days = valid_days
        task_desc = remaining_text[5:].strip()
    else:
        days_accumulated = []
        words = remaining_text.split()
        idx = 0
        
        for word in words:
            sub_tokens = [t.strip().lower() for t in word.split(",") if t.strip()]
            
            if sub_tokens and all(t in valid_days for t in sub_tokens):
                for t in sub_tokens:
                    if t not in days_accumulated:
                        days_accumulated.append(t)
                idx += 1
            else:
                break

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
    
    if text in ["🔙 Назад до квестів", "🔙 Назад", "/start"]:
        bot.send_message(message.chat.id, "Повертаємось до свитку ритуалів.", reply_markup=get_rituals_menu())
        return

    player = get_player(user_id)
    rituals = player["quests"].get("rituals", [])
    clean_input = clean_skin_tones(text).lower()
    
    found = None
    for r in rituals:
        task_name = clean_skin_tones(r.get("task", "")).lower()
        if task_name == clean_input:
            found = r
            break
    
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
        
    found["done_today"] = True
    earned_xp = float(found.get("xp", 5.0))
    player["xp_total"] += earned_xp
    
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

# ----------------------------------------------------
# 📌 Обробка створення рослини (Теплиця)
# ----------------------------------------------------
def process_plant_creation(message):
    user_id = str(message.from_user.id)
    text = message.text.strip() if message.text else ""

    # Якщо натиснули кнопку скасування
    if text in ["🔙 Назад", "🔙 Назад до квестів", "/cancel"]:
        bot.send_message(
            message.chat.id, 
            "🌲Лісовик🌲: Хм, ну й добре. Менше бур'янів у теплиці!", 
            reply_markup=get_greenhouse_menu()
        )
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
    emoji = clean_skin_tones(raw_emoji)

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
    update_player(user_id, player)

    bot.send_message(
        message.chat.id, 
        f"🌲Лісовик🌲: Ну добре, закопали твоє зерно <b>{emoji} {task}</b>! Тепер поливай його своєю працею до {deadline}!", 
        parse_mode="HTML", 
        reply_markup=get_greenhouse_menu()
    )
# ----------------------------------------------------
# 📌 Обробка "Квітка розквітла" (Збір врожаю)
# ----------------------------------------------------
def process_harvest_plant(message):
    user_id = str(message.from_user.id)
    task_name = message.text.strip() if message.text else ""

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
        update_player(user_id, player)

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


# ----------------------------------------------------
# 📌 Обробка "Вирвати баобаб" (Видалення цілі)
# ----------------------------------------------------
def process_remove_plant(message):
    user_id = str(message.from_user.id)
    task_name = message.text.strip() if message.text else ""

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
        update_player(user_id, player)

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
        
