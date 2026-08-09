from datetime import datetime

from telebot import types

from services.config import bot
from services.database import get_player, update_player


print("⚙️ Завантажено систему виконання справ...")


# =========================================================
# СФЕРИ
# =========================================================

SPHERE_NAMES = {
    "health": "💪",
    "wisdom": "🧠",
    "art": "🎨",
    "finance": "💵",
    "relations": "🤝"
}


# =========================================================
# ДОПОМІЖНІ ФУНКЦІЇ
# =========================================================

def get_sphere_emoji(sphere):
    if sphere in SPHERE_NAMES:
        return SPHERE_NAMES[sphere]

    if sphere in SPHERE_NAMES.values():
        return sphere

    return sphere


def get_spheres(item):
    """
    Отримує сфери з сувою / ритуалу / рослини.
    Підтримує кілька форматів старих записів.
    """

    spheres = item.get("spheres")

    if not spheres:
        spheres = item.get("sphere")

    if not spheres:
        return []

    if isinstance(spheres, str):

        result = []

        for sphere_key, emoji in SPHERE_NAMES.items():

            if sphere_key in spheres or emoji in spheres:
                result.append(emoji)

        if result:
            return result

        return [spheres]

    if isinstance(spheres, list):

        result = []

        for sphere in spheres:

            if isinstance(sphere, dict):

                emoji = sphere.get("emoji")

                if emoji:
                    result.append(emoji)

                elif sphere.get("name"):
                    result.append(sphere["name"])

            else:
                result.append(get_sphere_emoji(sphere))

        return result

    return []


def get_title(item):
    return (
        item.get("title")
        or item.get("name")
        or item.get("task")
        or "Без назви"
    )


def get_xp(item):

    try:
        return float(
            item.get("xp")
            or item.get("points")
            or item.get("reward_xp")
            or 0
        )

    except (TypeError, ValueError):
        return 0.0


def get_today():
    return datetime.now().strftime("%d.%m.%Y")


def add_xp_to_spheres(player, spheres, total_xp):

    if not spheres or total_xp <= 0:
        return

    player_spheres = player.get("spheres") or {}

    share = total_xp / len(spheres)

    for sphere in spheres:

        sphere_key = None

        for key, emoji in SPHERE_NAMES.items():

            if sphere == key or sphere == emoji:
                sphere_key = key
                break

        if sphere in player_spheres:
            sphere_key = sphere

        if not sphere_key:
            continue

        if sphere_key not in player_spheres:
            continue

        current_xp = float(
            player_spheres[sphere_key].get("xp", 0)
        )

        player_spheres[sphere_key]["xp"] = (
            current_xp + share
        )

        while (
            player_spheres[sphere_key]["xp"]
            >= float(
                player_spheres[sphere_key].get(
                    "max_xp",
                    10
                )
            )
        ):

            max_xp = float(
                player_spheres[sphere_key].get(
                    "max_xp",
                    10
                )
            )

            player_spheres[sphere_key]["xp"] -= max_xp

            player_spheres[sphere_key]["lvl"] = (
                int(
                    player_spheres[sphere_key].get(
                        "lvl",
                        1
                    )
                )
                + 1
            )

            player_spheres[sphere_key]["max_xp"] = (
                max_xp * 1.5
            )


def add_total_xp(player, xp):

    player["xp_total"] = (
        float(player.get("xp_total", 0))
        + xp
    )


def build_back_button():

    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    markup.row(
        types.KeyboardButton("🔙 Назад")
    )

    return markup


# =========================================================
# ГОЛОВНЕ МЕНЮ ВИКОНАННЯ
# =========================================================

