from datetime import datetime

from telebot import types

from services.config import bot
from services.database import get_player, update_player
from keyboards import get_main_menu


print("⚙️ Завантажено функціонал виконання справ...")


# ==================================================
# НАЛАШТУВАННЯ
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


WEEKDAYS = {
    0: "пн",
    1: "вт",
    2: "ср",
    3: "чт",
    4: "пт",
    5: "сб",
    6: "нд"
}


# ==================================================
# КНОПКА "ВИКОНАТИ СПРАВУ"
# ==================================================

@bot.message_handler(
    func=lambda message: message.text == "✅ Виконати справу"
)
def start_complete_activity(message):

    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    markup.row(
        types.KeyboardButton("📜 Запланована справа")
    )

    markup.row(
        types.KeyboardButton("🌿 Незапланована справа")
    )

    markup.row(
        types.KeyboardButton("🔙 Назад")
    )

    text = (
        "🦇 <b>Марчелло розгортає книгу виконаних справ.</b>\n\n"

        "— Ну що, герой, щось таки зробив? "
        "Тоді не смій залишати це без нагороди.\n\n"

        "Обери, що саме ти зробила:\n\n"

        "📜 <b>Запланована справа</b>\n"
        "— Виконати те, що вже чекало на тебе "
        "у сувоях, ритуалах або теплиці.\n\n"

        "🌿 <b>Незапланована справа</b>\n"
        "— Зробила щось корисне, чого заздалегідь "
        "не було в твоєму списку? Запиши це прямо зараз.\n\n"

        "✨ У будь-якому випадку магія не пропаде."
    )

    bot.send_message(
        message.chat.id,
        text,
        parse_mode="HTML",
        reply_markup=markup
    )


# ==================================================
# ЗАПЛАНОВАНА СПРАВА
# ==================================================

@bot.message_handler(
    func=lambda message: message.text == "📜 Запланована справа"
)
def choose_planned_activity(message):

    user_id = str(message.from_user.id)
    player = get_player(user_id)

    scrolls = player.get("scrolls") or []
    rituals = player.get("rituals") or []
    plants = player.get("plants") or []

    today = datetime.now().date()
    today_weekday = WEEKDAYS[today.weekday()]

    activities = []

    # --------------------------------------------------
    # СУВОЇ
    # --------------------------------------------------

    for index, scroll in enumerate(scrolls):

        title = scroll.get(
            "title",
            scroll.get("name", "Без назви")
        )

        xp = scroll.get("xp", 0)

        activities.append({
            "type": "scroll",
            "index": index,
            "title": title,
            "xp": xp,
            "label": f"📜 {title} ({xp} XP)"
        })


    # --------------------------------------------------
    # РИТУАЛИ
    # --------------------------------------------------

    for index, ritual in enumerate(rituals):

        days = ritual.get("days", [])

        if isinstance(days, str):

            if days.lower().strip() == "щодня":

                ritual_days = [
                    "пн", "вт", "ср",
                    "чт", "пт", "сб", "нд"
                ]

            else:

                ritual_days = [
                    day.strip().lower()
                    for day in days.split(",")
                ]

        elif isinstance(days, list):

            ritual_days = [
                str(day).strip().lower()
                for day in days
            ]

        else:

            ritual_days = []


        # Ритуал можна виконати лише в день,
        # для якого він запланований.

        if today_weekday not in ritual_days:
            continue


        title = ritual.get(
            "title",
            ritual.get("name", "Без назви")
        )

        xp = ritual.get("xp", 0)

        activities.append({
            "type": "ritual",
            "index": index,
            "title": title,
            "xp": xp,
            "label": f"🔄 {title} ({xp} XP)"
        })


    # --------------------------------------------------
    # РОСЛИНИ
    # --------------------------------------------------

    for index, plant in enumerate(plants):

        title = plant.get(
            "title",
            plant.get("name", "Без назви")
        )

        xp = plant.get("xp", 0)

        activities.append({
            "type": "plant",
            "index": index,
            "title": title,
            "xp": xp,
            "label": f"🌱 {title} ({xp} XP)"
        })


    # --------------------------------------------------
    # НЕМАЄ СПРАВ
    # --------------------------------------------------

    if not activities:

        markup = types.ReplyKeyboardMarkup(
            resize_keyboard=True
        )

        markup.row(
            types.KeyboardButton("🔙 Назад")
        )

        bot.send_message(
            message.chat.id,

            "🦇 <b>Марчелло перегортає сторінки...</b>\n\n"

            "— Тут порожньо.\n\n"

            "Немає жодної запланованої справи, "
            "яку можна виконати сьогодні.\n\n"

            "Можеш записати незаплановану справу.",

            parse_mode="HTML",
            reply_markup=markup
        )

        return


    # --------------------------------------------------
    # СПИСОК
    # --------------------------------------------------

    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    for number, activity in enumerate(
        activities,
        start=1
    ):

        markup.row(
            types.KeyboardButton(
                f"{number}. {activity['label']}"
            )
        )


    markup.row(
        types.KeyboardButton("🔙 Назад")
    )


    text = (
        "🦇 <b>Марчелло розгортає список.</b>\n\n"

        "— Ось що сьогодні чекає на твою руку "
        "і трохи героїчної рішучості.\n\n"

        "Обери виконану справу:\n\n"
    )


    for number, activity in enumerate(
        activities,
        start=1
    ):

        text += (
            f"<b>{number}.</b> "
            f"{activity['label']}\n"
        )


    msg = bot.send_message(
        message.chat.id,
        text,
        parse_mode="HTML",
        reply_markup=markup
    )

    bot.register_next_step_handler(
        msg,
        process_planned_activity,
        activities
    )


