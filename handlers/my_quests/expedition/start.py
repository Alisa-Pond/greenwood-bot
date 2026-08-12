from datetime import datetime, timezone

from services.config import bot
from services.database import get_player, update_player

from handlers.my_quests.expedition.menu import get_active_expedition


print("🐜 Реєструємо запуск експедицій...")


# =========================================================
# СФЕРИ
# =========================================================

SPHERE_ALIASES = {

    "💪": "health",
    "здоров'я": "health",
    "здоровя": "health",
    "health": "health",

    "🧠": "wisdom",
    "мудрість": "wisdom",
    "мудрість": "wisdom",
    "wisdom": "wisdom",

    "🎨": "art",
    "творчість": "art",
    "творчість": "art",
    "мистецтво": "art",
    "art": "art",

    "💵": "finance",
    "фінанси": "finance",
    "finance": "finance",

    "🤝": "relations",
    "зв'язки": "relations",
    "зв’язки": "relations",
    "відносини": "relations",
    "relations": "relations"
}


# =========================================================
# НАЗВИ СФЕР
# =========================================================

SPHERE_NAMES = {

    "health": "💪 Здоров'я",
    "wisdom": "🧠 Мудрість",
    "art": "🎨 Творчість",
    "finance": "💵 Фінанси",
    "relations": "🤝 Зв'язки"
}


# =========================================================
# КНОПКА СТАРТУ
# =========================================================

@bot.message_handler(
    func=lambda message:
        message.text == "🐜 Відправити мурах в експедицію"
)
def start_expedition(message):

    user_id = str(
        message.from_user.id
    )

    player = get_player(
        user_id
    )

    # =====================================================
    # ПЕРЕВІРКА: ЧИ НЕМАЄ ВЖЕ ЕКСПЕДИЦІЇ
    # =====================================================

    active_expedition = get_active_expedition(
        player
    )

    if active_expedition:

        bot.send_message(
            message.chat.id,
            (
                "🐜 <b>Генерал Мураха доповідає:</b>\n\n"
                "Загін уже перебуває в експедиції.\n\n"
                "Не можна відправити новий загін, "
                "поки попередній ще не повернувся."
            ),
            parse_mode="HTML"
        )

        return

    # =====================================================
    # ЗАПИТ СФЕР
    # =====================================================

    text = (
        "🐜 <b>Генерал Мураха:</b>\n\n"

        "Перед відправленням загону потрібно визначити, "
        "яким сферам сьогодні служитиме твоя експедиція.\n\n"

        "Можеш обрати <b>одну або кілька сфер</b>.\n\n"

        "Напиши їхні назви або просто використай емодзі.\n\n"

        "<b>Наприклад:</b>\n"
        "🧠 🎨\n\n"

        "<b>Доступні сфери:</b>\n"
        "💪 Здоров'я\n"
        "🧠 Мудрість\n"
        "🎨 Творчість\n"
        "💵 Фінанси\n"
        "🤝 Зв'язки\n\n"

        "🐜 <i>Генерал чекає на наказ.</i>"
    )

    bot.send_message(
        message.chat.id,
        text,
        parse_mode="HTML"
    )

    bot.register_next_step_handler(
        message,
        process_expedition_spheres
    )


# =========================================================
# ОБРОБКА ВИБОРУ СФЕР
# =========================================================

