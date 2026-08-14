from telebot import types

from services.config import bot
from services.database import get_player, save_ritual
from keyboards import get_rituals_menu


print("⚙️ Завантажено створення ритуалів...")


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


# =========================================================
# ДНІ ТИЖНЯ
# =========================================================

VALID_DAYS = {
    "пн",
    "вт",
    "ср",
    "чт",
    "пт",
    "сб",
    "нд"
}


# =========================================================
# КНОПКА "СТВОРИТИ РИТУАЛ"
# =========================================================

@bot.message_handler(
    func=lambda message: message.text == "➕ Створити ритуал"
)
def start_create_ritual(message):

    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    markup.row(
        types.KeyboardButton("🔙 Скасувати")
    )

    text = (
        "🦇 <b>Марчелло розгортає новий магічний запис...</b>\n\n"

        "Цього разу перед тобою не одноразовий сувій, "
        "а <b>ритуал</b> — справа, яка повертається до тебе "
        "знову і знову у визначені дні. 🔄\n\n"

        "Запиши його у такому форматі:\n\n"

        "<code>[Сфери] ; [Бали] ; [Дні] ; [Назва справи]</code>\n\n"

        "📜 <b>Приклади:</b>\n\n"

        "<code>🧠 ; 5 ; щодня ; Читати 20 сторінок</code>\n\n"

        "<code>💪 ; 8 ; пн,ср,пт ; Ранкова зарядка</code>\n\n"

        "<code>🧠🎨 ; 10 ; вт,чт,сб ; Грати на калімбі</code>\n\n"

        "🎯 <b>Доступні сфери:</b>\n"
        "💪 Здоров'я\n"
        "🧠 Мудрість\n"
        "🎨 Творчість\n"
        "💵 Фінанси\n"
        "🤝 Зв'язки\n\n"

        "⭐ <b>Бали:</b> від 4 до 14\n"
        "📅 <b>Дні:</b> пн, вт, ср, чт, пт, сб, нд\n"
        "або просто <b>щодня</b>\n\n"

        "⚖️ Якщо вказано кілька сфер, XP за виконання "
        "буде розділено між ними.\n\n"

        "📚 <b>Можеш створювати ритуали один за одним.</b>\n"
        "Після кожного успішного створення Марчелло "
        "чекатиме на наступний."
    )

    msg = bot.send_message(
        message.chat.id,
        text,
        parse_mode="HTML",
        reply_markup=markup
    )

    bot.register_next_step_handler(
        msg,
        process_ritual_creation
    )


# =========================================================
# ОБРОБКА ВВЕДЕННЯ
# =========================================================