@bot.message_handler(
    func=lambda message: message.text == "✅ Виконати справу"
)
def start_complete(message):

    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    markup.row(
        types.KeyboardButton("📜 Виконати сувій"),
        types.KeyboardButton("🔄 Провести ритуал")
    )

    markup.row(
        types.KeyboardButton("🌱 Завершити вирощування")
    )

    markup.row(
        types.KeyboardButton("✨ Зробити поза планом")
    )

    markup.row(
        types.KeyboardButton("🔙 Назад")
    )

    bot.send_message(
        message.chat.id,

        "🪷 <b>Час перетворити зроблене на XP!</b>\n\n"

        "Обери, що саме ти щойно завершила:\n\n"

        "📜 <b>Сувій</b> — запланована одноразова справа.\n"
        "🔄 <b>Ритуал</b> — справа, що повертається за розкладом.\n"
        "🌱 <b>Рослина</b> — велика ціль, яку ти виростила до кінця.\n"
        "✨ <b>Поза планом</b> — корисна справа, якої не було в планах.\n\n"

        "🦇 <b>Марчелло</b> уже тримає перо над книгою XP.",

        parse_mode="HTML",
        reply_markup=markup
    )


# =========================================================
# СУВОЇ
# =========================================================

@bot.message_handler(
    func=lambda message: message.text == "📜 Виконати сувій"
)
def choose_scroll(message):

    user_id = str(message.from_user.id)

    player = get_player(user_id)

    scrolls = player.get("scrolls") or []

    if not scrolls:

        bot.send_message(
            message.chat.id,

            "📜 <b>Жодного активного сувою.</b>\n\n"
            "Марчелло вже не має чим тебе завантажити. "
            "Поки що. 🦇",

            parse_mode="HTML",
            reply_markup=build_back_button()
        )

        return

    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    for index, scroll in enumerate(scrolls):

        title = get_title(scroll)

        markup.row(
            types.KeyboardButton(
                f"📜 {index + 1}. {title}"
            )
        )

    markup.row(
        types.KeyboardButton("🔙 Назад")
    )

    msg = bot.send_message(
        message.chat.id,

        "📜 <b>Обери сувій, який виконано:</b>",

        parse_mode="HTML",
        reply_markup=markup
    )

    bot.register_next_step_handler(
        msg,
        complete_scroll
    )


def complete_scroll(message):

    if message.text == "🔙 Назад":
        start_complete(message)
        return

    user_id = str(message.from_user.id)

    player = get_player(user_id)

    scrolls = player.get("scrolls") or []

    selected_index = None

    try:

        selected_index = (
            int(
                message.text.split(".")[0]
                .replace("📜", "")
                .strip()
            )
            - 1
        )

    except (ValueError, IndexError):
        pass

    if (
        selected_index is None
        or selected_index < 0
        or selected_index >= len(scrolls)
    ):

        bot.send_message(
            message.chat.id,

            "🦇 <b>Марчелло насупився.</b>\n\n"
            "Такого сувою в реєстрі немає. "
            "Обери його кнопкою.",

            parse_mode="HTML"
        )

        choose_scroll(message)
        return

    scroll = scrolls[selected_index]

    title = get_title(scroll)
    xp = get_xp(scroll)
    spheres = get_spheres(scroll)

    # -----------------------------------------------------
    # НАРАХУВАННЯ XP
    # -----------------------------------------------------

    add_total_xp(player, xp)

    add_xp_to_spheres(
        player,
        spheres,
        xp
    )

    # -----------------------------------------------------
    # АРХІВ СУВОЇВ
    # -----------------------------------------------------

    archive = player.get("scroll_archive") or []

    completed_scroll = dict(scroll)

    completed_scroll["completed_date"] = get_today()

    archive.append(completed_scroll)

    # -----------------------------------------------------
    # ВИДАЛЯЄМО З АКТИВНИХ
    # -----------------------------------------------------

    scrolls.pop(selected_index)

    player["scrolls"] = scrolls
    player["scroll_archive"] = archive

    update_player(
        user_id,
        {
            "xp_total": player["xp_total"],
            "spheres": player["spheres"],
            "scrolls": player["scrolls"],
            "scroll_archive": player["scroll_archive"]
        }
    )

    bot.send_message(
        message.chat.id,

        "🦇 <b>Марчелло ставить останню печатку.</b>\n\n"

        f"📜 <b>{title}</b>\n"
        f"⭐ Отримано: <b>{xp:.1f} XP</b>\n"
        f"🎯 Сфери: {' '.join(get_sphere_emoji(s) for s in spheres)}\n\n"

        "✨ Сувій виконано й відправлено до Архіву.\n"
        "Тепер ця справа вже не висить над головою.",

        parse_mode="HTML",
        reply_markup=build_back_button()
    )


