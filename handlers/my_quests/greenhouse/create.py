from datetime import datetime

from telebot import types

from services.config import bot
from services.database import get_player, update_player
from keyboards import get_greenhouse_menu


print("⚙️ Завантажено посадку рослин...")


# ==================================================
# 🌱 СФЕРИ
# ==================================================

EMOJI_TO_SPHERE = {
    "💪": "health",
    "🧠": "wisdom",
    "🎨": "art",
    "💵": "finance",
    "🤝": "relations"
}


# ==================================================
# 🌱 ПОЧАТОК СТВОРЕННЯ
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
        "🪵 <b>Олівер повільно піднімає погляд від грядки.</b>\n\n"

        "«Слухай сюди уважно! "
        "<b>Моя теплиця — це не смітник для дрібниць!</b>»\n\n"

        "❌ Не смій саджати сюди всілякий дріб'язок "
        "на п'ять хвилин накшталт "
        "<i>«помити посуд»</i> чи "
        "<i>«винести сміття»</i>.\n"
        "Для цієї щоденної метушні у тебе є ритуали та сувої!\n\n"

        "❌ І навіть не думай заривати сюди дурні фантазії "
        "типу <i>«стати володарем Всесвіту до завтра»</i>!\n"
        "Твоє насіння просто вибухне від напруги "
        "і спалить мені весь ґрунт!\n\n"

        "🌱 Сюди ми саджаємо тільки "
        "<b>Справжні Магічні Рослини</b> — "
        "цілі, які справді варті часу та сил.\n\n"

        "Олівер кладе перед тобою пакетик насіння.\n\n"

        "«Якщо вже зібралася щось саджати, "
        "то хоча б зроби це правильно.»\n\n"

        "📜 <b>Формула посадки:</b>\n"
        "<code>[Сфери] ; [Бали] ; [Дедлайн] ; "
        "[Назва + нагорода в реальному житті]</code>\n\n"

        "🌿 <b>Сфера</b> — що саме розвиватиме ця ціль.\n"
        "Можна обрати одну або кілька:\n"
        "💪 Здоров'я\n"
        "🧠 Мудрість\n"
        "🎨 Творчість\n"
        "💵 Фінанси\n"
        "🤝 Зв'язки\n\n"

        "⭐ <b>Бали:</b> від 1 до 14.\n"
        "Якщо сфер кілька, XP буде розділено між ними.\n\n"

        "📅 <b>Дедлайн:</b> ДД.ММ.РР.\n"
        "Дата має бути сьогоднішньою або майбутньою.\n\n"

        "🌱 <b>Назва + нагорода:</b>\n"
        "Назви конкретно, що ти хочеш виростити, "
        "і чим винагородиш себе після збору врожаю.\n\n"

        "Наприклад:\n"
        "<code>🧠 ; 10 ; 30.09.26 ; "
        "Пройти курс з Python + купити нову книгу</code>\n\n"

        "«Не треба саджати абстрактне "
        "«стати кращою версією себе».\n"
        "Мені потрібна рослина, яку можна побачити, "
        "виростити й зрештою зібрати.» 🌱"
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
# 🌱 ОБРОБКА ВВЕДЕННЯ
# ==================================================