def process_ritual_creation(message):

    # -----------------------------------------------------
    # Скасування
    # -----------------------------------------------------

    if message.text == "🔙 Скасувати":

        bot.send_message(
            message.chat.id,
            "🦇 Марчелло згортає чистий аркуш.\n\n"
            "Режим створення ритуалів завершено.",
            parse_mode="HTML",
            reply_markup=get_rituals_menu()
        )

        return


    try:

        # -------------------------------------------------
        # Розділення формули
        # -------------------------------------------------

        parts = [
            part.strip()
            for part in message.text.split(";")
        ]

        if len(parts) != 4:

            raise ValueError(
                "Потрібно заповнити всі 4 частини формули."
            )


        spheres_text, xp_text, days_text, title = parts


        # -------------------------------------------------
        # ПЕРЕВІРКА СФЕР
        # -------------------------------------------------

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


        # -------------------------------------------------
        # ПЕРЕВІРКА XP
        # -------------------------------------------------

        try:

            xp = int(xp_text)

        except ValueError:

            raise ValueError(
                "Бали мають бути цілим числом."
            )


        if xp < 4 or xp > 14:

            raise ValueError(
                "Для ритуалу кількість балів має бути від 4 до 14."
            )


        # -------------------------------------------------
        # ПЕРЕВІРКА ДНІВ
        # -------------------------------------------------

        days_text_lower = days_text.lower().strip()


        if days_text_lower == "щодня":

            days = [
                "пн",
                "вт",
                "ср",
                "чт",
                "пт",
                "сб",
                "нд"
            ]

            days_display = "щодня"

        else:

            days = [
                day.strip().lower()
                for day in days_text.split(",")
                if day.strip()
            ]


            if not days:

                raise ValueError(
                    "Потрібно вказати хоча б один день."
                )


            # ---------------------------------------------
            # Перевірка правильності назв днів
            # ---------------------------------------------

            invalid_days = [
                day
                for day in days
                if day not in VALID_DAYS
            ]


            if invalid_days:

                raise ValueError(
                    "Невідомий день: "
                    + ", ".join(invalid_days)
                    + ". Використовуй пн, вт, ср, чт, пт, сб або нд."
                )


            # ---------------------------------------------
            # Перевірка повторення дня
            # ---------------------------------------------

            if len(days) != len(set(days)):

                raise ValueError(
                    "Один із днів вказано двічі."
                )


            days_display = ", ".join(days)


        # -------------------------------------------------
        # ПЕРЕВІРКА НАЗВИ
        # -------------------------------------------------

        if len(title) < 3:

            raise ValueError(
                "Назва ритуалу занадто коротка."
            )


        # -------------------------------------------------
        # ПЕРЕВІРКА ОДНАКОВИХ НАЗВ
        # -------------------------------------------------

        user_id = str(message.from_user.id)

        player = get_player(user_id)

        rituals = player.get("rituals") or []


        for ritual in rituals:

            if not isinstance(ritual, dict):
                continue

            existing_title = ritual.get(
                "title",
                ritual.get("name", "")
            )


            if existing_title.strip().lower() == title.strip().lower():

                raise ValueError(
                    "Ритуал із такою назвою вже існує."
                )


        # -------------------------------------------------
        # СТВОРЕННЯ РИТУАЛУ
        # -------------------------------------------------

        ritual = {

            "title": title,

            "spheres": spheres,

            "xp": xp,

            "days": days,

            "completed": False
        }


        # -------------------------------------------------
        # ЗБЕРЕЖЕННЯ В SUPABASE
        # -------------------------------------------------

        ritual_count = save_ritual(
            user_id,
            ritual
        )


        # -------------------------------------------------
        # УСПІШНЕ ПОВІДОМЛЕННЯ
        # -------------------------------------------------

        sphere_emojis = "".join(
            [
                emoji
                for emoji, sphere_key in EMOJI_TO_SPHERE.items()
                if sphere_key in spheres
            ]
        )


        # Кнопка скасування залишається,
        # бо ми продовжуємо чекати наступний ритуал.

        markup = types.ReplyKeyboardMarkup(
            resize_keyboard=True
        )

        markup.row(
            types.KeyboardButton("🔙 Скасувати")
        )


        bot.send_message(
            message.chat.id,

            "🦇 <b>Марчелло ставить останню печатку...</b>\n\n"

            "✨ <b>Ритуал успішно запечатано!</b>\n\n"

            f"🔄 <b>{title}</b>\n"
            f"🎯 Сфери: {sphere_emojis}\n"
            f"⭐ Нагорода: {xp} XP\n"
            f"📅 Дні: {days_display}\n\n"

            f"📚 Тепер у тебе "
            f"<b>{ritual_count}</b> активних ритуалів.\n\n"

            "🔥 Марчелло заносить його до магічного розкладу "
            "Грінвуду.\n\n"

            "✨ <b>Надсилай наступний ритуал.</b>",

            parse_mode="HTML",
            reply_markup=markup
        )


        # -------------------------------------------------
        # ЧЕКАЄМО НАСТУПНИЙ РИТУАЛ
        # -------------------------------------------------

        bot.register_next_step_handler(
            message,
            process_ritual_creation
        )


    # -----------------------------------------------------
    # ПОМИЛКА
    # -----------------------------------------------------

    except ValueError as error:

        markup = types.ReplyKeyboardMarkup(
            resize_keyboard=True
        )

        markup.row(
            types.KeyboardButton("🔙 Скасувати")
        )


        bot.send_message(
            message.chat.id,

            "🦇 <b>Марчелло насупився над сувоєм...</b>\n\n"

            f"❌ {error}\n\n"

            "Спробуй ще раз за правильною формулою:\n\n"

            "<code>💪🧠 ; 10 ; пн,ср,пт ; Назва справи</code>\n\n"

            "або:\n\n"

            "<code>🧠 ; 5 ; щодня ; Назва справи</code>",

            parse_mode="HTML",
            reply_markup=markup
        )


        # Після помилки також залишаєтьсямося
        # у режимі створення ритуалів.

        bot.register_next_step_handler(
            message,
            process_ritual_creation
        )