# =========================================================
# РИТУАЛИ
# =========================================================

@bot.message_handler(
    func=lambda message: message.text == "🔄 Провести ритуал"
)
def choose_ritual(message):

    user_id = str(message.from_user.id)

    player = get_player(user_id)

    rituals = player.get("rituals") or []

    if not rituals:

        bot.send_message(
            message.chat.id,

            "🔄 <b>Жодного активного ритуалу.</b>\n\n"
            "Ліс сьогодні напрочуд тихий. 🌲",

            parse_mode="HTML",
            reply_markup=build_back_button()
        )

        return

    today = datetime.now().weekday()

    weekday_names = [
        "пн",
        "вт",
        "ср",
        "чт",
        "пт",
        "сб",
        "нд"
    ]

    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    available = []

    for index, ritual in enumerate(rituals):

        days = ritual.get("days") or []

        is_today = False

        if ritual.get("daily") is True:
            is_today = True

        elif today in days:
            is_today = True

        elif isinstance(days, list):

            if weekday_names[today] in days:
                is_today = True

        if is_today:

            available.append(
                (index, ritual)
            )

    if not available:

        bot.send_message(
            message.chat.id,

            "💤 <b>Сьогодні жоден ритуал не чекає на виконання.</b>\n\n"
            "Твої ритуали відпочивають до свого дня. 🌙",

            parse_mode="HTML",
            reply_markup=build_back_button()
        )

        return

    for index, ritual in available:

        title = get_title(ritual)

        markup.row(
            types.KeyboardButton(
                f"🔄 {index + 1}. {title}"
            )
        )

    markup.row(
        types.KeyboardButton("🔙 Назад")
    )

    msg = bot.send_message(
        message.chat.id,

        "🔄 <b>Сьогоднішні ритуали:</b>\n\n"
        "Обери той, який щойно провела.",

        parse_mode="HTML",
        reply_markup=markup
    )

    bot.register_next_step_handler(
        msg,
        complete_ritual,
        available
    )


def complete_ritual(message, available):

    if message.text == "🔙 Назад":
        start_complete(message)
        return

    user_id = str(message.from_user.id)

    player = get_player(user_id)

    rituals = player.get("rituals") or []

    selected_index = None

    try:

        selected_index = (
            int(
                message.text.split(".")[0]
                .replace("🔄", "")
                .strip()
            )
            - 1
        )

    except (ValueError, IndexError):
        pass

    if (
        selected_index is None
        or selected_index < 0
        or selected_index >= len(rituals)
    ):

        bot.send_message(
            message.chat.id,
            "🔄 Не вдалося знайти цей ритуал."
        )

        choose_ritual(message)
        return

    ritual = rituals[selected_index]

    title = get_title(ritual)
    xp = get_xp(ritual)
    spheres = get_spheres(ritual)

    today = get_today()

    if ritual.get("last_completed") == today:

        bot.send_message(
            message.chat.id,

            "🌙 <b>Цей ритуал уже виконано сьогодні.</b>\n\n"
            "Не треба чаклувати над одним завданням двічі. ✨",

            parse_mode="HTML",
            reply_markup=build_back_button()
        )

        return

    # -----------------------------------------------------
    # XP
    # -----------------------------------------------------

    add_total_xp(player, xp)

    add_xp_to_spheres(
        player,
        spheres,
        xp
    )

    # -----------------------------------------------------
    # ПОЗНАЧАЄМО ВИКОНАНИМ
    # -----------------------------------------------------

    ritual["last_completed"] = today

    rituals[selected_index] = ritual

    player["rituals"] = rituals

    # -----------------------------------------------------
    # АРХІВ РИТУАЛІВ
    #
    # Ритуал НЕ переноситься з активних у архів.
    # В архів потрапляє саме запис про виконання.
    # -----------------------------------------------------

    archive = player.get("ritual_archive") or []

    completed_ritual = dict(ritual)

    completed_ritual["completed_date"] = today

    archive.append(completed_ritual)

    player["ritual_archive"] = archive

    update_player(
        user_id,
        {
            "xp_total": player["xp_total"],
            "spheres": player["spheres"],
            "rituals": player["rituals"],
            "ritual_archive": player["ritual_archive"]
        }
    )

    bot.send_message(
        message.chat.id,

        "🔥 <b>Ритуал проведено!</b>\n\n"

        f"🔄 <b>{title}</b>\n"
        f"⭐ Отримано: <b>{xp:.1f} XP</b>\n"
        f"🎯 Сфери: {' '.join(get_sphere_emoji(s) for s in spheres)}\n\n"

        "🕯️ Полум'я ритуалу згасло до наступного "
        "призначеного дня.",

        parse_mode="HTML",
        reply_markup=build_back_button()
    )


