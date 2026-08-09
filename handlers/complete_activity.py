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


def get_sphere_emoji(sphere):
    """
    Перетворює назву сфери або її emoji
    на emoji для відображення.
    """

    if sphere in SPHERE_NAMES:
        return SPHERE_NAMES[sphere]

    if sphere in SPHERE_NAMES.values():
        return sphere

    return sphere


# =========================================================
# ДОПОМІЖНІ ФУНКЦІЇ
# =========================================================

def get_spheres(item):
    """
    Отримує список сфер із сувою / ритуалу / рослини.

    Підтримує кілька можливих форматів,
    щоб не ламати вже створені записи.
    """

    spheres = item.get("spheres")

    if not spheres:
        spheres = item.get("sphere")

    if not spheres:
        return []

    if isinstance(spheres, str):

        result = []

        for sphere_key, emoji in SPHERE_NAMES.items():

            if emoji in spheres:
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
    """
    Отримує назву справи.
    """

    return (
        item.get("title")
        or item.get("name")
        or item.get("task")
        or "Без назви"
    )


def get_xp(item):
    """
    Отримує кількість XP.
    """

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
    """
    Повертає сьогоднішню дату.
    """

    return datetime.now().strftime("%d.%m.%Y")


# =========================================================
# XP СФЕР
# =========================================================

def add_xp_to_spheres(player, spheres, total_xp):
    """
    Розподіляє XP між сферами.

    1 сфера:
        10 XP → 10 XP

    2 сфери:
        10 XP → 5 + 5 XP

    3 сфери:
        12 XP → 4 + 4 + 4 XP
    """

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

        player_spheres[sphere_key]["xp"] = (
            float(
                player_spheres[sphere_key].get("xp", 0)
            )
            + share
        )

        # Підвищення рівня
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
    """
    Додає XP до загального досвіду персонажа.
    """

    player["xp_total"] = (
        float(player.get("xp_total", 0))
        + xp
    )


# =========================================================
# КНОПКА НАЗАД
# =========================================================

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
        "🔄 <b>Ритуал</b> — справа, що повертається за своїм розкладом.\n"
        "🌱 <b>Рослина</b> — велика ціль, яку ти виростила до кінця.\n"
        "✨ <b>Поза планом</b> — щось корисне, чого взагалі не було в планах.\n\n"

        "🦇 <b>Марчелло</b> уже тримає перо над книгою XP. "
        "Не змушуй його чекати.",

        parse_mode="HTML",
        reply_markup=markup
    )


# =========================================================
# ВИБІР СУВОЮ
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
            "Схоже, Марчелло вже не має чим тебе завантажити. "
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

        "📜 <b>Обери сувій, який запечатати виконаним:</b>",

        parse_mode="HTML",
        reply_markup=markup
    )

    bot.register_next_step_handler(
        msg,
        complete_scroll
    )


# =========================================================
# ВИКОНАННЯ СУВОЮ
# =========================================================

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
                message.text
                .split(".")[0]
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
            "Я не знайшов такого сувою в реєстрі. "
            "Обери його кнопкою нижче.",

            parse_mode="HTML"
        )

        choose_scroll(message)
        return

    scroll = scrolls[selected_index]

    title = get_title(scroll)
    xp = get_xp(scroll)
    spheres = get_spheres(scroll)

    # =====================================================
    # НАРАХУВАННЯ XP
    # =====================================================

    add_total_xp(player, xp)

    add_xp_to_spheres(
        player,
        spheres,
        xp
    )

    # =====================================================
    # АРХІВ СУВОЇВ
    # =====================================================

    scroll_archive = (
        player.get("scroll_archive")
        or []
    )

    completed_scroll = dict(scroll)

    completed_scroll["completed_date"] = get_today()

    scroll_archive.append(
        completed_scroll
    )

    # =====================================================
    # ВИДАЛЯЄМО З АКТИВНИХ
    # =====================================================

    scrolls.pop(selected_index)

    player["scrolls"] = scrolls

    player["scroll_archive"] = scroll_archive

    # =====================================================
    # ЗБЕРІГАЄМО
    # =====================================================

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
        f"⭐ Отримано: <b>{xp:.1f} XP</b>\n\n"

        f"🎯 Сфери: "
        f"{' '.join(get_sphere_emoji(s) for s in spheres)}\n\n"

        "✨ Сувій виконано й відправлено до "
        "<b>Архіву Грінвуду</b>.",

        parse_mode="HTML",
        reply_markup=build_back_button()
    )


