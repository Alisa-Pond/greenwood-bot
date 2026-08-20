from datetime import datetime

from services.config import bot
from services.database import get_player

from keyboards import (
    get_quests_menu,
    get_scrolls_menu,
)

from services.activity_utils import (
    get_title,
    get_xp,
    get_spheres,
    parse_deadline,
)


print("⚙️ Реєструємо меню сувоїв...")


# =========================================================
# ДНІ ТИЖНЯ
# =========================================================

WEEKDAYS = [
    "пн",
    "вт",
    "ср",
    "чт",
    "пт",
    "сб",
    "нд",
]


# =========================================================
# ПОТОЧНА ДАТА
# =========================================================

def get_today_text():

    today = datetime.now()

    weekday = WEEKDAYS[
        today.weekday()
    ]

    return (
        f"{today.strftime('%d.%m.%Y')}, "
        f"{weekday}"
    )


# =========================================================
# ПЕРЕВІРКА: ДЕДЛАЙН СЬОГОДНІ
# =========================================================

def deadline_is_today(scroll):

    deadline = scroll.get(
        "deadline"
    )

    if not deadline:
        return False

    deadline_date = parse_deadline(
        deadline
    )

    if not deadline_date:
        return False

    return (
        deadline_date.date()
        == datetime.now().date()
    )


# =========================================================
# ФОРМАТУВАННЯ СУВОЮ
# =========================================================

def format_scroll(scroll):

    title = get_title(
        scroll
    )

    xp = get_xp(
        scroll
    )

    spheres = get_spheres(
        scroll
    )

    spheres_text = "".join(
        spheres
    )

    deadline = (
        scroll.get(
            "deadline"
        )
        or "без дедлайну"
    )

    fire = (
        "🔥 "
        if deadline_is_today(scroll)
        else ""
    )

    return (
        f"{fire}"
        f"{spheres_text} "
        f"<b>{title}</b> "
        f"({xp:.1f} XP)\n"
        f"    └── 📅 Дедлайн: "
        f"{deadline}"
    )


# =========================================================
# 📜 СУВОЇ
# =========================================================

@bot.message_handler(
    func=lambda message:
        message.text == "📜 Сувої"
)
def open_scrolls(message):

    user_id = str(
        message.from_user.id
    )

    player = get_player(
        user_id
    )

    scrolls = (
        player.get(
            "scrolls"
        )
        or []
    )

    # =====================================================
    # НЕМАЄ АКТИВНИХ СУВОЇВ
    # =====================================================

    if not scrolls:

        bot.send_message(
            message.chat.id,

            "📜 <b>Сувої Грінвуду</b>\n\n"

            "🦇 <b>Марчелло🦇:</b> "
            "Схоже, бібліотека порожня 📜",

            parse_mode="HTML",

            reply_markup=get_scrolls_menu()
        )

        return

    # =====================================================
    # ЗАГОЛОВОК
    # =====================================================

    text = (
        "📜 <b>Твої сувої Грінвуду</b>\n"
        f"📅 Сьогодні: <b>{get_today_text()}</b>\n"
        "────────────────────\n\n"
    )

    # =====================================================
    # СПИСОК СУВОЇВ
    # =====================================================

    for scroll in scrolls:

        text += (
            format_scroll(
                scroll
            )
            + "\n\n"
        )

    # =====================================================
    # ПОЯСНЕННЯ
    # =====================================================

    text += (
        "────────────────────\n"
        "🔥 — сувій має бути виконаний сьогодні"
    )

    # =====================================================
    # ВІДПРАВЛЯЄМО
    # =====================================================

    bot.send_message(
        message.chat.id,

        text,

        parse_mode="HTML",

        reply_markup=get_scrolls_menu()
    )


# =========================================================
# 🔙 НАЗАД ДО КВЕСТІВ
# =========================================================

@bot.message_handler(
    func=lambda message:
        message.text == "🔙 Назад до квестів"
)
def back_from_scrolls(message):

    bot.send_message(
        message.chat.id,

        "📝 Меню квестів",

        reply_markup=get_quests_menu()
    )
