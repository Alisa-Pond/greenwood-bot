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
        "🦇 <b>Марчелло відкриває стародавній сувій...</b>\n\n"

        "Отже, хочеш додати нове завдання до "
        "бібліотеки Грінвуду? Хм. Подивимось, "
        "чи вмієш ти правильно запечатувати квести. 🦇\n\n"

        "Запиши завдання у магічному форматі:\n\n"

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

        "⚖️ Якщо сфер кілька, досвід буде "
        "розділено між ними.\n\n"

        "🦇 <i>І пам'ятай: назви активних сувоїв "
        "не можуть повторюватися.</i>"
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

            "🦇 <b>Марчелло закрив сувій.</b>\n\n"
            "Добре, повертаємось до бібліотеки.",

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
                "Потрібно заповнити всі 4 частини."
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
                "Не знайдено жодної правильної сфери."
            )


        if len(spheres) != len(set(spheres)):

            raise ValueError(
                "Одна й та сама сфера вказана двічі."
            )


        # ==================================================
        # ПЕРЕВІРКА XP
        # ==================================================

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

                "🦇 <b>Марчелло різко завмирає...</b>\n\n"

                f"⚠️ Сувій "
                f"<b>«{safe_title}»</b> "
                "вже лежить серед активних.\n\n"

                "Два однакові квести бібліотека "
                "Грінвуду не приймає. 📚\n\n"

                "Спробуй створити сувій з іншою назвою.",

                parse_mode="HTML",

                reply_markup=markup
            )


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

                "🦇 <b>Марчелло насупився...</b>\n\n"

                "❌ Не вдалося запечатати сувій "
                "у бібліотеці Грінвуду.\n\n"

                "Спробуй ще раз трохи пізніше.",

                parse_mode="HTML",

                reply_markup=get_scrolls_menu()
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


        bot.send_message(

            message.chat.id,

            "🦇 <b>Марчелло задоволено посміхається...</b>\n\n"

            "✨ Сувій успішно перевірено "
            "та запечатано!\n\n"

            f"📜 <b>«{safe_title}»</b>\n\n"

            f"⭐ Нагорода: <b>{xp} XP</b>\n"

            f"🎯 Сфери: "
            f"{', '.join(sphere_names)}\n"

            f"📅 Дедлайн: <b>{date_text}</b>\n\n"

            f"📚 <b>Активних сувоїв: "
            f"{active_count}</b>\n\n"

            "🦇 <i>Тепер цей квест офіційно "
            "записаний у хроніки Грінвуду.</i>",

            parse_mode="HTML",

            reply_markup=get_scrolls_menu()
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

            "🦇 <b>Марчелло поправляє окуляри...</b>\n\n"

            f"❌ {error}\n\n"

            "Спробуй ще раз за цим форматом:\n\n"

            "<code>💪🧠 ; 10 ; 20.08.26 ; Назва справи</code>\n\n"

            "🦇 <i>І не поспішай. Навіть магічні "
            "архіваріуси не люблять криві сувої.</i>",

            parse_mode="HTML",

            reply_markup=markup
        )


        bot.register_next_step_handler(
            message,
            process_scroll_creation
        )
