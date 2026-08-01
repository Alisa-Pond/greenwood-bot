from datetime import datetime
from zoneinfo import ZoneInfo
from telebot import types

from config import bot
from database import get_player
from keyboards import get_quests_menu, get_scrolls_menu

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
