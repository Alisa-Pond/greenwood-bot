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

                result.append(
                    get_sphere_emoji(sphere)
                )

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
# ДАТА ДЕДЛАЙНУ
# =========================================================

def parse_deadline(deadline):
    """
    Перетворює дедлайн DD.MM.YY або DD.MM.YYYY
    у datetime.
    """

    if not deadline:
        return None

    try:

        return datetime.strptime(
            str(deadline),
            "%d.%m.%y"
        )

    except ValueError:

        try:

            return datetime.strptime(
                str(deadline),
                "%d.%m.%Y"
            )

        except ValueError:

            return None


def is_overdue(item):
    """
    Перевіряє, чи прострочена справа.
    """

    deadline = parse_deadline(
        item.get("deadline")
    )

    if not deadline:
        return False

    today = datetime.now().replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0
    )

    return today > deadline


# =========================================================
# ШТРАФ ЗА ПРОСТРОЧЕННЯ
# =========================================================

def get_penalty_xp(item):
    """
    Отримує штраф за прострочення.

    Підтримує:
        penalty
        penalty_xp
        overdue_penalty
    """

    possible_fields = [
        "penalty",
        "penalty_xp",
        "overdue_penalty"
    ]

    for field in possible_fields:

        value = item.get(field)

        if value is not None:

            try:
                return abs(float(value))

            except (TypeError, ValueError):
                pass

    return 0.0


def calculate_plant_reward(plant):
    """
    Розраховує фактичну нагороду рослини.

    Якщо рослина виконана до дедлайну:
        повний XP.

    Якщо після дедлайну:
        XP мінус штраф.

    Нагорода не може бути меншою за 0.
    """

    base_xp = get_xp(plant)

    if not is_overdue(plant):
        return base_xp, 0.0

    penalty = get_penalty_xp(plant)

    final_xp = max(
        0.0,
        base_xp - penalty
    )

    return final_xp, penalty


# =========================================================
# XP СФЕР
# =========================================================

