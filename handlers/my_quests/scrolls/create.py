from datetime import datetime
from html import escape

from telebot import types

from services.config import bot
from keyboards import get_scrolls_menu
from services.database import save_scroll


print("⚙️ Завантажено створення сувоїв...")


# ==================================================
# СФЕРИ
# ==================================================

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


# ==================================================
# КНОПКА "СТВОРИТИ СУВІЙ"
# ==================================================

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
        "🦇 <b>Марчелло🦇:</b>\n"
        "Бібліотека Грінвуду готова задокументувати твої обіцянки собі. "
        "Запиши його правильно, і я відправлю його до бібліотеки Грінвуду. Не хочу, щоб архіваріуси потім звинувачували мене у твоєму почерку \n\n"

        "<code>Сфери ; Бали ; Дедлайн ; Назва справи</code>\n\n"

        "🎯 <b>Доступні сфери:</b>\n"
        "💪 Здоров'я\n"
        "🧠 Мудрість\n"
        "🎨 Творчість\n"
        "💵 Фінанси\n"
        "🤝 Зв'язки\n\n"

        "⭐ Бали: від 4 до 14\n"
        "📅 Дата: ДД.ММ.РР\n\n"

        "⚖️ Якщо сфер кілька, досвід буде "
        "розділено між ними.\n\n"

        "<i>І пам'ятай: бібліотека не допустить існування активних сувоїв з однаковими назвами.</i>\n\n"
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


# ==================================================
# ОБРОБКА ВВЕДЕННЯ
# ==================================================