# =========================================================
# РОСЛИНИ
# =========================================================

@bot.message_handler(
    func=lambda message: message.text == "🌱 Завершити вирощування"
)
def choose_plant(message):

    user_id = str(message.from_user.id)

    player = get_player(user_id)

    plants = player.get("plants") or []

    if not plants:

        bot.send_message(
            message.chat.id,

            "🌱 <b>У теплиці немає рослин, готових до збору.</b>\n\n"
            "Олівер оглядає ґрунт і хмикає:\n\n"
            "«Ну? Чого стоїш? Посади щось путнє.» 🌿",

            parse_mode="HTML",
            reply_markup=build_back_button()
        )

        return

    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    for index, plant in enumerate(plants):

        title = get_title(plant)

        markup.row(
            types.KeyboardButton(
                f"🌱 {index + 1}. {title}"
            )
        )

    markup.row(
        types.KeyboardButton("🔙 Назад")
    )

    msg = bot.send_message(
        message.chat.id,

        "🌿 <b>Яку рослину ти виростила?</b>\n\n"
        "Обери її зі списку:",

        parse_mode="HTML",
        reply_markup=markup
    )

    bot.register_next_step_handler(
        msg,
        complete_plant
    )


def complete_plant(message):

    if message.text == "🔙 Назад":
        start_complete(message)
        return

    user_id = str(message.from_user.id)

    player = get_player(user_id)

    plants = player.get("plants") or []

    selected_index = None

    try:

        selected_index = (
            int(
                message.text.split(".")[0]
                .replace("🌱", "")
                .strip()
            )
            - 1
        )

    except (ValueError, IndexError):
        pass

    if (
        selected_index is None
        or selected_index < 0
        or selected_index >= len(plants)
    ):

        bot.send_message(
            message.chat.id,

            "🌿 Олівер піднімає брову.\n\n"
            "«Цієї рослини в теплиці немає. "
            "Обирай із того, що справді посаджено.»",

            parse_mode="HTML"
        )

        choose_plant(message)
        return

    plant = plants[selected_index]

    title = get_title(plant)
    xp = get_xp(plant)
    spheres = get_spheres(plant)

    # -----------------------------------------------------
    # XP
    # -----------------------------------------------------

    add_total_xp(player, xp)

    add_xp_to_spheres(
        player,
        spheres,
        xp
    )

    # -----------------------------------------------------
    # АРХІВ РОСЛИН
    # -----------------------------------------------------

    archive = player.get("plant_archive") or []

    completed_plant = dict(plant)

    completed_plant["completed_date"] = get_today()

    archive.append(completed_plant)

    # -----------------------------------------------------
    # ВИДАЛЯЄМО З АКТИВНИХ
    # -----------------------------------------------------

    plants.pop(selected_index)

    player["plants"] = plants
    player["plant_archive"] = archive

    update_player(
        user_id,
        {
            "xp_total": player["xp_total"],
            "spheres": player["spheres"],
            "plants": player["plants"],
            "plant_archive": player["plant_archive"]
        }
    )

    reward = plant.get(
        "reward",
        "твоя нагорода"
    )

    bot.send_message(
        message.chat.id,

        "🌳 <b>Олівер мовчки оглядає вирощену рослину.</b>\n\n"

        f"🌱 <b>{title}</b>\n\n"

        "«Гаразд.\n"
        "Це вже можна назвати справжнім урожаєм.»\n\n"

        f"⭐ Отримано: <b>{xp:.1f} XP</b>\n"
        f"🎁 Нагорода: <b>{reward}</b>\n\n"

        "🌿 Рослину переміщено до Архіву теплиці.",

        parse_mode="HTML",
        reply_markup=build_back_button()
    )


