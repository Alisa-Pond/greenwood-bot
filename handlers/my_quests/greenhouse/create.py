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
            "🌲<b>Олівер:🌲</b>\n\n "

            "« <b>Моя теплиця — це не смітник для дрібниць!</b>\n\n"

            "Не смій саджати сюди все, що можна зробити "
            "за кілька хвилин. "
            "Для такої метушні існують сувої та ритуали.\n\n"

            "І не принось мені фантазії на кшталт "
            "<i>«стати володарем Всесвіту до завтра»</i>.\n"
            "Навіть найкраще насіння не виросте з такої нісенітниці. 🌱\n\n"

            "🌱 У теплиці ми вирощуємо "
            "<b>Справжні Магічні Рослини</b> — "
            "цілі з чіткою формою, зрозумілим результатом "
            "і визначеним дедлайном.\n\n"

            "Твоя ціль повинна бути:\n"
            "🎯 <b>Конкретною</b> — що саме ти хочеш зробити?\n"
            "📏 <b>Вимірюваною</b> — як зрозуміти, що її завершено?\n"
            "🌱 <b>Досяжною</b> — без маячні на зразок "
            "«прокинутись завтра генієм».\n"
            "🧭 <b>Релевантною</b> — навіщо тобі ця ціль?\n"
            "📅 <b>Обмеженою в часі</b> — вкажи дедлайн\n\n"

            " <b>Дай мені точний опис насіння у наступному форматі. Я не люблю табличок із загадковими написами.</b>\n"
            "<code>Сфери ; Бали ; Дедлайн ; "
            "Назва; Нагорода</code>\n\n"

            "⛳️ Доступні сфери:\n "
            "<code>💪</code> Здоров'я\n"
            "<code>🧠</code> Мудрість\n"
            "<code>🎨</code> Творчість\n"
            "<code>💵</code> Фінанси\n"
            "<code>🤝</code> Зв'язки\n\n"
        
            "⭐ <b>Бали:</b> від 15 до 75\n"
            "📅 <b>Дедлайн:</b> ДД.ММ.РР\n"
            "🍭 <b>Нагорода:</b> те, чим ти порадуєш себе після збору врожаю\n"
            "⚖️ Якщо вказано кілька сфер, XP за виконання "
            "буде розділено між ними."
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
            "🌲<b>Олівер🌲</b>\n"
            "«Добре. Жодного насіння сьогодні не загублено. »",
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
                "🌲<b>Олівер🌲</b>\n"
                "«Потрібно заповнити всі 5 частин формули. Таблички під кожною рослиною мусять містити:\n"
                "Сфери ; Бали ; Дедлайн ; Назва ; Нагорода »"
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
                "🌲<b>Олівер🌲</b>\n"
                "«Не бачу тут жодної сфери яка б відповідала вимогам Грінвуду. »"
            )

        if len(spheres) != len(set(spheres)):

            raise ValueError(
                "🌲<b>Олівер🌲</b>\n"
                "«Дві однакові сфери? Що тинамагаєшся цим сказати?»"
        
            )


        # ==================================================
        # Перевірка XP
        # ==================================================

        try:

            xp = int(xp_text)

        except ValueError:

            raise ValueError(
                "🌲<b>Олівер🌲</b>\n"
                "« Що це за число??? »"
            )

        if xp < 15 or xp > 75:

            raise ValueError(
               "🌲<b>Олівер🌲</b>\n"
                "«Для рослини потрібно вказати "
                "від 15 до 75 балів.»"
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
                "🌲<b>Олівер🌲</b>\n"
                "«Дедлайн має бути у форматі ДД.ММ.РР.»"
            )

        if deadline.date() < datetime.now().date():

            raise ValueError(
                "🌲<b>Олівер:🌲</b>\n"
                "«Ти мандрівник в часі, ця дата вже минула?»"
            )


        # ==================================================
        # Перевірка назви
        # ==================================================

        if len(title) < 3:

            raise ValueError(
                "🌲<b>Олівер:🌲</b>\n"
                "«Назва рослини має містити щонайменше "
                "3 символи.»"
            )


        # ==================================================
        # Перевірка нагороди
        # ==================================================

        if len(reward) < 2:

            raise ValueError(
                "«Ти заслуговуєш більшого за зусилля які докладеш. »"
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
                    "🌲<b>Олівер:🌲</b>\n"
                    "«Рослина з такою назвою вже росте "
                    "у моїй теплиці.»"
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

            "🌲<b>Олівер🌲</b>\n\n"

            "🗯 «<b>Добре.</b> Це вже схоже на справжню "
            "рослину, а не на чергову примху.\n\n"

            f"🌱 <b>{title}</b>\n"
            f"⭐ Потенціал: {xp} XP\n"
            f"📅 Дедлайн: {date_text}\n"
            f"🍭 Нагорода: {reward}\n\n"

            "🌱 Насіння посаджено. "
            "Тепер твоя справа — докласти зусиль аби воно дало плідний урожай. »",

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

            f"❕ {error}\n\n"

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
