from datetime import datetime
from telebot import types

from services.config import bot
from services.database import get_player, update_player
from services.activity_utils import get_title, get_xp, get_spheres, get_today, add_total_xp, add_xp_to_spheres, update_statistics, build_back_button
from services.activity_loot import try_activity_loot

WEEKDAYS = ["пн", "вт", "ср", "чт", "пт", "сб", "нд"]


def ritual_is_for_today(ritual):
    if ritual.get("daily") is True:
        return True
    days = ritual.get("days") or []
    if not isinstance(days, list):
        return False
    today = datetime.now().weekday()
    return today in days or WEEKDAYS[today] in days


def choose_ritual(message):
    user_id = str(message.from_user.id)
    player = get_player(user_id)
    rituals = player.get("rituals") or []

    if not rituals:
        bot.send_message(message.chat.id, "🔄 <b>Жодного активного ритуалу.</b>\n\nЛіс сьогодні напрочуд тихий. 🌲", parse_mode="HTML", reply_markup=build_back_button())
        return

    available = [(i, r) for i, r in enumerate(rituals) if ritual_is_for_today(r)]
    if not available:
        bot.send_message(message.chat.id, "💤 <b>Сьогодні жоден ритуал не чекає на виконання.</b>\n\nТвої ритуали відпочивають до свого дня. 🌙", parse_mode="HTML", reply_markup=build_back_button())
        return

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for index, ritual in available:
        markup.row(types.KeyboardButton(f"🔄 {index + 1}. {get_title(ritual)}"))
    markup.row(types.KeyboardButton("🔙 Назад"))

    msg = bot.send_message(message.chat.id, "🔄 <b>Сьогоднішні ритуали:</b>\n\nОбери той, який щойно провела.", parse_mode="HTML", reply_markup=markup)
    bot.register_next_step_handler(msg, complete_ritual)


def complete_ritual(message):
    if message.text == "🔙 Назад":
        from handlers.complete_activity import start_complete
        start_complete(message)
        return

    user_id = str(message.from_user.id)
    player = get_player(user_id)
    rituals = player.get("rituals") or []

    try:
        selected_index = int(message.text.split(".")[0].replace("🔄", "").strip()) - 1
    except (ValueError, IndexError):
        selected_index = None

    if selected_index is None or not 0 <= selected_index < len(rituals):
        choose_ritual(message)
        return

    ritual = rituals[selected_index]
    title = get_title(ritual)
    xp = get_xp(ritual)
    spheres = get_spheres(ritual)
    today = get_today()

    if ritual.get("last_completed") == today:
        bot.send_message(message.chat.id, "🌙 <b>Цей ритуал уже виконано сьогодні.</b>", parse_mode="HTML", reply_markup=build_back_button())
        return

    add_total_xp(player, xp)
    add_xp_to_spheres(player, spheres, xp)
    loot = try_activity_loot(player)

    archive = player.get("ritual_archive") or []
    completed = dict(ritual)
    completed["completed_date"] = today
    archive.append(completed)

    ritual["last_completed"] = today
    rituals[selected_index] = ritual
    player["rituals"] = rituals
    player["ritual_archive"] = archive
    update_statistics(player, completed_rituals=1)

    update_player(user_id, {
        "xp_total": player["xp_total"],
        "spheres": player["spheres"],
        "rituals": player["rituals"],
        "ritual_archive": player["ritual_archive"],
        "statistics": player["statistics"],
        "inventory": player.get("inventory") or [],
    })

    loot_text = f"\n🎁 Знайдено: <b>{loot}</b>" if loot else ""
    bot.send_message(
        message.chat.id,
        "🔥 <b>Ритуал проведено!</b>\n\n"
        f"🔄 <b>{title}</b>\n"
        f"⭐ Отримано: <b>{xp:.1f} XP</b>\n"
        f"🎯 Сфери: {' '.join(spheres)}"
        f"{loot_text}\n\n"
        "🕯️ Запис збережено в <b>Архіві ритуалів</b>.",
        parse_mode="HTML",
        reply_markup=build_back_button(),
    )