# ==================================================
# ОБРОБКА ЗАПЛАНОВАНОЇ СПРАВИ
# ==================================================

def process_planned_activity(
    message,
    activities
):

    if message.text == "🔙 Назад":

        bot.send_message(
            message.chat.id,
            "🌲 Повертаємось до головної галявини.",
            reply_markup=get_main_menu()
        )

        return


    try:

        number = int(
            message.text.split(".")[0]
        )

        if number < 1 or number > len(activities):

            raise ValueError


    except (ValueError, IndexError):

        bot.send_message(
            message.chat.id,

            "🦇 <b>Марчелло постукав пальцем по столу.</b>\n\n"
            "— Номер. Просто номер зі списку.\n\n"
            "Спробуй ще раз.",

            parse_mode="HTML"
        )

        bot.register_next_step_handler(
            message,
            process_planned_activity,
            activities
        )

        return


    activity = activities[number - 1]

    user_id = str(message.from_user.id)

    player = get_player(user_id)


    # ==================================================
    # ЗАХИСТ ВІД ЗМІН
    # ==================================================

    activity_type = activity["type"]
    activity_index = activity["index"]


    if activity_type == "scroll":

        items = player.get("scrolls") or []

    elif activity_type == "ritual":

        items = player.get("rituals") or []

    else:

        items = player.get("plants") or []


    if (
        activity_index < 0
        or activity_index >= len(items)
    ):

        bot.send_message(
            message.chat.id,

            "🦇 <b>Марчелло моргнув.</b>\n\n"
            "— Ця справа кудись зникла. "
            "Спробуй відкрити список ще раз.",

            parse_mode="HTML",
            reply_markup=get_main_menu()
        )

        return


    selected = items[activity_index]

    title = selected.get(
        "title",
        selected.get("name", "Без назви")
    )

    xp = float(
        selected.get("xp", 0)
    )


    spheres = selected.get(
        "spheres",
        []
    )


    # ==================================================
    # НАРАХУВАННЯ XP
    # ==================================================

    award_xp(
        player,
        spheres,
        xp
    )


    # ==================================================
    # ЗАПЛАНОВАНА СПРАВА
    # ==================================================

    if activity_type == "scroll":

        items.pop(activity_index)

        player["scrolls"] = items


    elif activity_type == "plant":

        items.pop(activity_index)

        player["plants"] = items


    elif activity_type == "ritual":

        # Ритуал не видаляємо.
        # Він залишається активним і буде доступний
        # знову після нового дня.

        selected["completed_today"] = True

        items[activity_index] = selected

        player["rituals"] = items


    update_player(
        user_id,
        player
    )


    # ==================================================
    # ПОВІДОМЛЕННЯ
    # ==================================================

    bot.send_message(
        message.chat.id,

        "🦇 <b>Марчелло задоволено закриває книгу.</b>\n\n"

        f"✨ <b>{title}</b> виконано!\n\n"

        f"⭐ Ти отримуєш <b>{xp:.1f} XP</b>.\n\n"

        "— Отак. Зроблене діло має бути "
        "записане в хроніках.",

        parse_mode="HTML",
        reply_markup=get_main_menu()
    )


# ==================================================
# НЕЗАПЛАНОВАНА СПРАВА
# ==================================================