def process_expedition_spheres(message):

    user_id = str(
        message.from_user.id
    )

    # =====================================================
    # СКАСУВАННЯ
    # =====================================================

    if message.text is None:

        bot.send_message(
            message.chat.id,
            (
                "🐜 Генерал Мураха не зміг розібрати "
                "цей наказ.\n\n"
                "Спробуй ще раз, використовуючи "
                "назви сфер або їхні емодзі."
            )
        )

        return

    user_text = message.text.strip()

    if user_text.lower() in (
        "скасувати",
        "відміна",
        "назад"
    ):

        bot.send_message(
            message.chat.id,
            (
                "🐜 Наказ скасовано.\n\n"
                "Загін залишається в таборі."
            )
        )

        return

    # =====================================================
    # РОЗБИВАЄМО ТЕКСТ
    # =====================================================

    # Дозволяємо:
    #
    # 🧠 🎨
    #
    # або:
    #
    # мудрість творчість
    #
    # або:
    #
    # 🧠, 🎨
    #
    normalized_text = (
        user_text
        .replace(",", " ")
        .replace(";", " ")
        .replace("\n", " ")
    )

    parts = normalized_text.split()

    selected_spheres = []
    unknown_parts = []

    # =====================================================
    # ВИЗНАЧАЄМО СФЕРИ
    # =====================================================

    for part in parts:

        normalized_part = part.strip().lower()

        sphere_key = SPHERE_ALIASES.get(
            normalized_part
        )

        if sphere_key:

            if sphere_key not in selected_spheres:

                selected_spheres.append(
                    sphere_key
                )

        else:

            unknown_parts.append(
                part
            )

    # =====================================================
    # НЕ ВДАЛОСЯ РОЗПІЗНАТИ ЖОДНОЇ СФЕРИ
    # =====================================================

    if not selected_spheres:

        bot.send_message(
            message.chat.id,
            (
                "🐜 <b>Генерал Мураха:</b>\n\n"

                "Наказ не розпізнано.\n\n"

                "Спробуй, наприклад:\n"
                "🧠 🎨\n\n"

                "або:\n"
                "<i>мудрість творчість</i>\n\n"

                "Обери хоча б одну сферу."
            ),
            parse_mode="HTML"
        )

        bot.register_next_step_handler(
            message,
            process_expedition_spheres
        )

        return

    # =====================================================
    # ЯКЩО Є НЕВІДОМІ СЛОВА
    # =====================================================

    if unknown_parts:

        unknown_text = ", ".join(
            unknown_parts
        )

        bot.send_message(
            message.chat.id,
            (
                "🐜 <b>Генерал Мураха:</b>\n\n"

                f"Я розпізнав не всі частини наказу: "
                f"<b>{unknown_text}</b>\n\n"

                "Щоб не відправити загін "
                "не в той бік, введи сфери ще раз.\n\n"

                "Наприклад:\n"
                "🧠 🎨 💵"
            ),
            parse_mode="HTML"
        )

        bot.register_next_step_handler(
            message,
            process_expedition_spheres
        )

        return

    # =====================================================
    # ОТРИМУЄМО ГРАВЦЯ ЩЕ РАЗ
    # =====================================================

    player = get_player(
        user_id
    )

    active_expedition = get_active_expedition(
        player
    )

    # =====================================================
    # ЗАХИСТ ВІД ПОДВІЙНОГО ЗАПУСКУ
    # =====================================================

    if active_expedition:

        bot.send_message(
            message.chat.id,
            (
                "🐜 <b>Генерал Мураха:</b>\n\n"
                "Стоп!\n\n"
                "Загін уже вирушив у експедицію. "
                "Новий наказ більше не потрібен."
            ),
            parse_mode="HTML"
        )

        return

    # =====================================================
    # ЧАС ПОЧАТКУ
    # =====================================================

    now = datetime.now(
        timezone.utc
    )

    started_at = now.isoformat()

    # =====================================================
    # СТВОРЮЄМО ЕКСПЕДИЦІЮ
    # =====================================================

    expedition = {

        "status": "active",

        "started_at": started_at,

        "last_resumed_at": started_at,

        "paused_at": None,

        "active_seconds": 0,

        "last_reminder_minute": 0,

        "spheres": selected_spheres
    }

    # =====================================================
    # ЗБЕРІГАЄМО
    # =====================================================

    success = update_player(
        user_id,
        {
            "expeditions": [
                expedition
            ]
        }
    )

    if not success:

        bot.send_message(
            message.chat.id,
            (
                "🐜 <b>Генерал Мураха:</b>\n\n"
                "Виникла проблема з картою експедиції. "
                "Я не можу безпечно відправити загін.\n\n"
                "Спробуй ще раз трохи пізніше."
            ),
            parse_mode="HTML"
        )

        return

    # =====================================================
    # ГОТУЄМО НАЗВИ СФЕР
    # =====================================================

    spheres_text = "\n".join(
        f"• {SPHERE_NAMES[sphere]}"
        for sphere in selected_spheres
    )

    # =====================================================
    # ФІНАЛЬНА ДОПОВІДЬ ПРО СТАРТ
    # =====================================================

    text = (
        "🐜 <b>ГЕНЕРАЛ МУРАХА ДОПОВІДАЄ!</b>\n\n"

        "Загін отримав наказ і вирушає "
        "досліджувати Грінвуд.\n\n"

        "<b>Сфери експедиції:</b>\n"
        f"{spheres_text}\n\n"

        "🎒 Рюкзаки споряджено.\n"
        "🧭 Компаси перевірено.\n"
        "🔎 Розвідники розосереджені по стежках.\n\n"

        "⏱️ <b>Експедицію розпочато.</b>\n\n"

        "Ти можеш займатися своєю справою, "
        "а мурахи тим часом шукатимуть "
        "те, що приховано серед дерев, води "
        "та нічного неба.\n\n"

        "🐜 <i>Коли захочеш повернути загін, "
        "відкрий розділ «🧭 Експедиції».</i>"
    )

    bot.send_message(
        message.chat.id,
        text,
        parse_mode="HTML"
    )
