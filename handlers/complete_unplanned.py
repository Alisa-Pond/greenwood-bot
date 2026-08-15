from telebot import types

from services.config import bot
from services.database import get_player, update_player

from services.activity_utils import (
    SPHERE_NAMES,
    add_total_xp,
    add_xp_to_spheres,
    build_back_button,
)

from services.activity_loot import try_activity_loot


# =========================================================
# ПОЗАПЛАНОВА СПРАВА
# =========================================================

@bot.message_handler(
    func=lambda message:
        message.text == "✨ Зробити поза планом"
)
def start_unplanned(message):

    msg = bot.send_message(
        message.chat.id,

        "🦇 <b>Марчелло відкладає перо.</b>\n\n"

        "«Не все корисне в житті "
        "народжується в календарі.»\n\n"

        "Запиши справу у форматі:\n\n"

        "<code>💪🧠 ; 10 ; Вивчити нову тему</code>\n\n"

        "або:\n\n"

        "<code>🎨 ; 6 ; Намалювати картину</code>\n\n"

        "🎯 Можна вказати кілька сфер.\n"
        "⭐ Бали: від 4 до 14.\n"
        "📝 Остання частина — назва справи.\n\n"

        "⚖️ Якщо сфер кілька, XP буде "
        "поділено між ними.",

        parse_mode="HTML",

        reply_markup=build_back_button(),
    )

    bot.register_next_step_handler(
        msg,
        process_unplanned
    )


# =========================================================
# ОБРОБКА ПОЗАПЛАНОВОЇ СПРАВИ
# =========================================================

def process_unplanned(message):

    if message.text == "🔙 Назад":

        from handlers.complete_activity import start_complete

        start_complete(message)

        return

    try:

        # -------------------------------------------------
        # РОЗБИВАЄМО РЯДОК
        # -------------------------------------------------

        parts = [
            part.strip()
            for part in message.text.split(";")
        ]

        if len(parts) != 3:

            raise ValueError(
                "Потрібно вказати 3 частини "
                "через «;»."
            )

        spheres_text, xp_text, title = parts

        # -------------------------------------------------
        # СФЕРИ
        # -------------------------------------------------

        spheres = []

        for emoji in spheres_text:

            if emoji in SPHERE_NAMES.values():

                spheres.append(
                    emoji
                )

        if not spheres:

            raise ValueError(
                "Не знайдено жодної "
                "правильної сфери."
            )

        if len(spheres) != len(
            set(spheres)
        ):

            raise ValueError(
                "Одна сфера вказана двічі."
            )

        # -------------------------------------------------
        # XP
        # -------------------------------------------------

        try:

            xp = int(
                xp_text
            )

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
        # ГРАВЕЦЬ
        # -------------------------------------------------

        user_id = str(
            message.from_user.id
        )

        player = get_player(
            user_id
        )

        # -------------------------------------------------
        # XP
        # -------------------------------------------------

        add_total_xp(
            player,
            float(xp)
        )

        add_xp_to_spheres(
            player,
            spheres,
            float(xp)
        )

        # -------------------------------------------------
        # ЛУТ
        # -------------------------------------------------

        loot = try_activity_loot(
            player
        )

        # -------------------------------------------------
        # SUPABASE
        # -------------------------------------------------

        update_player(
            user_id,
            {
                "xp_total": player[
                    "xp_total"
                ],
                "spheres": player[
                    "spheres"
                ],
                "inventory": player.get(
                    "inventory"
                ) or [],
            }
        )

        # -------------------------------------------------
        # ПОВІДОМЛЕННЯ
        # -------------------------------------------------

        loot_text = ""

        if loot:

            loot_text = (
                f"\n🎁 Знайдено: "
                f"<b>{loot}</b>"
            )

        spheres_text = " ".join(
            spheres
        )

        bot.send_message(
            message.chat.id,

            "🦇 <b>Марчелло схвально киває.</b>\n\n"

            "✨ Справу зараховано!\n\n"

            f"📝 <b>{title}</b>\n"
            f"⭐ Отримано: <b>{xp} XP</b>\n"
            f"🎯 Сфери: {spheres_text}"

            f"{loot_text}",

            parse_mode="HTML",

            reply_markup=build_back_button(),
        )

    except ValueError as error:

        # -------------------------------------------------
        # ПОМИЛКА ФОРМАТУ
        # -------------------------------------------------

        bot.send_message(
            message.chat.id,

            "🦇 <b>Марчелло постукує "
            "пером по столу.</b>\n\n"

            f"❌ {error}\n\n"

            "Спробуй ще раз:\n\n"

            "<code>💪🧠 ; 10 ; Назва справи</code>",

            parse_mode="HTML",

            reply_markup=build_back_button(),
        )

        bot.register_next_step_handler(
            message,
            process_unplanned
        )
