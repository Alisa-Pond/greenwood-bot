from datetime import datetime

from telebot import types

from services.config import bot
from services.database import get_player, update_player
from keyboards import get_greenhouse_menu


print("⚙️ Завантажено створення рослин...")


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


# ==================================================
# СТВОРЕННЯ РОСЛИНИ
# ==================================================

@bot.message_handler(
    func=lambda message: message.text == "🌱 Посадити рослину"
)
def start_create_plant(message):

    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    markup.row(
        types.KeyboardButton("🔙 Скасувати")
    )

    text = (
        "🌿 <b>Олівер витирає землю з рук і дивиться "
        "на тебе поверх окулярів.</b>\n\n"

        "Слухай сюди уважно!\n\n"

        "<b>Моя теплиця — це не смітник для дрібниць!</b>\n\n"

        "❌ Не смій саджати сюди всілякий дріб'язок "
        "на п'ять хвилин накшталт "
        "<i>«помити посуд»</i> чи "
        "<i>«винести сміття»</i>.\n"
        "Для цієї щоденної метушні у тебе є "
        "ритуали та сувої!\n\n"

        "❌ І навіть не думай заривати сюди дурні "
        "фантазії типу "
        "<i>«стати володарем Всесвіту до завтра»</i>!\n"
        "Твоє насіння просто вибухне від напруги "
        "і спалить мені весь ґрунт!\n\n"

        "🌱 Сюди ми саджаємо тільки "
        "<b>Справжні Магічні Рослини</b> — "
        "цілі, які мають чітку форму, вимірюваний "
        "результат і реальний дедлайн.\n\n"

        "🪵 <b>Олівер пояснює правила:</b>\n\n"

        "Твоя ціль повинна бути:\n"
        "🎯 <b>Конкретною</b> — що саме ти хочеш зробити?\n"
        "📏 <b>Вимірюваною</b> — як зрозуміти, що ти її завершив?\n"
        "🌱 <b>Досяжною</b> — без магії рівня "
        "«завтра прокинуся генієм».\n"
        "🧭 <b>Релевантною</b> — навіщо тобі ця ціль?\n"
        "📅 <b>Обмеженою в часі</b> — до якої дати "
        "ти її завершиш?\n\n"

        "🪴 Одним словом: посади те, що справді "
        "хочеш виростити.\n\n"

        "🦉 <b>Формула насіння:</b>\n"
        "<code>[Сфери] ; [Бали] ; [Дедлайн] ; "
        "[Назва] ; [Нагорода]</code>\n\n"

        "📚 <b>Приклад:</b>\n"
        "<code>🧠 ; 50 ; 30.09.26 ; "
        "Пройти курс з Python ; Купити нову книгу</code>\n\n"

        "🌿 Можна обрати кілька сфер. "
        "Тоді XP буде розділено між ними.\n\n"

        "⭐ <b>Бали:</b> від 15 до 75\n"
        "📅 <b>Дедлайн:</b> ДД.ММ.РР\n"
        "🎁 <b>Нагорода:</b> те, що дозволиш собі "
        "після того, як рослина виросте."
    )

    msg = bot.send_message(
        message.chat.id,
        text,
        parse_mode="HTML",
        reply_markup=markup
    )

    bot.register_next_step_handler(
        msg,
        process_plant_creation
    )


# ==================================================
# ОБРОБКА ВВЕДЕННЯ
# ==================================================

