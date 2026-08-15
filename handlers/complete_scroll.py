from telebot import types

from services.config import bot
from services.database import get_player, update_player

from services.activity_utils import (
    get_title,
    get_xp,
    get_spheres,
    get_today,
    is_overdue,
    add_total_xp,
    add_xp_to_spheres,
    update_statistics,
    build_back_button,
)

from services.activity_loot import try_activity_loot


# =========================================================
# ВИБІР СУВОЮ
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
            reply_markup=build_back_button(),
        )

        return

    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    for index, scroll in enumerate(scrolls):

        overdue = "⚠️ " if is_overdue(scroll) else ""

        markup.row(
            types.KeyboardButton(
                f"📜 {overdue}{index + 1}. "
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
        reply_markup=markup,
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

        from handlers.complete_activity import start_complete

        start_complete(message)

        return

    user_id = str(message.from_user.id)

    player = get_player(user_id)

    scrolls = player.get("scrolls") or []

    # -----------------------------------------------------
    # ВИЗНАЧАЄМО НОМЕР СУВОЮ
    # -----------------------------------------------------

    try:

        number = int(
            message.text
            .split(".")[0]
            .replace("📜", "")
            .replace("⚠️", "")
            .strip()
        )

        selected_index = number - 1

    except (ValueError, IndexError):

        selected_index = None

    # -----------------------------------------------------
    # ПЕРЕВІРКА ВИБОРУ
    # -----------------------------------------------------

    if (
        selected_index is None
        or not 0 <= selected_index < len(scrolls)
    ):

        bot.send_message(
            message.chat.id,

            "🦇 Не вдалося знайти цей сувій."
        )

        choose_scroll(message)

        return

    # -----------------------------------------------------
    # ОТРИМУЄМО СУВІЙ
    # -----------------------------------------------------

    scroll = scrolls[selected_index]

    title = get_title(scroll)

    xp = get_xp(scroll)

    spheres = get_spheres(scroll)

    overdue = is_overdue(scroll)

    # -----------------------------------------------------
    # XP
    # -----------------------------------------------------
    #
    # Штраф за прострочення має списуватися
    # окремо через summary.py.
    #
    # Під час виконання сувою користувач
    # отримує повний XP, прописаний у сувої.
    #

    add_total_xp(
        player,
        xp
    )

    add_xp_to_spheres(
        player,
        spheres,
        xp
    )

    # -----------------------------------------------------
    # ЛУТ
    # -----------------------------------------------------

    loot = try_activity_loot(
        player
    )

    # -----------------------------------------------------
    # АРХІВ
    # -----------------------------------------------------

    scroll_archive = (
        player.get("scroll_archive") or []
    )

    completed_scroll = dict(
        scroll
    )

    completed_scroll["completed"] = True

    completed_scroll["completed_date"] = (
        get_today()
    )

    scroll_archive.append(
        completed_scroll
    )

    # -----------------------------------------------------
    # ВИДАЛЯЄМО З АКТИВНИХ
    # -----------------------------------------------------

    scrolls.pop(
        selected_index
    )

    player["scrolls"] = scrolls

    player["scroll_archive"] = (
        scroll_archive
    )

    # -----------------------------------------------------
    # СТАТИСТИКА
    # -----------------------------------------------------

    update_statistics(
        player,
        completed_scrolls=1
    )

    # -----------------------------------------------------
    # ЗБЕРІГАЄМО В SUPABASE
    # -----------------------------------------------------

    update_player(
        user_id,
        {
            "xp_total": player["xp_total"],
            "spheres": player["spheres"],
            "scrolls": player["scrolls"],
            "scroll_archive": player["scroll_archive"],
            "statistics": player["statistics"],
            "inventory": player.get(
                "inventory"
            ) or [],
        }
    )

    # -----------------------------------------------------
    # ПОВІДОМЛЕННЯ
    # -----------------------------------------------------

    loot_text = ""

    if loot:

        loot_text = (
            f"\n🎁 Знайдено: "
            f"<b>{loot}</b>"
        )

    overdue_text = ""

    if overdue:

        overdue_text = (
            "\n⚠️ Сувій був прострочений, "
            "але повна нагорода за виконання повернута."
        )

    spheres_text = " ".join(
        spheres
    )

    bot.send_message(
        message.chat.id,

        "🦇 <b>Марчелло ставить останню печатку.</b>\n\n"

        f"📜 <b>{title}</b>\n"
        f"⭐ Отримано: <b>{xp:.1f} XP</b>\n"
        f"🎯 Сфери: {spheres_text}"

        f"{overdue_text}"

        f"{loot_text}\n\n"

        "✨ Сувій виконано й відправлено "
        "до <b>Архіву Грінвуду</b>.",

        parse_mode="HTML",

        reply_markup=build_back_button(),
    )