# =========================================================
# ВИБІР РИТУАЛУ
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

            weekday_names = [
                "пн",
                "вт",
                "ср",
                "чт",
                "пт",
                "сб",
                "нд"
            ]

            if today < len(weekday_names):

                if weekday_names[today] in days:

                    is_today = True

        if is_today:

            available.append(
                (index, ritual)
            )

    if not available:

        bot.send_message(
            message.chat.id,

            "💤 <b>Сьогодні жоден ритуал не чекає "
            "на виконання.</b>\n\n"
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


# =========================================================
# ВИКОНАННЯ РИТУАЛУ
# =========================================================

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
                message.text
                .split(".")[0]
                .replace("🔄", "")
                .strip()
            )
            - 1
        )

    except (ValueError, IndexError):

        pass

    if selected_index is None:

        bot.send_message(
            message.chat.id,
            "🔄 Не вдалося знайти цей ритуал. "
            "Спробуй обрати його кнопкою."
        )

        choose_ritual(message)
        return

    if (
        selected_index < 0
        or selected_index >= len(rituals)
    ):

        choose_ritual(message)
        return

    ritual = rituals[selected_index]

    title = get_title(ritual)
    xp = get_xp(ritual)
    spheres = get_spheres(ritual)

    # =====================================================
    # ПЕРЕВІРКА ПОВТОРНОГО ВИКОНАННЯ
    # =====================================================

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

    # =====================================================
    # XP
    # =====================================================

    add_total_xp(player, xp)

    add_xp_to_spheres(
        player,
        spheres,
        xp
    )

    # =====================================================
    # ЗАПИС В АРХІВ РИТУАЛІВ
    # =====================================================

    ritual_archive = (
        player.get("ritual_archive")
        or []
    )

    completed_ritual = dict(ritual)

    completed_ritual["completed_date"] = today

    ritual_archive.append(
        completed_ritual
    )

    # =====================================================
    # ПОЗНАЧАЄМО РИТУАЛ ВИКОНАНИМ СЬОГОДНІ
    # =====================================================

    ritual["last_completed"] = today

    rituals[selected_index] = ritual

    player["rituals"] = rituals

    player["ritual_archive"] = ritual_archive

    # =====================================================
    # ЗБЕРІГАЄМО
    # =====================================================

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
        f"⭐ Отримано: <b>{xp:.1f} XP</b>\n\n"

        f"🎯 Сфери: "
        f"{' '.join(get_sphere_emoji(s) for s in spheres)}\n\n"

        "🕯️ Запис про виконання збережено в "
        "<b>Архіві ритуалів</b>.\n\n"

        "Полум'я ритуалу згасло до наступного "
        "призначеного дня.",

        parse_mode="HTML",
        reply_markup=build_back_button()
    )


# =========================================================
# ВИБІР РОСЛИНИ
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


# =========================================================
# ВИКОНАННЯ РОСЛИНИ
# =========================================================

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
                message.text
                .split(".")[0]
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

    # =====================================================
    # XP
    # =====================================================

    add_total_xp(player, xp)

    add_xp_to_spheres(
        player,
        spheres,
        xp
    )

    # =====================================================
    # АРХІВ РОСЛИН
    # =====================================================

    archive = (
        player.get("plant_archive")
        or []
    )

    completed_plant = dict(plant)

    completed_plant["completed_date"] = get_today()

    archive.append(
        completed_plant
    )

    # =====================================================
    # ВИДАЛЯЄМО З АКТИВНИХ
    # =====================================================

    plants.pop(selected_index)

    player["plants"] = plants

    player["plant_archive"] = archive

    # =====================================================
    # ЗБЕРІГАЄМО
    # =====================================================

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

        "🌿 Рослину переміщено до Архіву теплиці.\n"
        "Тепер вона там, де мають лежати речі, "
        "якими справді можна пишатися.",

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

        "Якщо ти зробила щось поза планом, "
        "це теж заслуговує на XP.\n\n"

        "Запиши справу у форматі:\n\n"

        "<code>💪🧠 ; 10 ; Вивчити нову тему</code>\n\n"

        "або:\n\n"

        "<code>🎨 ; 6 ; Намалювати картину</code>\n\n"

        "🎯 Можна вказати кілька сфер.\n"
        "⭐ Бали: від 4 до 14.\n"
        "📝 Остання частина — назва справи.\n\n"

        "⚖️ Якщо сфер кілька, XP буде поділено між ними.\n\n"

        "🔙 Якщо передумала — натисни «Назад».",

        parse_mode="HTML",
        reply_markup=markup
    )

    bot.register_next_step_handler(
        msg,
        process_unplanned
    )


# =========================================================
# ОБРОБКА НЕЗАПЛАНОВАНОЇ СПРАВИ
# =========================================================

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

        # -------------------------
        # Сфери
        # -------------------------

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

        # -------------------------
        # XP
        # -------------------------

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

        # -------------------------
        # Назва
        # -------------------------

        if len(title) < 3:

            raise ValueError(
                "Назва справи занадто коротка."
            )

        # -------------------------
        # Нарахування
        # -------------------------

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