def add_xp_to_spheres(player, spheres, total_xp):
    """
    Розподіляє XP між сферами.
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
                player_spheres[sphere_key].get(
                    "xp",
                    0
                )
            )
            + share
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
    """
    Додає XP до загального досвіду персонажа.
    """

    player["xp_total"] = (
        float(player.get("xp_total", 0))
        + xp
    )


# =========================================================
# СТАТИСТИКА
# =========================================================

def update_statistics(
    player,
    completed_scrolls=0,
    completed_rituals=0,
    plants_harvested=0,
    expeditions_completed=0
):
    """
    Оновлює statistics.

    Використовуються тільки поля:

        completed_scrolls
        completed_rituals
        plants_harvested
        expeditions_completed
        last_summary_date

    completed_history НЕ використовується.
    """

    statistics = player.get("statistics") or {}

    statistics["completed_scrolls"] = (
        int(
            statistics.get(
                "completed_scrolls",
                0
            )
        )
        + completed_scrolls
    )

    statistics["completed_rituals"] = (
        int(
            statistics.get(
                "completed_rituals",
                0
            )
        )
        + completed_rituals
    )

    statistics["plants_harvested"] = (
        int(
            statistics.get(
                "plants_harvested",
                0
            )
        )
        + plants_harvested
    )

    statistics["expeditions_completed"] = (
        int(
            statistics.get(
                "expeditions_completed",
                0
            )
        )
        + expeditions_completed
    )

    if "last_summary_date" not in statistics:
        statistics["last_summary_date"] = None

    player["statistics"] = statistics


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
    func=lambda message:
        message.text == "✅ Виконати справу"
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
    func=lambda message:
        message.text == "📜 Виконати сувій"
)
def choose_scroll(message):

    user_id = str(message.from_user.id)

    player = get_player(user_id)

    scrolls = player.get("scrolls") or []

    if not scrolls:

        bot.send_message(
            message.chat.id,

            "📜 <b>Жодного активного сувою.</b>\n\n"
            "Марчелло поки не має чим тебе завантажити. 🦇",

            parse_mode="HTML",
            reply_markup=build_back_button()
        )

        return

    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    for index, scroll in enumerate(scrolls):

        markup.row(
            types.KeyboardButton(
                f"📜 {index + 1}. "
                f"{get_title(scroll)}"
            )
        )

    markup.row(
        types.KeyboardButton("🔙 Назад")
    )

    msg = bot.send_message(
        message.chat.id,

        "📜 <b>Обери сувій:</b>",

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
            "🦇 Не вдалося знайти цей сувій."
        )

        choose_scroll(message)
        return

    scroll = scrolls[selected_index]

    title = get_title(scroll)
    xp = get_xp(scroll)
    spheres = get_spheres(scroll)

    add_total_xp(
        player,
        xp
    )

    add_xp_to_spheres(
        player,
        spheres,
        xp
    )

    scroll_archive = (
        player.get("scroll_archive") or []
    )

    completed_scroll = dict(scroll)

    completed_scroll["completed"] = True
    completed_scroll["completed_date"] = get_today()

    scroll_archive.append(
        completed_scroll
    )

    scrolls.pop(selected_index)

    player["scrolls"] = scrolls
    player["scroll_archive"] = scroll_archive

    update_statistics(
        player,
        completed_scrolls=1
    )

    update_player(
        user_id,
        {
            "xp_total": player["xp_total"],
            "spheres": player["spheres"],
            "scrolls": player["scrolls"],
            "scroll_archive": player["scroll_archive"],
            "statistics": player["statistics"]
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
# РИТУАЛИ
# =========================================================

@bot.message_handler(
    func=lambda message:
        message.text == "🔄 Провести ритуал"
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

    today_weekday = datetime.now().weekday()

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

        elif today_weekday in days:

            is_today = True

        elif isinstance(days, list):

            if weekday_names[today_weekday] in days:

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

        markup.row(
            types.KeyboardButton(
                f"🔄 {index + 1}. "
                f"{get_title(ritual)}"
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
        complete_ritual
    )


def complete_ritual(message):

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

    if (
        selected_index is None
        or selected_index < 0
        or selected_index >= len(rituals)
    ):

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

            "🌙 <b>Цей ритуал уже виконано сьогодні.</b>",

            parse_mode="HTML",
            reply_markup=build_back_button()
        )

        return

    add_total_xp(
        player,
        xp
    )

    add_xp_to_spheres(
        player,
        spheres,
        xp
    )

    ritual_archive = (
        player.get("ritual_archive") or []
    )

    completed_ritual = dict(ritual)

    completed_ritual["completed_date"] = today

    ritual_archive.append(
        completed_ritual
    )

    ritual["last_completed"] = today

    rituals[selected_index] = ritual

    player["rituals"] = rituals
    player["ritual_archive"] = ritual_archive

    update_statistics(
        player,
        completed_rituals=1
    )

    update_player(
        user_id,
        {
            "xp_total": player["xp_total"],
            "spheres": player["spheres"],
            "rituals": player["rituals"],
            "ritual_archive": player["ritual_archive"],
            "statistics": player["statistics"]
        }
    )

    bot.send_message(
        message.chat.id,

        "🔥 <b>Ритуал проведено!</b>\n\n"

        f"🔄 <b>{title}</b>\n"
        f"⭐ Отримано: <b>{xp:.1f} XP</b>\n\n"

        f"🎯 Сфери: "
        f"{' '.join(get_sphere_emoji(s) for s in spheres)}\n\n"

        "🕯️ Запис збережено в "
        "<b>Архіві ритуалів</b>.",

        parse_mode="HTML",
        reply_markup=build_back_button()
    )


# =========================================================
# РОСЛИНИ
# =========================================================

@bot.message_handler(
    func=lambda message:
        message.text == "🌱 Завершити вирощування"
)
def choose_plant(message):

    user_id = str(message.from_user.id)

    player = get_player(user_id)

    plants = player.get("plants") or []

    if not plants:

        bot.send_message(
            message.chat.id,

            "🌱 <b>У теплиці немає рослин.</b>\n\n"
            "Олівер дивиться на порожній ґрунт. 🌿",

            parse_mode="HTML",
            reply_markup=build_back_button()
        )

        return

    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    for index, plant in enumerate(plants):

        markup.row(
            types.KeyboardButton(
                f"🌱 {index + 1}. "
                f"{get_title(plant)}"
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

        choose_plant(message)
        return

    plant = plants[selected_index]

    title = get_title(plant)
    spheres = get_spheres(plant)

    base_xp = get_xp(plant)

    final_xp, penalty = calculate_plant_reward(
        plant
    )

    add_total_xp(
        player,
        final_xp
    )

    add_xp_to_spheres(
        player,
        spheres,
        final_xp
    )

    plant_archive = (
        player.get("plant_archive") or []
    )

    completed_plant = dict(plant)

    completed_plant["completed_date"] = get_today()
    completed_plant["earned_xp"] = final_xp

    if penalty > 0:

        completed_plant["penalty_applied"] = penalty

    plant_archive.append(
        completed_plant
    )

    plants.pop(selected_index)

    player["plants"] = plants
    player["plant_archive"] = plant_archive

    update_statistics(
        player,
        plants_harvested=1
    )

    update_player(
        user_id,
        {
            "xp_total": player["xp_total"],
            "spheres": player["spheres"],
            "plants": player["plants"],
            "plant_archive": player["plant_archive"],
            "statistics": player["statistics"]
        }
    )

    reward = plant.get(
        "reward",
        "твоя нагорода"
    )

    if penalty > 0:

        xp_message = (
            f"⭐ Базова нагорода: <b>{base_xp:.1f} XP</b>\n"
            f"⚠️ Штраф за прострочення: "
            f"<b>-{penalty:.1f} XP</b>\n"
            f"✨ Отримано: <b>{final_xp:.1f} XP</b>"
        )

    else:

        xp_message = (
            f"⭐ Отримано: <b>{final_xp:.1f} XP</b>"
        )

    bot.send_message(
        message.chat.id,

        "🌳 <b>Олівер оглядає вирощену рослину.</b>\n\n"

        f"🌱 <b>{title}</b>\n\n"

        f"{xp_message}\n"
        f"🎁 Нагорода: <b>{reward}</b>\n\n"

        "🌿 Рослину переміщено до "
        "<b>Архіву теплиці</b>.",

        parse_mode="HTML",
        reply_markup=build_back_button()
    )


# =========================================================
# НЕЗАПЛАНОВАНА СПРАВА
# =========================================================

@bot.message_handler(
    func=lambda message:
        message.text == "✨ Зробити поза планом"
)
def start_unplanned(message):

    markup = build_back_button()

    msg = bot.send_message(
        message.chat.id,

        "🦇 <b>Марчелло відкладає перо.</b>\n\n"

        "«Не все корисне в житті народжується "
        "в календарі.»\n\n"

        "Запиши справу у форматі:\n\n"

        "<code>💪🧠 ; 10 ; Вивчити нову тему</code>\n\n"

        "або:\n\n"

        "<code>🎨 ; 6 ; Намалювати картину</code>\n\n"

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

        if len(title) < 3:

            raise ValueError(
                "Назва справи занадто коротка."
            )

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
            f"🎯 Сфери: {' '.join(spheres)}",

            parse_mode="HTML",
            reply_markup=build_back_button()
        )

    except ValueError as error:

        bot.send_message(
            message.chat.id,

            "🦇 <b>Марчелло постукує пером по столу.</b>\n\n"

            f"❌ {error}\n\n"

            "Спробуй ще раз:\n\n"

            "<code>💪🧠 ; 10 ; Назва справи</code>",

            parse_mode="HTML",
            reply_markup=build_back_button()
        )

        bot.register_next_step_handler(
            message,
            process_unplanned
        )
