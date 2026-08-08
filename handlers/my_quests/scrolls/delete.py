from services.config import bot
from services.database import get_player, update_player
from keyboards import get_scrolls_menu

print("⚙️ Завантажено видалення сувоїв...")


# ==================================================
# 🔥 ПОЧАТОК ВИДАЛЕННЯ СУВОЮ
# ==================================================

@bot.message_handler(
    func=lambda message: message.text == "🔥 Спалити сувій"
)
def start_delete_scroll(message):

    user_id = str(message.from_user.id)
    player = get_player(user_id)

    scrolls = player.get("scrolls") or []

    if not scrolls:
        bot.send_message(
            message.chat.id,
            "🦇 <b>Марчелло перегортає книгу сувоїв...</b>\n\n"
            "Тут поки що немає жодного сувою, "
            "який можна спалити. 📜🌙",
            parse_mode="HTML",
            reply_markup=get_scrolls_menu()
        )
        return

    text = (
        "🔥 <b>Спалення сувою</b>\n\n"
        "Обери сувій, який хочеш вилучити з архіву Грінвуду:\n\n"
    )

    for index, scroll in enumerate(scrolls, start=1):

        title = scroll.get(
            "title",
            "Без назви"
        )

        text += (
            f"<b>{index}.</b> {title}\n"
        )

    text += (
        "\n✍️ Напиши <b>номер</b> сувою, "
        "який хочеш спалити.\n"
        "Наприклад: <code>2</code>"
    )

    msg = bot.send_message(
        message.chat.id,
        text,
        parse_mode="HTML"
    )

    bot.register_next_step_handler(
        msg,
        process_delete_scroll
    )


# ==================================================
# 🔥 ОБРОБКА ВИБОРУ
# ==================================================

def process_delete_scroll(message):

    if message.text == "🔙 Назад до квестів":

        bot.send_message(
            message.chat.id,
            "📜 Повертаємось до сувоїв.",
            reply_markup=get_scrolls_menu()
        )

        return

    user_id = str(message.from_user.id)

    player = get_player(user_id)

    scrolls = player.get("scrolls") or []

    # ==================================================
    # ПЕРЕВІРКА НОМЕРА
    # ==================================================

    try:

        number = int(
            message.text.strip()
        )

    except ValueError:

        bot.send_message(
            message.chat.id,

            "🦇 <b>Марчелло хмуриться.</b>\n\n"
            "Потрібно вказати саме номер сувою.\n"
            "Наприклад: <code>2</code>",

            parse_mode="HTML"
        )

        bot.register_next_step_handler(
            message,
            process_delete_scroll
        )

        return

    # ==================================================
    # ПЕРЕВІРКА ДІАПАЗОНУ
    # ==================================================

    if number < 1 or number > len(scrolls):

        bot.send_message(
            message.chat.id,

            f"🦇 <b>Такого сувою немає.</b>\n\n"
            f"У тебе зараз "
            f"<b>{len(scrolls)}</b> активних сувоїв.\n\n"
            f"Вкажи номер від "
            f"<b>1</b> до <b>{len(scrolls)}</b>.",

            parse_mode="HTML"
        )

        bot.register_next_step_handler(
            message,
            process_delete_scroll
        )

        return

    # ==================================================
    # ВИДАЛЕННЯ
    # ==================================================

    scroll = scrolls[number - 1]

    title = scroll.get(
        "title",
        "Без назви"
    )

    scrolls.pop(number - 1)

    # ==================================================
    # ЗБЕРІГАЄМО В SUPABASE
    # ==================================================

    update_player(
        user_id,
        {
            "scrolls": scrolls
        }
    )

    remaining = len(scrolls)

    # ==================================================
    # ПОВІДОМЛЕННЯ
    # ==================================================

    bot.send_message(
        message.chat.id,

        "🔥 <b>Сувій спалено.</b>\n\n"

        f"📜 <b>{title}</b>\n\n"

        "Його написані рядки спалахнули "
        "золотим полум'ям і перетворилися на попіл. ✨\n\n"

        f"📚 Активних сувоїв залишилось: "
        f"<b>{remaining}</b>",

        parse_mode="HTML",

        reply_markup=get_scrolls_menu()
    )
