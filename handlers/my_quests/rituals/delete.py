from services.config import bot
from services.database import get_player, update_player
from keyboards import get_rituals_menu

print("⚙️ Завантажено видалення ритуалів...")


# ==================================================
# 🔥 ПОЧАТОК ВИДАЛЕННЯ
# ==================================================

@bot.message_handler(
    func=lambda message: message.text == "🔥 Спалити ритуал"
)
def start_delete_ritual(message):

    user_id = str(message.from_user.id)
    player = get_player(user_id)

    rituals = player.get("rituals") or []

    if not rituals:
        bot.send_message(
            message.chat.id,
            "🕯 <b>Марчелло заглядає до книги ритуалів...</b>\n\n"
            "Тут поки що немає жодного ритуалу, який можна спалити. 🌙",
            parse_mode="HTML",
            reply_markup=get_rituals_menu()
        )
        return

    text = (
        "🔥 <b>Спалення ритуалу</b>\n\n"
        "Обери ритуал, який хочеш назавжди вилучити з книги Грінвуду:\n\n"
    )

    for index, ritual in enumerate(rituals, start=1):
        title = ritual.get("title", "Без назви")
        text += f"<b>{index}.</b> {title}\n"

    text += (
        "\n✍️ Напиши <b>номер</b> ритуалу, який хочеш спалити.\n"
        "Наприклад: <code>2</code>"
    )

    msg = bot.send_message(
        message.chat.id,
        text,
        parse_mode="HTML"
    )

    bot.register_next_step_handler(
        msg,
        process_delete_ritual
    )


# ==================================================
# 🔥 ОБРОБКА ВИБОРУ
# ==================================================

def process_delete_ritual(message):

    if message.text == "🔙 Назад до квестів":

        bot.send_message(
            message.chat.id,
            "🕯 Повертаємось до ритуалів.",
            reply_markup=get_rituals_menu()
        )
        return

    user_id = str(message.from_user.id)
    player = get_player(user_id)

    rituals = player.get("rituals") or []

    try:
        number = int(message.text.strip())

    except ValueError:

        bot.send_message(
            message.chat.id,
            "🦇 <b>Марчелло хмуриться.</b>\n\n"
            "Потрібно вказати саме номер ритуалу. "
            "Наприклад: <code>2</code>",
            parse_mode="HTML"
        )

        bot.register_next_step_handler(
            message,
            process_delete_ritual
        )
        return

    if number < 1 or number > len(rituals):

        bot.send_message(
            message.chat.id,
            f"🦇 <b>Такого ритуалу немає.</b>\n\n"
            f"У тебе зараз {len(rituals)} активних ритуалів.\n"
            "Вкажи номер від 1 до "
            f"{len(rituals)}.",
            parse_mode="HTML"
        )

        bot.register_next_step_handler(
            message,
            process_delete_ritual
        )
        return

    # ==================================================
    # ВИДАЛЯЄМО РИТУАЛ
    # ==================================================

    ritual = rituals[number - 1]
    title = ritual.get("title", "Без назви")

    rituals.pop(number - 1)

    update_player(
        user_id,
        {
            "rituals": rituals
        }
    )

    remaining = len(rituals)

    bot.send_message(
        message.chat.id,
        "🔥 <b>Ритуал спалено.</b>\n\n"
        f"🕯 <b>{title}</b>\n\n"
        "Його слова розчинилися у вогні, "
        "а сторінка книги Грінвуду спорожніла. 🌙\n\n"
        f"📖 Активних ритуалів залишилось: <b>{remaining}</b>",
        parse_mode="HTML",
        reply_markup=get_rituals_menu()
    )