# =========================================================
# НЕЗАПЛАНОВАНА СПРАВА
# =========================================================

@bot.message_handler(
    func=lambda message: message.text == "✨ Зробити поза планом"
)
def start_unplanned(message):

    markup = build_back_button()

    msg = bot.send_message(
        message.chat.id,

        "🦇 <b>Марчелло відкладає перо.</b>\n\n"

        "«Не все корисне в житті народжується "
        "в календарі, люба чаклунко.»\n\n"

        "Запиши справу у форматі:\n\n"

        "<code>💪🧠 ; 10 ; Вивчити нову тему</code>\n\n"

        "🎯 Можна вказати кілька сфер.\n"
        "⭐ Бали: від 4 до 14.\n"
        "📝 Остання частина — назва справи.\n\n"

        "⚖️ Якщо сфер кілька, XP буде поділено між ними.",

        parse_mode="HTML",
        reply_markup=markup
    )

    bot.register_next_step_handler(
        msg,
        process_unplanned
    )


def process_unplanned(message):

    if message.text == "🔙 Назад":
        start_complete(message)
        return

    try:

        parts = [
            part.strip()
            for part in message.text.split(";")
        ]

        if len(parts) != 3:

            raise ValueError(
                "Потрібно вказати 3 частини через «;»."
            )

        spheres_text, xp_text, title = parts

        # -------------------------------------------------
        # СФЕРИ
        # -------------------------------------------------

        spheres = []

        for emoji in spheres_text:

            if emoji in SPHERE_NAMES.values():
                spheres.append(emoji)

        if not spheres:

            raise ValueError(
                "Не знайдено жодної правильної сфери."
            )

        if len(spheres) != len(set(spheres)):

            raise ValueError(
                "Одна сфера вказана двічі."
            )

        # -------------------------------------------------
        # XP
        # -------------------------------------------------

        try:
            xp = int(xp_text)

        except ValueError:

            raise ValueError(
                "Кількість балів має бути числом."
            )

        if xp < 4 or xp > 14:

            raise ValueError(
                "Кількість балів має бути від 4 до 14."
            )

        # -------------------------------------------------
        # НАЗВА
        # -------------------------------------------------

        if len(title) < 3:

            raise ValueError(
                "Назва справи занадто коротка."
            )

        # -------------------------------------------------
        # XP
        # -------------------------------------------------

        user_id = str(message.from_user.id)

        player = get_player(user_id)

        add_total_xp(
            player,
            float(xp)
        )

        add_xp_to_spheres(
            player,
            spheres,
            float(xp)
        )

        update_player(
            user_id,
            {
                "xp_total": player["xp_total"],
                "spheres": player["spheres"]
            }
        )

        bot.send_message(
            message.chat.id,

            "🦇 <b>Марчелло схвально киває.</b>\n\n"

            "✨ Справу зараховано!\n\n"

            f"📝 <b>{title}</b>\n"
            f"⭐ Отримано: <b>{xp} XP</b>\n"
            f"🎯 Сфери: {' '.join(spheres)}\n\n"

            "«Бачиш? Навіть те, чого не було в планах, "
            "може стати частиною твоєї хроніки.»",

            parse_mode="HTML",
            reply_markup=build_back_button()
        )

    except ValueError as error:

        markup = build_back_button()

        bot.send_message(
            message.chat.id,

            "🦇 <b>Марчелло постукує пером по столу.</b>\n\n"

            f"❌ {error}\n\n"

            "Спробуй ще раз:\n\n"

            "<code>💪🧠 ; 10 ; Назва справи</code>",

            parse_mode="HTML",
            reply_markup=markup
        )

        bot.register_next_step_handler(
            message,
            process_unplanned
        )
