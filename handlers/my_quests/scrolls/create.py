from datetime import datetime

from telebot import types

from services.config import bot
from keyboards import get_scrolls_menu
from services.database import get_player, save_scroll


print("⚙️ Завантажено створення сувоїв...")


# =========================================================
# СФЕРИ
# =========================================================

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


# =========================================================
# СТВОРЕННЯ СУВОЮ
# =========================================================

@bot.message_handler(
    func=lambda message: message.text == "➕ Створити сувій"
)
def start_create_scroll(message):

    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    markup.row(
        types.KeyboardButton("🔙 Скасувати")
    )

    text = (
        "🦇 <b>Марчелло відкриває стародавній сувій...</b>\n\n"

        "Щоб створити новий квест, запиши його у магічному форматі:\n\n"

        "<code>[Сфери] ; [Бали] ; [Дедлайн] ; [Назва справи]</code>\n\n"

        "📜 <b>Приклади:</b>\n\n"

        "<code>🧠 ; 8 ; 12.08.26 ; Вивчити нову тему</code>\n\n"

        "<code>💪🧠 ; 10 ; 20.08.26 ; Прочитати книгу</code>\n\n"

        "<code>💪🎨🤝 ; 12 ; 25.08.26 ; Створити творчий проєкт</code>\n\n"

        "🎯 <b>Доступні сфери:</b>\n"
        "💪 Здоров'я\n"
        "🧠 Мудрість\n"
        "🎨 Творчість\n"
        "💵 Фінанси\n"
        "🤝 Зв'язки\n\n"

        "⭐ Бали: від 4 до 14\n"
        "📅 Дата: ДД.ММ.РР\n\n"

        "⚖️ Якщо сфер кілька, досвід буде розділено між ними.\n\n"

        "🦇 <i>Марчелло чекає на твоє завдання...</i>"
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


# =========================================================
# ОБРОБКА ВВЕДЕНОГО СУВОЮ
# =========================================================

def process_scroll_creation(message):

    # -----------------------------------------------------
    # Скасування
    # -----------------------------------------------------

    if message.text == "🔙 Скасувати":

        bot.send_message(
            message.chat.id,
            "🦇 Марчелло обережно згорнув сувій.\n\n"
            "✨ Нічого не було записано.",
            parse_mode="HTML",
            reply_markup=get_scrolls_menu()
        )

        return

    try:

        # -------------------------------------------------
        # Розділення введення
        # -------------------------------------------------

        parts = [
            part.strip()
            for part in message.text.split(";")
        ]

        if len(parts) != 4:

            raise ValueError(
                "Потрібно заповнити всі 4 частини."
            )

        spheres_text, xp_text, date_text, title = parts

        # -------------------------------------------------
        # Перевірка сфер
        # -------------------------------------------------

        spheres = []

        for emoji in spheres_text:

            if emoji in EMOJI_TO_SPHERE:

                sphere = EMOJI_TO_SPHERE[emoji]

                if sphere not in spheres:
                    spheres.append(sphere)

        if not spheres:

            raise ValueError(
                "Не знайдено жодної правильної сфери."
            )

        # -------------------------------------------------
        # Перевірка XP
        # -------------------------------------------------

        try:

            xp = int(xp_text)

        except ValueError:

            raise ValueError(
                "Бали мають бути цілим числом."
            )

        if xp < 4 or xp > 14:

            raise ValueError(
                "Кількість балів має бути від 4 до 14."
            )

        # -------------------------------------------------
        # Перевірка дедлайну
        # -------------------------------------------------

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
                "Ця дата вже минула."
            )

        # -------------------------------------------------
        # Перевірка назви
        # -------------------------------------------------

        if not title:

            raise ValueError(
                "Назва справи не може бути порожньою."
            )

        if len(title) < 3:

            raise ValueError(
                "Назва сувою занадто коротка."
            )

        # -------------------------------------------------
        # Формуємо дані сувою
        # -------------------------------------------------

        scroll = {
            "title": title,
            "spheres": spheres,
            "xp": xp,
            "deadline": date_text,
            "created_at": datetime.now().isoformat(),
            "completed": False
        }

        # -------------------------------------------------
        # Зберігаємо сувій у Supabase
        # -------------------------------------------------

        user_id = str(message.from_user.id)

        save_scroll(
            user_id,
            scroll
        )

        # -------------------------------------------------
        # Виводимо назви сфер
        # -------------------------------------------------

        sphere_names = [
            SPHERE_NAMES[sphere]
            for sphere in spheres
        ]

        spheres_text_result = ", ".join(
            sphere_names
        )

        # -------------------------------------------------
        # Успішне створення
        # -------------------------------------------------

        bot.send_message(
            message.chat.id,

            "🦇 <b>Марчелло задоволено посміхається...</b>\n\n"

            "✨ <b>Сувій успішно запечатано!</b>\n\n"

            f"📜 <b>{title}</b>\n\n"

            f"⭐ Нагорода: {xp} XP\n"

            f"🎯 Сфери: {spheres_text_result}\n"

            f"📅 Дедлайн: {date_text}\n\n"

            "Сувій уже лежить серед твоїх активних квестів.\n"

            "🕯️ Не дай йому припасти пилом до настання дедлайну...",

            parse_mode="HTML",

            reply_markup=get_scrolls_menu()
        )

    except ValueError as error:

        # -------------------------------------------------
        # Помилка формату
        # -------------------------------------------------

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

            "Спробуй ще раз за магічною формулою:\n\n"

            "<code>💪🧠 ; 10 ; 20.08.26 ; Назва справи</code>\n\n"

            "Або натисни «🔙 Скасувати», якщо передумала.",

            parse_mode="HTML",

            reply_markup=markup
        )

        bot.register_next_step_handler(
            message,
            process_scroll_creation
        )

    except Exception:

        # -------------------------------------------------
        # Непередбачена помилка
        # -------------------------------------------------

        bot.send_message(
            message.chat.id,

            "🦇 <b>Марчелло завмер над сувоєм...</b>\n\n"

            "❌ Сталася технічна помилка під час запечатування.\n\n"

            "Спробуй створити сувій ще раз.",

            parse_mode="HTML",

            reply_markup=get_scrolls_menu()
        )
