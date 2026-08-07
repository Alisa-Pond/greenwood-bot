from datetime import datetime

from telebot import types

from services.config import bot
from keyboards import get_scrolls_menu


print("⚙️ Завантажено створення сувоїв...")


# =========================
# Налаштування сфер
# =========================

EMOJI_TO_SPHERE = {
    "💪": "health",
    "🧠": "wisdom",
    "🎨": "art",
    "💵": "finance",
    "🤝": "relations"
}


# =========================
# Кнопка створення сувою
# =========================

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

        "Приклади:\n\n"

        "<code>🧠 ; 8 ; 12.08.26 ; Вивчити нову тему</code>\n\n"

        "<code>💪🧠 ; 10 ; 20.08.26 ; Прочитати книгу</code>\n\n"

        "<code>💪🎨🤝 ; 12 ; 25.08.26 ; Створити творчий проєкт</code>\n\n"

        "📚 Доступні сфери:\n"
        "💪 Здоров'я\n"
        "🧠 Мудрість\n"
        "🎨 Творчість\n"
        "💵 Фінанси\n"
        "🤝 Зв'язки\n\n"

        "⭐ Бали: від 4 до 14\n"
        "📅 Дата: ДД.ММ.РР\n\n"

        "⚖️ Якщо сфер кілька, досвід буде розділено між ними."
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



# =========================
# Обробка введення
# =========================

def process_scroll_creation(message):


    if message.text == "🔙 Скасувати":

        bot.send_message(
            message.chat.id,
            "🦇 Марчелло закрив сувій. Повертаємось.",
            reply_markup=get_scrolls_menu()
        )

        return



    try:

        parts = [
            part.strip()
            for part in message.text.split(";")
        ]


        if len(parts) != 4:

            raise ValueError(
                "Потрібно заповнити всі 4 частини."
            )


        spheres_text, xp_text, date_text, title = parts



        # =========================
        # Перевірка сфер
        # =========================

        spheres = []

        for emoji in spheres_text:

            if emoji in EMOJI_TO_SPHERE:

                spheres.append(
                    EMOJI_TO_SPHERE[emoji]
                )


        if not spheres:

            raise ValueError(
                "Не знайдено жодної правильної сфери."
            )


        if len(spheres) != len(set(spheres)):

            raise ValueError(
                "Одна сфера вказана двічі."
            )



        # =========================
        # Перевірка XP
        # =========================

        try:

            xp = int(xp_text)

        except:

            raise ValueError(
                "Бали мають бути числом."
            )


        if xp < 4 or xp > 14:

            raise ValueError(
                "Кількість балів має бути від 4 до 14."
            )



        # =========================
        # Перевірка дати
        # =========================

        try:

            deadline = datetime.strptime(
                date_text,
                "%d.%m.%y"
            )


        except:

            raise ValueError(
                "Дата має бути у форматі ДД.ММ.РР."
            )


        if deadline.date() < datetime.now().date():

            raise ValueError(
                "Ця дата вже минула."
            )



        # =========================
        # Назва
        # =========================

        if len(title) < 3:

            raise ValueError(
                "Назва сувою занадто коротка."
            )



        # =========================
        # Успішна перевірка
        # =========================

        bot.send_message(
            message.chat.id,

            "🦇 <b>Марчелло задоволено посміхається...</b>\n\n"

            "✨ Сувій успішно перевірено!\n\n"

            f"📜 <b>{title}</b>\n\n"

            f"⭐ Нагорода: {xp} XP\n"

            f"🎯 Сфери: {', '.join(spheres)}\n"

            f"📅 Дедлайн: {date_text}\n\n"

            "Незабаром він буде запечатаний у бібліотеці Грінвуду.",

            parse_mode="HTML",

            reply_markup=get_scrolls_menu()
        )



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

            "Спробуй ще раз:\n\n"

            "<code>💪🧠 ; 10 ; 20.08.26 ; Назва справи</code>",

            parse_mode="HTML",

            reply_markup=markup
        )


        bot.register_next_step_handler(
            message,
            process_scroll_creation
        )
