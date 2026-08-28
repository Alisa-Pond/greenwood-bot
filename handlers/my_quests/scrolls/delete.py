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

    player = get_player(
        user_id
    )

    scrolls = player.get(
        "scrolls"
    ) or []

    # ==================================================
    # НЕМАЄ СУВОЇВ
    # ==================================================

    if not scrolls:

        bot.send_message(
            message.chat.id,

            "🦇 <b>Марчелло🦇</b>\n"
            "«Тут поки що немає жодного сувою, "
            "який можна спалити.» 📜🌙",

            parse_mode="HTML",

            reply_markup=get_scrolls_menu()
        )

        return

    # ==================================================
    # СПИСОК СУВОЇВ
    # ==================================================

    text = (
        "🦇 <b>Марчелло🦇</b>\n"
        "🔥 <b>Спалення сувоїв</b>\n\n"
        "«Обери сувій або кілька сувоїв, "
        "які хочеш спалити.\n\n"
    )

    # ==================================================
    # НУМЕРАЦІЯ
    # ==================================================
    

    for display_number, scroll in enumerate(
        scrolls,
        start=1
    ):

        title = scroll.get(
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
        "✍️ Напиши номер сувою або кілька номерів "
        "через кому.\n\n"
        "Наприклад: 2 або 1,2,5 »\n",
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
# 🔥 ПАРСИНГ НОМЕРІВ
# ==================================================

def parse_scroll_numbers(text):

    if not text:
        return None

    # --------------------------------------------------
    # Розділяємо тільки через кому
    # --------------------------------------------------

    parts = text.split(",")

    numbers = []

    for part in parts:

        part = part.strip()

        # Порожній елемент
        #
        # Наприклад:
        # 1,,3
        #
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

def process_delete_scroll(message):

    # ==================================================
    # НАЗАД
    # ==================================================

    if message.text == "🔙 Назад до квестів":

        bot.send_message(
            message.chat.id,

            "📜 Повертаємось до сувоїв.",

            reply_markup=get_scrolls_menu()
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

    scrolls = player.get(
        "scrolls"
    ) or []

    # ==================================================
    # ПЕРЕВІРКА:
    # ЧИ Є СУВОЇ
    # ==================================================

    if not scrolls:

        bot.send_message(
            message.chat.id,

            "📜 Активних сувоїв більше немає.",

            reply_markup=get_scrolls_menu()
        )

        return

    # ==================================================
    # ОТРИМУЄМО НОМЕРИ
    # ==================================================

    selected_numbers = parse_scroll_numbers(
        message.text.strip()
    )

    # ==================================================
    # НЕВІРНИЙ ФОРМАТ
    # ==================================================

    if not selected_numbers:

        bot.send_message(
            message.chat.id,

            "🦇 <b>Марчелло🦇</b>\n"
            "«Я не зміг зрозуміти номери сувоїв.\n\n"
            "Напиши одне число або кілька через кому.»\n",

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

    invalid_numbers = [
        number
        for number in selected_numbers
        if not 1 <= number <= len(scrolls)
    ]

    if invalid_numbers:

        bot.send_message(
            message.chat.id,

            "🦇 <b>Марчелло🦇"
            f"«У тебе зараз "
            f"<b>{len(scrolls)}</b> активних сувоїв.\n\n"
            f"Вкажи номер.»",

            parse_mode="HTML"
        )

        bot.register_next_step_handler(
            message,
            process_delete_scroll
        )

        return

    # ==================================================
    # ПЕРЕТВОРЮЄМО НОМЕРИ КОРИСТУВАЧА
    # НА РЕАЛЬНІ ІНДЕКСИ
    # ==================================================

    selected_indexes = [
        number - 1
        for number in selected_numbers
    ]

    # ==================================================
    # ЗБЕРІГАЄМО НАЗВИ ДЛЯ ПОВІДОМЛЕННЯ
    # ==================================================

    deleted_titles = []

    for index in selected_indexes:

        scroll = scrolls[index]

        title = scroll.get(
            "title",
            "Без назви"
        )

        deleted_titles.append(
            title
        )

    # ==================================================
    # ВИДАЛЕННЯ
    # ==================================================
    #
    # ВАЖЛИВО:
    #
    # Видаляємо від більшого індексу до меншого.
    #
    # Наприклад:
    #
    # 1, 3, 4
    #
    # перетворюється на:
    #
    # 0, 2, 3
    #
    # Видаляємо:
    #
    # 3 → 2 → 0
    #
    # Тому pop() не зміщує індекси,
    # які ми ще не обробили.
    # ==================================================

    for selected_index in sorted(
        selected_indexes,
        reverse=True
    ):

        scrolls.pop(
            selected_index
        )

    # ==================================================
    # ЗБЕРІГАЄМО В SUPABASE
    # ==================================================

    player["scrolls"] = scrolls

    update_player(
        user_id,
        {
            "scrolls": scrolls
        }
    )

    # ==================================================
    # КІЛЬКІСТЬ ВИДАЛЕНИХ
    # ==================================================

    deleted_count = len(
        deleted_titles
    )

    remaining = len(
        scrolls
    )

    # ==================================================
    # СПИСОК ВИДАЛЕНИХ СУВОЇВ
    # ==================================================

    deleted_text = "\n".join(
        f"📜 {title}"
        for title in deleted_titles
    )

    # ==================================================
    # ФІНАЛЬНЕ ПОВІДОМЛЕННЯ
    # ==================================================

    if deleted_count == 1:

        message_text = (
            "🦇 <b>Марчелло🦇</b>\n"
            "«🔥 <b>Сувій спалено.</b>\n\n"

            f"{deleted_text}\n\n"

            "Його написані рядки спалахнули "
            "золотим полум'ям і перетворилися "
            "на попіл. ✨\n\n"

            f"📚 Активних сувоїв залишилось: "
            f"<b>{remaining}</b>»"
        )

    else:

        message_text = (
            "🦇 <b>Марчелло🦇</b>\n"
            "«🔥 <b>Сувої спалено.</b>\n\n"

            f"✨ Вилучено сувоїв: "
            f"<b>{deleted_count}</b>\n\n"

            f"{deleted_text}\n\n"

            "Їхні рядки спалахнули "
            "золотим полум'ям і перетворилися "
            "на попіл. ✨\n\n"

            f"📚 Активних сувоїв залишилось: "
            f"<b>{remaining}</b> »"
        )

    bot.send_message(
        message.chat.id,

        message_text,

        parse_mode="HTML",

        reply_markup=get_scrolls_menu()
    )