def process_plant_creation(message):

    if message.text == "🔙 Скасувати":

        bot.send_message(
            message.chat.id,
            "🌿 Олівер зітхає з полегшенням.\n\n"
            "Добре. Жодного насіння сьогодні не загублено. "
            "Повертаємось до теплиці.",
            parse_mode="HTML",
            reply_markup=get_greenhouse_menu()
        )

        return

    try:

        # ==================================================
        # Розділення формули
        # ==================================================

        parts = [
            part.strip()
            for part in message.text.split(";")
        ]

        if len(parts) != 5:

            raise ValueError(
                "Потрібно заповнити всі 5 частин формули:\n"
                "Сфери ; Бали ; Дедлайн ; Назва ; Нагорода"
            )

        spheres_text, xp_text, date_text, title, reward = parts


        # ==================================================
        # Перевірка сфер
        # ==================================================

        spheres = []

        for emoji in spheres_text:

            if emoji in EMOJI_TO_SPHERE:

                spheres.append(
                    EMOJI_TO_SPHERE[emoji]
                )

        if not spheres:

            raise ValueError(
                "Олівер не знайшов жодної правильної сфери."
            )

        if len(spheres) != len(set(spheres)):

            raise ValueError(
                "Одну й ту саму сферу не можна посадити "
                "двічі в одну рослину."
            )


        # ==================================================
        # Перевірка XP
        # ==================================================

        try:

            xp = int(xp_text)

        except ValueError:

            raise ValueError(
                "Кількість балів має бути числом."
            )

        if xp < 15 or xp > 75:

            raise ValueError(
                "Для рослини потрібно вказати "
                "від 15 до 75 балів."
            )


        # ==================================================
        # Перевірка дедлайну
        # ==================================================

        try:

            deadline = datetime.strptime(
                date_text,
                "%d.%m.%y"
            )

        except ValueError:

            raise ValueError(
                "Дедлайн має бути у форматі ДД.ММ.РР."
            )

        if deadline.date() < datetime.now().date():

            raise ValueError(
                "Цей дедлайн уже минув. "
                "Олівер не саджатиме рослину в минуле."
            )


        # ==================================================
        # Перевірка назви
        # ==================================================

        if len(title) < 3:

            raise ValueError(
                "Назва рослини має містити щонайменше "
                "3 символи."
            )


        # ==================================================
        # Перевірка нагороди
        # ==================================================

        if len(reward) < 2:

            raise ValueError(
                "Рослині потрібна гідна нагорода."
            )


        # ==================================================
        # Перевірка повторної назви
        # ==================================================

        user_id = str(message.from_user.id)

        player = get_player(user_id)

        plants = player.get("plants") or []

        normalized_title = " ".join(
            title.lower().split()
        )

        for plant in plants:

            existing_title = plant.get(
                "title",
                ""
            )

            normalized_existing = " ".join(
                existing_title.lower().split()
            )

            if normalized_existing == normalized_title:

                raise ValueError(
                    "Рослина з такою назвою вже росте "
                    "у твоїй теплиці."
                )


        # ==================================================
        # Створення рослини
        # ==================================================

        plant = {

            "spheres": spheres,

            "xp": xp,

            "deadline": date_text,

            "title": title,

            "reward": reward
        }


        plants.append(plant)


        update_player(
            user_id,
            {
                "plants": plants
            }
        )


        # ==================================================
        # УСПІШНЕ СТВОРЕННЯ
        # ==================================================

        bot.send_message(
            message.chat.id,

            "🌿 <b>Олівер мовчки дивиться на посаджене "
            "насіння...</b>\n\n"

            "Потім ледь помітно киває.\n\n"

            "✨ <b>Добре.</b> Це вже схоже на справжню "
            "рослину, а не на чергову примху.\n\n"

            f"🌱 <b>{title}</b>\n"
            f"⭐ Потенціал: {xp} XP\n"
            f"📅 Дедлайн: {date_text}\n"
            f"🎁 Нагорода: {reward}\n\n"

            "🌱 Насіння посаджено. "
            "Тепер твоя справа — не забути його виростити.",

            parse_mode="HTML",

            reply_markup=get_greenhouse_menu()
        )


    # ==================================================
    # ПОМИЛКА
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

            "🌿 <b>Олівер повільно піднімає брову.</b>\n\n"

            f"❌ {error}\n\n"

            "Спробуй ще раз за правильною формулою:\n\n"

            "<code>🧠 ; 50 ; 30.09.26 ; "
            "Пройти курс з Python ; Купити нову книгу</code>\n\n"

            "⭐ Бали: <b>15–75</b>",

            parse_mode="HTML",

            reply_markup=markup
        )

        bot.register_next_step_handler(
            message,
            process_plant_creation
        )
