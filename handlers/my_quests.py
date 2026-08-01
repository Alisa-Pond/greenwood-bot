from datetime import datetime
from zoneinfo import ZoneInfo
from telebot import types

from config import bot
from database import get_player
from keyboards import get_quests_menu, get_scrolls_menu, get_rituals_menu, get_greenhouse_menu  

# --- ГОЛОВНЕ МЕНЮ КВЕСТІВ ---

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
