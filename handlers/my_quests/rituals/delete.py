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

    user_id = str(
        message.from_user.id
    )

    player = get_player(
        user_id
    )

    rituals = player.get(
        "rituals"
    ) or []

    # ==================================================
    # НЕМАЄ РИТУАЛІВ
    # ==================================================

    if not rituals:

        bot.send_message(
            message.chat.id,

            "🦇 <b>Марчелло🦇:</b>\n"
            "Тут поки що немає жодного ритуалу, "
            "який можна спалити. ",

            parse_mode="HTML",

            reply_markup=get_rituals_menu()
        )

        return

    # ==================================================
    # СПИСОК РИТУАЛІВ
    # ==================================================

    text = (
        "🦇 <b>Марчелло🦇:.</b>\n"
        "Обери ритуал або кілька ритуалів, "
        "які хочеш назавжди вилучити "
        "з книги Грінвуду:\n\n"
    )

   

    for display_number, ritual in enumerate(
        rituals,
        start=1
    ):

        title = ritual.get(
            "title",
            "Без назви"
        )

        text += (
            f"<b>{display_number}.</b> "
            f"{title}\n"
        )

    # ==================================================
    # ІНСТРУКЦІЯ
    # ==================================================

    text += (
        "\n"
        "✍️ Напиши номер ритуалу або кілька номерів "
        "через кому.\n\n"
        "Наприклад:\n"
        "2 або 1, 3, 4"
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
# 🔥 ПАРСИНГ НОМЕРІВ
# ==================================================

def parse_ritual_numbers(text):

    if not text:
        return None

    # --------------------------------------------------
    # Розділяємо номери через кому
    # --------------------------------------------------

    parts = text.split(",")

    numbers = []

    for part in parts:

        part = part.strip()

        # --------------------------------------------------
        # Захист від порожніх значень
        #
        # Наприклад:
        # 1,,3
        # --------------------------------------------------

        if not part:

            return None

        try:

            number = int(
                part
            )

        except (
            ValueError,
            TypeError
        ):

            return None

        # --------------------------------------------------
        # Номер повинен бути позитивним
        # --------------------------------------------------

        if number <= 0:

            return None

        numbers.append(
            number
        )

    # ==================================================
    # ЗАХИСТ ВІД ДУБЛІВ
    # ==================================================
    #
    # Наприклад:
    #
    # 1, 2, 2
    #
    # не дозволяємо.
    # ==================================================

    if len(numbers) != len(set(numbers)):

        return None

    return numbers


# ==================================================
# 🔥 ОБРОБКА ВИБОРУ
# ==================================================

def process_delete_ritual(message):

    # ==================================================
    # НАЗАД
    # ==================================================

    if message.text == "🔙 Назад до квестів":

        bot.send_message(
            message.chat.id,

            " Повертаємось до ритуалів.",

            reply_markup=get_rituals_menu()
        )

        return

    # ==================================================
    # ОТРИМУЄМО ГРАВЦЯ
    # ==================================================

    user_id = str(
        message.from_user.id
    )

    player = get_player(
        user_id
    )

    rituals = player.get(
        "rituals"
    ) or []

    # ==================================================
    # НЕМАЄ РИТУАЛІВ
    # ==================================================

    if not rituals:

        bot.send_message(
            message.chat.id,

            "🦇 <b>Марчелло🦇:</b>\n" 
            "Активних ритуалів більше немає.",

            reply_markup=get_rituals_menu()
        )

        return

    # ==================================================
    # ОТРИМУЄМО НОМЕРИ
    # ==================================================

    selected_numbers = parse_ritual_numbers(
        message.text.strip()
    )

    # ==================================================
    # НЕВІРНИЙ ФОРМАТ
    # ==================================================

    if not selected_numbers:

        bot.send_message(
            message.chat.id,

            "🦇 <b>Марчелло🦇:</b>\n\n\n"
            "Я не зміг зрозуміти номери ритуалів.\n\n"
            "Напиши, наприклад:\n"
            "<code>2</code>\n"
            "або\n"
            "<code>1, 3, 4</code>",

            parse_mode="HTML"
        )

        bot.register_next_step_handler(
            message,
            process_delete_ritual
        )

        return

    # ==================================================
    # ПЕРЕВІРКА ДІАПАЗОНУ
    # ==================================================

    invalid_numbers = [
        number
        for number in selected_numbers
        if not 1 <= number <= len(rituals)
    ]

    if invalid_numbers:

        bot.send_message(
            message.chat.id,

            "🦇 <b>Марчелло🦇:</b>\n <b>Такого ритуалу немає.</b>\n\n"
            f"У тебе зараз "
            f"<b>{len(rituals)}</b> активних ритуалів.\n\n"
            f"Вкажи номер або номери від "
            f"<b>1</b> до <b>{len(rituals)}</b>.",

            parse_mode="HTML"
        )

        bot.register_next_step_handler(
            message,
            process_delete_ritual
        )

        return

    # ==================================================
    # ПЕРЕТВОРЮЄМО НОМЕРИ
    # КОРИСТУВАЧА НА ІНДЕКСИ
    # ==================================================

    selected_indexes = [
        number - 1
        for number in selected_numbers
    ]

    # ==================================================
    # ЗБЕРІГАЄМО НАЗВИ
    # ==================================================

    deleted_titles = []

    for index in selected_indexes:

        ritual = rituals[index]

        title = ritual.get(
            "title",
            "Без назви"
        )

        deleted_titles.append(
            title
        )


    for selected_index in sorted(
        selected_indexes,
        reverse=True
    ):

        rituals.pop(
            selected_index
        )

    # ==================================================
    # ЗБЕРІГАЄМО В PLAYER
    # ==================================================

    player["rituals"] = rituals

    # ==================================================
    # SUPABASE
    # ==================================================

    update_player(
        user_id,
        {
            "rituals": rituals
        }
    )

    # ==================================================
    # КІЛЬКІСТЬ
    # ==================================================

    deleted_count = len(
        deleted_titles
    )

    remaining = len(
        rituals
    )

    # ==================================================
    # СПИСОК ВИДАЛЕНИХ РИТУАЛІВ
    # ==================================================

    deleted_text = "\n".join(
        f"🕯 {title}"
        for title in deleted_titles
    )

    # ==================================================
    # ФІНАЛЬНЕ ПОВІДОМЛЕННЯ
    # ==================================================

    if deleted_count == 1:

        message_text = (
            "🦇 <b>Марчелло🦇:</b>\n"
            "🔥 <b>Ритуал спалено.</b>\n\n"

            f"{deleted_text}\n\n"

            "Його слова розчинилися у вогні, "
            "а сторінка книги Грінвуду "
            "спорожніла. 🌙\n\n"

            f"📖 Активних ритуалів залишилось: "
            f"<b>{remaining}</b>"
        )

    else:

        message_text = (
            "🦇 <b>Марчелло🦇:</b>\n"
            "🔥 <b>Ритуали спалено.</b>\n\n"

            f"✨ Вилучено ритуалів: "
            f"<b>{deleted_count}</b>\n\n"

            f"{deleted_text}\n\n"

            "Їхні слова розчинилися у вогні, "
            "а сторінки книги Грінвуду "
            "спорожніли. 🌙\n\n"

            f"📖 Активних ритуалів залишилось: "
            f"<b>{remaining}</b>"
        )

    bot.send_message(
        message.chat.id,

        message_text,

        parse_mode="HTML",

        reply_markup=get_rituals_menu()
    )