@bot.message_handler(
    func=lambda message: message.text == "🌿 Незапланована справа"
)
def start_unplanned_activity(message):

    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    markup.row(
        types.KeyboardButton("🔙 Скасувати")
    )


    text = (
        "🦇 <b>Марчелло перегортає чистий аркуш.</b>\n\n"

        "— Не все корисне народжується "
        "у сувоях заздалегідь.\n\n"

        "Якщо ти зробила щось хороше "
        "і цього не було в планах, "
        "запиши це зараз.\n\n"

        "<b>Формула:</b>\n"
        "<code>[Сфери] ; [Бали] ; [Назва справи]</code>\n\n"

        "Наприклад:\n"
        "<code>💪 ; 6 ; Зробила зарядку</code>\n"
        "<code>🧠🎨 ; 10 ; Вивчила нову тему і намалювала схему</code>\n\n"

        "⭐ Бали: від <b>4 до 14</b>\n"
        "🎯 Якщо сфер кілька, XP буде розділено між ними.\n\n"

        "📚 Доступні сфери:\n"
        "💪 Здоров'я\n"
        "🧠 Мудрість\n"
        "🎨 Творчість\n"
        "💵 Фінанси\n"
        "🤝 Зв'язки"
    )


    msg = bot.send_message(
        message.chat.id,
        text,
        parse_mode="HTML",
        reply_markup=markup
    )


    bot.register_next_step_handler(
        msg,
        process_unplanned_activity
    )


# ==================================================
# ОБРОБКА НЕЗАПЛАНОВАНОЇ СПРАВИ
# ==================================================

def process_unplanned_activity(message):

    if message.text == "🔙 Скасувати":

        bot.send_message(
            message.chat.id,
            "🦇 Марчелло закриває чистий аркуш.\n\n"
            "Повертаємось до головного меню.",

            parse_mode="HTML",
            reply_markup=get_main_menu()
        )

        return


    try:

        parts = [
            part.strip()
            for part in message.text.split(";")
        ]


        if len(parts) != 3:

            raise ValueError(
                "Потрібно вказати сфери, бали та назву."
            )


        spheres_text, xp_text, title = parts


        # ==================================================
        # СФЕРИ
        # ==================================================

        spheres = []

        for emoji in spheres_text:

            if emoji in EMOJI_TO_SPHERE:

                sphere = EMOJI_TO_SPHERE[emoji]

                if sphere not in spheres:

                    spheres.append(sphere)


        if not spheres:

            raise ValueError(
                "Не знайдено правильної сфери."
            )


        # ==================================================
        # XP
        # ==================================================

        try:

            xp = int(xp_text)

        except ValueError:

            raise ValueError(
                "Бали мають бути числом."
            )


        if xp < 4 or xp > 14:

            raise ValueError(
                "Кількість балів має бути від 4 до 14."
            )


        # ==================================================
        # НАЗВА
        # ==================================================

        if len(title) < 3:

            raise ValueError(
                "Назва справи занадто коротка."
            )


        # ==================================================
        # НАРАХУВАННЯ
        # ==================================================

        user_id = str(message.from_user.id)

        player = get_player(user_id)


        award_xp(
            player,
            spheres,
            xp
        )


        update_player(
            user_id,
            player
        )


        # ==================================================
        # УСПІХ
        # ==================================================

        sphere_text = ", ".join(
            SPHERE_NAMES[sphere]
            for sphere in spheres
        )


        bot.send_message(
            message.chat.id,

            "🦇 <b>Марчелло посміхається краєчком губ.</b>\n\n"

            "— Непогано. Навіть без сувою "
            "ти не дозволила хорошій справі "
            "пройти повз тебе.\n\n"

            f"✨ <b>{title}</b>\n"
            f"⭐ Нагорода: <b>{xp:.1f} XP</b>\n"
            f"🎯 Сфери: {sphere_text}\n\n"

            "🔥 XP записано до твоїх хронік.",

            parse_mode="HTML",
            reply_markup=get_main_menu()
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

            "🦇 <b>Марчелло насупився.</b>\n\n"

            f"❌ {error}\n\n"

            "Спробуй ще раз за формулою:\n\n"

            "<code>💪🧠 ; 10 ; Назва справи</code>",

            parse_mode="HTML",
            reply_markup=markup
        )


        bot.register_next_step_handler(
            message,
            process_unplanned_activity
        )


# ==================================================
# XP
# ==================================================

def award_xp(player, spheres, xp):

    if not spheres:

        return


    share = xp / len(spheres)


    player["xp_total"] = float(
        player.get("xp_total", 0)
    ) + xp


    player_spheres = player.get(
        "spheres",
        {}
    )


    for sphere_key in spheres:

        if sphere_key not in player_spheres:

            continue


        sphere = player_spheres[sphere_key]


        sphere["xp"] = float(
            sphere.get("xp", 0)
        ) + share


        # ==================================================
        # ЛЕВЕЛАП
        # ==================================================

        max_xp = float(
            sphere.get("max_xp", 10)
        )


        while sphere["xp"] >= max_xp:

            sphere["xp"] -= max_xp

            sphere["lvl"] = int(
                sphere.get("lvl", 1)
            ) + 1

            max_xp *= 2

            sphere["max_xp"] = max_xp


    player["spheres"] = player_spheres