def process_plant_creation(message):

    if message.text == "🔙 Скасувати":

        bot.send_message(
            message.chat.id,
            "🪵 Олівер буркнув щось про «марно витрачене насіння» "
            "і повернувся до своїх грядок.",
            reply_markup=get_greenhouse_menu()
        )

        return


    try:

        # ==================================================
        # РОЗБИВАЄМО ФОРМУЛУ
        # ==================================================

        parts = [
            part.strip()
            for part in message.text.split(";")
        ]

        if len(parts) != 4:

            raise ValueError(
                "Потрібно заповнити всі 4 частини формули."
            )


        spheres_text, xp_text, date_text, title_reward = parts


        # ==================================================
        # ПЕРЕВІРКА СФЕР
        # ==================================================

        spheres = []

        for emoji in spheres_text:

            if emoji in EMOJI_TO_SPHERE:

                sphere_key = EMOJI_TO_SPHERE[emoji]

                if sphere_key not in spheres:

                    spheres.append(
                        sphere_key
                    )


        if not spheres:

            raise ValueError(
                "Не знайдено жодної правильної сфери."
            )


        # ==================================================
        # ПЕРЕВІРКА XP
        # ==================================================

        try:

            xp = int(xp_text)

        except ValueError:

            raise ValueError(
                "Кількість балів має бути цілим числом."
            )


        if xp < 1 or xp > 14:

            raise ValueError(
                "Для рослини кількість балів має бути від 1 до 14."
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
                "Дедлайн має бути у форматі ДД.ММ.РР."
            )


        if deadline.date() < datetime.now().date():

            raise ValueError(
                "Ця дата вже минула. "
                "Насіння не проросте в минулому."
            )


        # ==================================================
        # ПЕРЕВІРКА НАЗВИ ТА НАГОРОДИ
        # ==================================================

        if len(title_reward) < 5:

            raise ValueError(
                "Назва цілі та нагорода мають бути конкретнішими."
            )


        # ==================================================
        # ПЕРЕВІРКА НА ОДНАКОВІ НАЗВИ
        # ==================================================

        user_id = str(message.from_user.id)

        player = get_player(user_id)

        plants = player.get("plants") or []


        for plant in plants:

            existing_title = plant.get(
                "title",
                ""
            ).strip().lower()

            new_title = title_reward.strip().lower()

            if existing_title == new_title:

                raise ValueError(
                    "Рослина з такою назвою вже росте у твоїй теплиці."
                )


        # ==================================================
        # СТВОРЕННЯ РОСЛИНИ
        # ==================================================

        plant = {

            "title": title_reward,

            "spheres": spheres,

            "xp": xp,

            "deadline": date_text,

            "status": "active"

        }


        plants.append(plant)


        # ==================================================
        # ЗБЕРЕЖЕННЯ У SUPABASE
        # ==================================================

        update_player(
            user_id,
            {
                "plants": plants
            }
        )


        # ==================================================
        # УСПІШНЕ ПОВІДОМЛЕННЯ
        # ==================================================

        sphere_emojis = ""

        for sphere_key in spheres:

            for emoji, key in EMOJI_TO_SPHERE.items():

                if key == sphere_key:

                    sphere_emojis += emoji


        bot.send_message(
            message.chat.id,

            "🌱 <b>Олівер завмирає на мить...</b>\n\n"

            "Він уважно оглядає посаджене насіння, "
            "проводить пальцями по землі й нарешті киває.\n\n"

            "«Ну... це вже схоже на справжню рослину.» 🌿\n\n"

            "✨ <b>Ціль успішно посаджено!</b>\n\n"

            f"🌱 <b>{title_reward}</b>\n"
            f"🎯 Сфери: {sphere_emojis}\n"
            f"⭐ Нагорода: {xp} XP\n"
            f"📅 Дедлайн: {date_text}\n\n"

            f"🌿 Активних рослин у теплиці: "
            f"<b>{len(plants)}</b>\n\n"

            "«Доглядай за нею. "
            "І не забудь, що рослини ростуть не від бажань, "
            "а від того, що ти щось робиш.»",

            parse_mode="HTML",

            reply_markup=get_greenhouse_menu()
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

            "🪵 <b>Олівер дивиться на тебе поверх окулярів.</b>\n\n"

            f"❌ {error}\n\n"

            "«Я ж просив нормально посадити насіння. "
            "Спробуй ще раз.»\n\n"

            "Правильний формат:\n"
            "<code>🧠 ; 10 ; 30.09.26 ; "
            "Пройти курс з Python + купити нову книгу</code>",

            parse_mode="HTML",

            reply_markup=markup
        )


        bot.register_next_step_handler(
            message,
            process_plant_creation
        )
