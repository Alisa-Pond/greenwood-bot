from datetime import datetime

from services.config import bot
from services.database import get_player
from keyboards import get_quests_menu, get_scrolls_menu

from services.activity_utils import (
    get_title,
    get_xp,
    get_spheres,
    parse_deadline,
)


print("⚙️ Реєструємо меню сувоїв...")


# =========================================================
# 📜 МЕНЮ СУВОЇВ
# =========================================================

@bot.message_handler(
    func=lambda message: message.text == "📜 Сувої"
)
def open_scrolls(message):

    user_id = str(
        message.from_user.id
    )

    player = get_player(
        user_id
    )

    scrolls = player.get(
        "scrolls"
    ) or []

    # =====================================================
    # НЕМАЄ АКТИВНИХ СУВОЇВ
    # =====================================================

    if not scrolls:

        bot.send_message(
            message.chat.id,

            "📜 <b>Сувої Грінвуду</b>\n\n"

            "🦇 <b>Марчелло🦇:</b>\n"
            "Схоже, цього разу моя книга порожня. "
            "Жодного активного сувою. "
            "Або ти вже встигла виконати все, "
            "що на себе записала. Непогано. 🦇",

            parse_mode="HTML",

            reply_markup=get_scrolls_menu()
        )

        return

    # =====================================================
    # ДАТА СЬОГОДНІ
    # =====================================================

    today = datetime.now().date()

    weekday_names = [
        "пн",
        "вт",
        "ср",
        "чт",
        "пт",
        "сб",
        "нд",
    ]

    today_text = (
        f"{today.strftime('%d.%m.%Y')}, "
        f"{weekday_names[today.weekday()]}"
    )

    # =====================================================
    # ЗАГОЛОВОК
    # =====================================================

    text = (
        "📜 <b>Твої сувої Грінвуду</b>\n"
        f"📅 Сьогодні: <b>{today_text}</b>\n"
        "────────────────────\n\n"
    )

    # =====================================================
    # СПИСОК СУВОЇВ
    # =====================================================

    for index, scroll in enumerate(
        scrolls,
        start=1
    ):

        # -------------------------------------------------
        # СФЕРИ
        # -------------------------------------------------

        spheres = get_spheres(
            scroll
        )

        spheres_text = "".join(
            spheres
        )

        # -------------------------------------------------
        # XP
        # -------------------------------------------------

        xp = get_xp(
            scroll
        )

        # -------------------------------------------------
        # НАЗВА
        # -------------------------------------------------

        title = get_title(
            scroll
        )

        # -------------------------------------------------
        # ДЕДЛАЙН
        # -------------------------------------------------

        deadline = scroll.get(
            "deadline"
        )

        status_icon = ""

        deadline_text = (
            deadline
            if deadline
            else "без дедлайну"
        )

        if deadline:

            deadline_date = parse_deadline(
                deadline
            )

            if deadline_date:

                deadline_day = (
                    deadline_date.date()
                )

                # -----------------------------------------
                # 🔥 ДЕДЛАЙН СЬОГОДНІ
                # -----------------------------------------

                if deadline_day == today:

                    status_icon = "🔥"

                # -----------------------------------------
                # ⚠️ ПРОСТРОЧЕНИЙ
                # -----------------------------------------

                elif deadline_day < today:

                    status_icon = "⚠️"

        # =================================================
        # РЯДОК СУВОЮ
        # =================================================

        text += (
            f"{status_icon} "
            f"📜 <b>{index}. {title}</b> "
            f"({xp:.1f} XP)\n"
            f"    └── 📅 Дедлайн: {deadline_text}\n\n"
        )

    # =====================================================
    # ПОЯСНЕННЯ СТАТУСІВ
    # =====================================================

    has_today = False
    has_overdue = False

    for scroll in scrolls:

        deadline = scroll.get(
            "deadline"
        )

        if not deadline:
            continue

        deadline_date = parse_deadline(
            deadline
        )

        if not deadline_date:
            continue

        deadline_day = deadline_date.date()

        if deadline_day == today:

            has_today = True

        elif deadline_day < today:

            has_overdue = True

    if has_today or has_overdue:

        text += (
            "────────────────────\n"
        )

        if has_today:

            text += (
                "🔥 — дедлайн сьогодні\n"
            )

        if has_overdue:

            text += (
                "⚠️ — сувій прострочений\n"
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

        "📝 <b>Меню квестів</b>",

        parse_mode="HTML",

        reply_markup=get_quests_menu()
    )
