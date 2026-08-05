from datetime import datetime
from zoneinfo import ZoneInfo

from services.config import bot
from services.database import get_player
from keyboards import get_main_menu, get_quests_menu

print("⚙️ Модуль handlers/quests завантажено!")


# --- ГОЛОВНЕ МЕНЮ КВЕСТІВ ---

@bot.message_handler(func=lambda message: message.text in ["🎯 Мої Квести", "🔙 Назад до квестів"])
def show_quests_menu(message):
    user_id = str(message.from_user.id)
    player = get_player(user_id)

    # Поточна дата за Києвом (формат ДД.ММ)
    today_str = datetime.now(ZoneInfo("Europe/Kyiv")).strftime("%d.%m")

    scrolls = player.get("quests", {}).get("scrolls", [])
    active_scrolls = [
        s for s in scrolls
        if s.get("done_count", 0) < s.get("max_count", 1)
    ]

    rituals = player.get("quests", {}).get("rituals", [])
    plants = player.get("quests", {}).get("plants", [])

    status_text = (
        "🌿 <b>Органайзер Завдань Грінвуду</b>\n"
        "────────────────────\n\n"
    )

    # === Блок Сувоїв ===
    status_text += "📜 <b>Активні сувої:</b>\n"

    if not active_scrolls:
        status_text += "• <i>Немає запечатаних угодок.</i>\n"
    else:
        for s in active_scrolls:
            fire = " 🔥" if s.get("deadline") == today_str else ""
            status_text += (
                f"• {s.get('emoji', '📜')} {s.get('task', 'Без назви')} "
                f"({s.get('done_count', 0)}/{s.get('max_count', 1)}) | "
                f"до {s.get('deadline', '--.--')}{fire}\n"
            )

    status_text += "\n"

    # === Блок Ритуалів ===
    status_text += "🔄 <b>Активні ритуали на сьогодні:</b>\n"

    kyiv_days = {
        0: "пн",
        1: "вт",
        2: "ср",
        3: "чт",
        4: "пт",
        5: "сб",
        6: "нд"
    }

    today_day = kyiv_days[datetime.now(ZoneInfo("Europe/Kyiv")).weekday()]

    today_rituals = [
        r for r in rituals
        if today_day in r.get("days", [])
    ]

    if not today_rituals:
        status_text += "• <i>На сьогодні немає активних ритуалів.</i>\n"
    else:
        for r in today_rituals:
            status = "✅" if r.get("done_today", False) else "⏳"
            status_text += (
                f"• {status} {r.get('emoji', '🔄')} "
                f"{r.get('task', 'Без назви')}\n"
            )

    status_text += "\n"

    # === Блок Рослин ===
    status_text += "🌱 <b>Рослини в теплиці:</b>\n"

    if not plants:
        status_text += "• <i>Теплиця порожня.</i>\n"
    else:
        for p in plants:
            fire = " 🔥" if p.get("deadline") == today_str else ""
            status_text += (
                f"• {p.get('emoji', '🌱')} "
                f"{p.get('task', 'Без назви')} | "
                f"до {p.get('deadline', '--.--')}{fire}\n"
            )

    status_text += "\n────────────────────\n"
    status_text += "Обери розділ для керування:"

    bot.send_message(
        message.chat.id,
        status_text,
        parse_mode="HTML",
        reply_markup=get_quests_menu()
    )


@bot.message_handler(func=lambda message: message.text == "🔙 Назад")
def back_to_main_menu(message):
    bot.send_message(
        message.chat.id,
        "🌲 Повертаємось до головного табору.",
        reply_markup=get_main_menu()
    )
