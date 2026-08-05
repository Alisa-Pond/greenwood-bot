from services.config import bot
from services.database import get_player
from keyboards import get_scrolls_menu

@bot.message_handler(func=lambda message: message.text == "📜 Сувої завдань")
def show_scrolls_menu(message):
    user_id = str(message.from_user.id)
    player = get_player(user_id)

    scrolls = player.get("quests", {}).get("scrolls", [])
    active_scrolls = [
        s for s in scrolls
        if s.get("done_count", 0) < s.get("max_count", 1)
    ]

    status_text = (
        "📜 <b>Книга Сувоїв Грінвуду</b>\n\n"
        "🦇 <b>Марчелло:</b>\n"
        "«Кожен сувій є угодою із самим собою.\n"
        "Виконані угоди зміцнюють твою силу.\n"
        "Порушені залишають слід у хроніках...»\n\n"

        "📌 <b>Активні сувої:</b>\n"
    )

    if not active_scrolls:
        status_text += (
            "• <i>Жодного активного сувою.</i>"
        )
    else:
        for idx, s in enumerate(active_scrolls, start=1):
            status_text += (
                f"{idx}. "
                f"{s.get('emoji','📜')} "
                f"<b>{s.get('task')}</b>\n"
                f"    {s.get('done_count',0)}/{s.get('max_count',1)} "
                f"• {float(s.get('xp_per_once',0)):.1f} XP"
                f" • до {s.get('deadline','--.--.----')}\n"
            )

    status_text += "\n👇 Обери дію."

    bot.send_message(
        message.chat.id,
        status_text,
        parse_mode="HTML",
        reply_markup=get_scrolls_menu()
    )
