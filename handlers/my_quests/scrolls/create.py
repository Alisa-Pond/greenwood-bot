from datetime import datetime
import uuid

from telebot import types

from services.config import bot
from keyboards import get_scrolls_menu
from services.database import get_player, update_player

print("⚙️ Завантажено створення сувоїв...")

# =========================

# Сфери

# =========================

EMOJI_TO_SPHERE = {
"💪": "health",
"🧠": "wisdom",
"🎨": "art",
"💵": "finance",
"🤝": "relations"
}

SPHERE_NAMES = {
"health": "💪 Здоров'я",
"wisdom": "🧠 Мудрість",
"art": "🎨 Творчість",
"finance": "💵 Фінанси",
"relations": "🤝 Зв'язки"
}

# =========================

# Створення сувою

# =========================

@bot.message_handler(
func=lambda message: message.text == "➕ Створити сувій"
)
def start_create_scroll(message):

```
markup = types.ReplyKeyboardMarkup(
    resize_keyboard=True
)

markup.row(
    types.KeyboardButton("🔙 Скасувати")
)

text = (
    "🦇 <b>Марчелло розгортає чистий аркуш стародавнього сувою...</b>\n\n"

    "Щоб запечатати новий квест, напиши його у такому форматі:\n\n"

    "<code>[Сфери] - [Бали] - [Дедлайн] - [Назва справи]</code>\n\n"

    "Наприклад:\n\n"

    "<code>🧠 - 8 - 12.08.26 - Вивчити нову тему</code>\n\n"

    "<code>💪🧠 - 10 - 20.08.26 - Прочитати книгу</code>\n\n"

    "<code>💪🎨🤝 - 12 - 25.08.26 - Створити творчий проєкт</code>\n\n"

    "📚 <b>Доступні сфери:</b>\n"
    "💪 Здоров'я\n"
    "🧠 Мудрість\n"
    "🎨 Творчість\n"
    "💵 Фінанси\n"
    "🤝 Зв'язки\n\n"

    "⭐ Бали: від 4 до 14\n"
    "📅 Дедлайн: ДД.ММ.РР\n\n"

    "⚖️ Якщо вказати кілька сфер, отриманий досвід "
    "буде розділено між ними.\n\n"

    "🦇 <i>Марчелло чекає на твій запис...</i>"
)

msg = bot.send_message(
    message.chat.id,
    text,
    parse_mode="HTML",
    reply_markup=markup
)

bot.register_next_step_handler(
    msg,
    process_scroll_creation
)
```

# =========================

# Обробка створення

# =========================

def process_scroll_creation(message):

```
# -------------------------
# Скасування
# -------------------------

if message.text == "🔙 Скасувати":

    bot.send_message(
        message.chat.id,
        "🦇 Марчелло акуратно згортає чистий аркуш.\n\n"
        "Сувій залишився незапечатаним.",
        parse_mode="HTML",
        reply_markup=get_scrolls_menu()
    )

    return


try:

    # =========================
    # Розбір введення
    # =========================

    parts = [
        part.strip()
        for part in message.text.split("-")
    ]

    if len(parts) != 4:

        raise ValueError(
            "Потрібно заповнити всі 4 частини формули."
        )


    spheres_text, xp_text, date_text, title = parts


    # =========================
    # Перевірка сфер
    # =========================

    spheres = []

    for emoji in spheres_text:

        if emoji in EMOJI_TO_SPHERE:

            sphere = EMOJI_TO_SPHERE[emoji]

            if sphere not in spheres:

                spheres.append(sphere)


    if not spheres:

        raise ValueError(
            "Марчелло не знайшов жодної відомої сфери."
        )


    # =========================
    # Перевірка XP
    # =========================

    try:

        xp = int(xp_text)

    except ValueError:

        raise ValueError(
            "Бали мають бути цілим числом від 4 до 14."
        )


    if xp < 4 or xp > 14:

        raise ValueError(
            "Кількість балів має бути від 4 до 14."
        )


    # =========================
    # Перевірка дедлайну
    # =========================

    try:

        deadline = datetime.strptime(
            date_text,
            "%d.%m.%y"
        )

    except ValueError:

        raise ValueError(
            "Дата має бути у форматі ДД.ММ.РР."
        )


    if deadline.date() < datetime.now().date():

        raise ValueError(
            "Цей дедлайн уже минув. Марчелло не приймає прострочені сувої."
        )


    # =========================
    # Перевірка назви
    # =========================

    if len(title) < 3:

        raise ValueError(
            "Назва справи має містити щонайменше 3 символи."
        )


    # =========================
    # Створення сувою
    # =========================

    scroll = {

        "id": str(uuid.uuid4()),

        "name": title,

        "spheres": spheres,

        "xp": xp,

        "deadline": date_text,

        "completed": False,

        "failed": False,

        "created_at": datetime.now().strftime("%d.%m.%Y")
    }


    # =========================
    # Отримання гравця
    # =========================

    user_id = str(message.from_user.id)

    player = get_player(user_id)


    # =========================
    # Отримання сувоїв
    # =========================

    scrolls = player.get("scrolls") or []


    # =========================
    # Додаємо новий сувій
    # =========================

    scrolls.append(scroll)


    # =========================
    # Зберігаємо в Supabase
    # =========================

    update_player(
        user_id,
        {
            "scrolls": scrolls
        }
    )


    # =========================
    # Формуємо назви сфер
    # =========================

    sphere_names = [
        SPHERE_NAMES[sphere]
        for sphere in spheres
    ]


    # =========================
    # Успішне створення
    # =========================

    bot.send_message(

        message.chat.id,

        "🦇 <b>Марчелло піднімає погляд від сувою...</b>\n\n"

        "✨ <b>Сувій успішно запечатано!</b>\n\n"

        f"📜 <b>{title}</b>\n\n"

        f"⭐ Нагорода: {xp} XP\n"

        f"🎯 Сфери: {', '.join(sphere_names)}\n"

        f"📅 Дедлайн: {date_text}\n\n"

        "Сувій передано до бібліотеки Грінвуду. 🌲\n"
        "Тепер він чекатиме свого героя.",

        parse_mode="HTML",

        reply_markup=get_scrolls_menu()
    )


# =========================
# Помилка формату
# =========================

except ValueError as error:

    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    markup.row(
        types.KeyboardButton("🔙 Скасувати")
    )

    bot.send_message(

        message.chat.id,

        "🦇 <b>Марчелло поправляє окуляри...</b>\n\n"

        f"❌ {error}\n\n"

        "Спробуй записати сувій ще раз:\n\n"

        "<code>💪🧠 - 10 - 20.08.26 - Назва справи</code>\n\n"

        "Або натисни «🔙 Скасувати», якщо передумала.",

        parse_mode="HTML",

        reply_markup=markup
    )

    bot.register_next_step_handler(
        message,
        process_scroll_creation
    )


# =========================
# Непередбачена помилка
# =========================

except Exception as error:

    print(
        f"❌ Помилка під час створення сувою: {error}"
    )

    bot.send_message(

        message.chat.id,

        "🦇 <b>Марчелло завмер над сувоєм...</b>\n\n"

        "❌ Сталася внутрішня помилка, і сувій не вдалося запечатати.\n\n"

        "Спробуй ще раз.",

        parse_mode="HTML",

        reply_markup=get_scrolls_menu()
    )
```