def process_scroll_creation(message):

    # ==================================================
    # СКАСУВАННЯ
    # ==================================================

    if message.text == "🔙 Скасувати":

        bot.send_message(
            message.chat.id,

            "🦇 <b>Марчелло🦇:</b>\n"
            "Повертаємось",

            parse_mode="HTML",

            reply_markup=get_scrolls_menu()
        )

        return


    try:

        # ==================================================
        # РОЗБИВАЄМО НА 4 ЧАСТИНИ
        # ==================================================

        parts = [
            part.strip()
            for part in message.text.split(";")
        ]

        if len(parts) != 4:

            raise ValueError(
                "🦇 <b>Марчелло🦇:</b>\n"
                "Слідуй формулі запису аби я міг записати сувій в бібліотеку\n"
                 "<code>Сфери ; Бали ; Дедлайн ; Назва справи</code>\n",
            )


        spheres_text, xp_text, date_text, title = parts


        # ==================================================
        # ПЕРЕВІРКА СФЕР
        # ==================================================

        spheres = []

        for emoji in spheres_text:

            if emoji in EMOJI_TO_SPHERE:

                spheres.append(
                    EMOJI_TO_SPHERE[emoji]
                )


        if not spheres:

            raise ValueError(
                "🦇 <b>Марчелло🦇:</b>\n"
                "Бібліотека вимагає сферу\n",
            )


        if len(spheres) != len(set(spheres)):

            raise ValueError(
                "Схоже що одна й та сама сфера вказана двічі."
            )


        # ==================================================
        # ПЕРЕВІРКА XP
        # ==================================================

        try:

            xp = int(xp_text)

        except ValueError:

            raise ValueError(
                "🦇 <b>Марчелло🦇:</b>\n"
                "Бали мають бути цілим числом від 4 до 14."
            )


        if xp < 4 or xp > 14:

            raise ValueError(
                "🦇 <b>Марчелло🦇:</b>\n"
                "Я не знаю таких цисел. Кількість балів має бути від 4 до 14."
            )


        # ==================================================
        # ПЕРЕВІРКА ДАТИ
        # ==================================================

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


        # ==================================================
        # ПЕРЕВІРКА НАЗВИ
        # ==================================================

        if len(title) < 3:

            raise ValueError(
                "🦇 <b>Марчелло🦇:</b>\n"
                "Назва сувою має містити щонайменше 3 символи."
            )


        # ==================================================
        # СТВОРЮЄМО СУВІЙ
        # ==================================================

        scroll = {

            "title": title,

            "spheres": spheres,

            "xp": xp,

            "deadline": date_text,

            "created_at": datetime.now().isoformat(),

            "completed": False
        }


        # ==================================================
        # ЗБЕРІГАЄМО В SUPABASE
        # ==================================================

        result = save_scroll(
            message.from_user.id,
            scroll
        )


        # ==================================================
        # ДУБЛЬ
        # ==================================================

        if result.get("duplicate"):

            safe_title = escape(title)


            markup = types.ReplyKeyboardMarkup(
                resize_keyboard=True
            )

            markup.row(
                types.KeyboardButton("🔙 Скасувати")
            )


            bot.send_message(

                message.chat.id,

                "🦇 <b>Марчелло🦇:</b>\n"

                f"❕Сувій "
                f"<b>«{safe_title}»</b> "
                "вже лежить серед активних.\n\n"

                "Два однакові квести бібліотека "
                "Грінвуду не приймає. 📚\n\n",

                parse_mode="HTML",

                reply_markup=markup
            )


            # Продовжуємо чекати наступний сувій

            bot.register_next_step_handler(
                message,
                process_scroll_creation
            )

            return


        # ==================================================
        # ПОМИЛКА ЗБЕРЕЖЕННЯ
        # ==================================================

        if not result.get("success"):

            bot.send_message(

                message.chat.id,

                "🦇 <b>Марчелло🦇:</b>\n"
                "❕ Не вдалося запечатати сувій "
                "у бібліотеці Грінвуду.\n\n"

                "Спробуй ще раз.",

                parse_mode="HTML",

                reply_markup=types.ReplyKeyboardMarkup(
                    resize_keyboard=True
                )
            )

            # Навіть після помилки продовжуємо чекати
            # наступну спробу

            bot.register_next_step_handler(
                message,
                process_scroll_creation
            )

            return


        # ==================================================
        # УСПІШНЕ СТВОРЕННЯ
        # ==================================================

        safe_title = escape(title)


        sphere_names = [
            SPHERE_NAMES[sphere]
            for sphere in spheres
        ]


        active_count = result.get(
            "count",
            0
        )


        # ==================================================
        # КНОПКА СКАСУВАННЯ
        # ==================================================

        markup = types.ReplyKeyboardMarkup(
            resize_keyboard=True
        )

        markup.row(
            types.KeyboardButton("🔙 Скасувати")
        )


        bot.send_message(

            message.chat.id,

           "🦇 <b>Марчелло🦇</b>\n"

            "🗯 Сувій успішно перевірено "
            "та запечатано!\n\n"

            f"📜 <b>«{safe_title}»</b>\n\n"
            f"Нагорода: <b>{xp} XP</b>\n"
            
            f"Сфери: "
            f"{', '.join(sphere_names)}\n"

            f"Дедлайн: <b>{date_text}</b>\n\n"

            f"📚 <b>Активних сувоїв: "
            f"{active_count}</b>\n\n"

            "🦇 <b>Марчелло🦇:</b>\n"
            "Готовий до запису настпного сувою",

            parse_mode="HTML",

            reply_markup=markup
        )


        # ==================================================
        # ЧЕКАЄМО НАСТУПНИЙ СУВІЙ
        # ==================================================

        bot.register_next_step_handler(
            message,
            process_scroll_creation
        )


    # ==================================================
    # ПОМИЛКА ФОРМАТУ
    # ==================================================

    except ValueError as error:

        markup = types.ReplyKeyboardMarkup(
            resize_keyboard=True
        )

        markup.row(
            types.KeyboardButton("🔙 Скасувати")
        )


        bot.send_message(

            message.chat.id,

            "🦇 <b>Марчелло🦇:</b>\n"

            f"❕ {error}\n"

            "Спробуй ще раз за цим форматом:\n\n"

            "<code>💪🧠 ; 10 ; 20.08.26 ; Назва справи</code>\n\n",

            parse_mode="HTML",

            reply_markup=markup
        )


        # Після помилки також одразу чекаємо
        # новий ввід

        bot.register_next_step_handler(
            message,
            process_scroll_creation
        )
