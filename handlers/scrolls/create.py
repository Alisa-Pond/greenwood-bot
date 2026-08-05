import re
from datetime import datetime
from zoneinfo import ZoneInfo

from telebot import types

from services.config import bot
from services.database import get_player, update_player
from services.utils import clean_skin_tones
from keyboards import get_scrolls_menu


KYIV = ZoneInfo("Europe/Kyiv")


def validate_deadline(date_text):
    """
    Перевіряє дату дедлайну.
    Формат: ДД.ММ.РРРР
    """

    try:
        deadline = datetime.strptime(
            date_text,
            "%d.%m.%Y"
        ).replace(tzinfo=KYIV)

        today = datetime.now(KYIV).replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0
        )

        if deadline < today:
            return False

        return True

    except ValueError:
        return False



@bot.message_handler(
    func=lambda message: message.text == "➕ Створити сувой"
)
def create_scroll_start(message):

    guide = (
        "🦇 <b>Марчелло:</b>\n"
        "«Новий сувій готовий бути записаним у хроніки.\n"
        "Але пам'ятай: кожен контракт має наслідки.»\n\n"

        "📖 Запиши його одним рядком:\n\n"

        "<code>"
        "[Емодзі] [Кратність] [XP] [ДД.ММ.РРРР] [Опис]"
        "</code>\n\n"

        "Приклад:\n"
        "<code>"
        "💪 3 10 20.08.2026 "
        "Пробіжка 5 км"
        "</code>\n\n"

        "Правила:\n"
        "• XP за крок: 4-14\n"
        "• Дедлайн не може бути у минулому\n"
        "• Виконані сувої залишаться у хроніках\n\n"

        "Напиши 🔙 Назад до квестів для скасування."
    )


    msg = bot.send_message(
        message.chat.id,
        guide,
        parse_mode="HTML",
        reply_markup=types.ForceReply(selective=True)
    )

    bot.register_next_step_handler(
        msg,
        process_create_scroll
    )



def process_create_scroll(message):

    user_id = str(message.from_user.id)

    text = (
        message.text.strip()
        if message.text
        else ""
    )


    if text == "🔙 Назад до квестів":

        bot.send_message(
            message.chat.id,
            "🦇 Марчелло: «Запис сувою скасовано.»",
            reply_markup=get_scrolls_menu()
        )

        return



    text = clean_skin_tones(text)



    match = re.match(
        r"^([^\w\s]+)\s+(\d+)\s+(\d+)\s+(\d{2}\.\d{2}\.\d{4})\s+(.+)$",
        text
    )



    if not match:

        msg = bot.send_message(
            message.chat.id,
            (
                "🦇 <b>Марчелло:</b>\n"
                "«Чорнило розмазалось. Формат неправильний.\n\n"
                "Спробуй так:\n"
                "<code>"
                "💪 3 10 20.08.2026 Пробіжка"
                "</code>"
            ),
            parse_mode="HTML"
        )

        bot.register_next_step_handler(
            msg,
            process_create_scroll
        )

        return



    emoji, max_count, xp, deadline, task = match.groups()



    max_count = int(max_count)
    xp = int(xp)



    if xp < 4 or xp > 14:

        msg = bot.send_message(
            message.chat.id,
            (
                "🦇 Марчелло:\n"
                "«Сила одного кроку має бути від 4 до 14 XP.»"
            )
        )

        bot.register_next_step_handler(
            msg,
            process_create_scroll
        )

        return



    if not validate_deadline(deadline):

        msg = bot.send_message(
            message.chat.id,
            (
                "🦇 Марчелло:\n"
                "«Цей день уже залишився позаду.\n"
                "Сувій не може вести у минуле.»"
            )
        )

        bot.register_next_step_handler(
            msg,
            process_create_scroll
        )

        return



    player = get_player(user_id)


    quests = player.setdefault(
        "quests",
        {}
    )

    scrolls = quests.setdefault(
        "scrolls",
        []
    )



    exists = any(
        s.get("task","").lower() == task.lower()
        and s.get("status","active") == "active"
        for s in scrolls
    )


    if exists:

        bot.send_message(
            message.chat.id,
            (
                "🦇 Марчелло:\n"
                "«Такий сувій уже лежить на столі.»"
            )
        )

        return



    new_scroll = {

        "emoji": emoji,

        "task": task.strip(),

        "max_count": max_count,

        "done_count": 0,

        "xp_per_once": xp,

        "deadline": deadline,

        "status": "active",

        "created_at": datetime.now(KYIV).strftime(
            "%d.%m.%Y"
        ),

        "penalty_applied": False
    }



    scrolls.append(
        new_scroll
    )


    update_player(
        user_id,
        player
    )



    bot.send_message(
        message.chat.id,

        (
            "🦇 <b>Марчелло:</b>\n"
            "«Новий контракт запечатано.»\n\n"

            f"{emoji} <b>{task}</b>\n"
            f"Повторень: {max_count}\n"
            f"Нагорода: {xp} XP\n"
            f"До: {deadline}"
        ),

        parse_mode="HTML",

        reply_markup=get_scrolls_menu()
    )
