from datetime import datetime, timezone

from services.config import bot
from services.database import get_player, update_player

from keyboards import (
    get_expedition_menu,
    get_quests_menu
)

from handlers.my_quests.expedition.menu import (
    get_active_expedition
)


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
    "мудрость": "wisdom",
    "wisdom": "wisdom",

    "🎨": "art",
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
# КЛАВІАТУРА ВИБОРУ СФЕР
# =========================================================

def get_sphere_selection_keyboard():

    from telebot import types

    markup = types.ReplyKeyboardMarkup(
        resize_keyboard=True
    )

    markup.row(
        types.KeyboardButton("🔙 Назад")
    )

    return markup


# =========================================================
# ПОЧАТОК ЕКСПЕДИЦІЇ
# =========================================================

def start_expedition(message):

    user_id = str(
        message.from_user.id
    )

    player = get_player(
        user_id
    )

    # =====================================================
    # ПЕРЕВІРКА АКТИВНОЇ ЕКСПЕДИЦІЇ
    # =====================================================

    active_expedition = get_active_expedition(
        player
    )

    if active_expedition:

        bot.send_message(
            message.chat.id,
            (
                "🐜 <b>Генерал Мураха доповідає!</b>\n\n"

                "Загін уже перебуває в експедиції.\n\n"

                "Новий загін не може вирушити, "
                "поки попередній ще не повернувся."
            ),
            parse_mode="HTML",
            reply_markup=get_expedition_menu(
                active_expedition
            )
        )

        return

    # =====================================================
    # ОПИС + ВИБІР СФЕР
    # =====================================================

    text = (
        "🐜 <b>Генерал Мураха доповідає! 🐜</b>\n\n"

        "🧭 <b>Експедиція</b> — це вихід "
        "розвідувального загону в дикі землі Грінвуду.\n\n"

        "Ліс постійно змінюється. Стежки ведуть "
        "у нові місця, старі дупла приховують знахідки, "
        "а під корінням іноді знаходиться те, "
        "чого там учора ще не було.\n\n"

        "🐜 Загін досліджує Грінвуд, поки триває "
        "експедиція. Чим довше мурахи залишаються "
        "в дорозі, тим більше території вони "
        "встигають обстежити.\n\n"

        "🎒 Після повернення всі знайдені предмети "
        "потраплять до твого рюкзака.\n\n"

        "Перед відправленням обери, "
        "яким сферам служитиме ця експедиція.\n\n"

        "Можна обрати <b>одну або кілька сфер</b>.\n\n"

        "<b>Доступні сфери:</b>\n"
        "💪 Здоров'я\n"
        "🧠 Мудрість\n"
        "🎨 Творчість\n"
        "💵 Фінанси\n"
        "🤝 Зв'язки\n\n"

        "Наприклад:\n"
        "<code>🧠 🎨</code>\n"
        "<code>🧠🎨</code>\n"
        "<code>мудрість творчість</code>"
    )

    bot.send_message(
        message.chat.id,
        text,
        parse_mode="HTML",
        reply_markup=get_sphere_selection_keyboard()
    )

    bot.register_next_step_handler(
        message,
        process_expedition_spheres
    )


# =========================================================
# ОБРОБКА СФЕР
# =========================================================

def process_expedition_spheres(message):

    user_id = str(
        message.from_user.id
    )

    # =====================================================
    # ПЕРЕВІРКА ПОВІДОМЛЕННЯ
    # =====================================================

    if message.text is None:

        bot.send_message(
            message.chat.id,
            (
                "🐜 <b>Генерал Мураха:</b>\n\n"

                "Наказ не вдалося розібрати.\n\n"

                "Вкажи одну або кілька сфер "
                "за назвою чи емодзі."
            ),
            parse_mode="HTML",
            reply_markup=get_sphere_selection_keyboard()
        )

        bot.register_next_step_handler(
            message,
            process_expedition_spheres
        )

        return

    user_text = message.text.strip()

    # =====================================================
    # НАЗАД
    # =====================================================

    if user_text.lower() in (
        "🔙 назад",
        "назад",
        "скасувати",
        "відміна"
    ):

        bot.send_message(
            message.chat.id,
            (
                "🐜 <i>Наказ скасовано. "
                "Загін залишається в таборі.</i>"
            ),
            parse_mode="HTML",
            reply_markup=get_quests_menu()
        )

        return

    # =====================================================
    # НОРМАЛІЗАЦІЯ
    # =====================================================

    normalized_text = (
        user_text
        .lower()
        .replace(",", " ")
        .replace(";", " ")
        .replace("\n", " ")
    )

    parts = normalized_text.split()

    selected_spheres = []
    unknown_parts = []

    # =====================================================
    # ВИЗНАЧЕННЯ СФЕР
    # =====================================================

    for part in parts:

        # -------------------------------------------------
        # ЗВИЧАЙНИЙ АЛІАС
        # -------------------------------------------------

        sphere_key = SPHERE_ALIASES.get(
            part
        )

        if sphere_key:

            if sphere_key not in selected_spheres:

                selected_spheres.append(
                    sphere_key
                )

            continue

        # -------------------------------------------------
        # ЗЧЕПЛЕНІ ЕМОДЗІ
        #
        # 🧠🎨
        # 🧠🎨💵
        # 💪🧠🎨🤝
        # -------------------------------------------------

        remaining = part
        found_spheres = []

        emoji_aliases = (
            "💪",
            "🧠",
            "🎨",
            "💵",
            "🤝"
        )

        while remaining:

            found = False

            for emoji in emoji_aliases:

                if remaining.startswith(emoji):

                    sphere_key = SPHERE_ALIASES.get(
                        emoji
                    )

                    if (
                        sphere_key
                        and sphere_key not in found_spheres
                    ):

                        found_spheres.append(
                            sphere_key
                        )

                    remaining = remaining[
                        len(emoji):
                    ]

                    found = True

                    break

            if not found:

                break

        # -------------------------------------------------
        # ЕМОДЗІ РОЗІБРАНІ ПОВНІСТЮ
        # -------------------------------------------------

        if (
            found_spheres
            and not remaining
        ):

            for sphere_key in found_spheres:

                if sphere_key not in selected_spheres:

                    selected_spheres.append(
                        sphere_key
                    )

        else:

            unknown_parts.append(
                part
            )

    # =====================================================
    # НЕМАЄ ЖОДНОЇ СФЕРИ
    # =====================================================

    if not selected_spheres:

        bot.send_message(
            message.chat.id,
            (
                "🐜 <b>Генерал Мураха:</b>\n\n"

                "Наказ не розпізнано.\n\n"

                "Спробуй, наприклад:\n"
                "<code>🧠 🎨</code>\n"
                "<code>🧠🎨</code>\n"
                "<code>мудрість творчість</code>\n\n"

                "Обери хоча б одну сферу."
            ),
            parse_mode="HTML",
            reply_markup=get_sphere_selection_keyboard()
        )

        bot.register_next_step_handler(
            message,
            process_expedition_spheres
        )

        return

    # =====================================================
    # Є НЕВІДОМІ ЧАСТИНИ
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
                "<code>🧠 🎨 💵</code>\n"
                "або\n"
                "<code>🧠🎨💵</code>"
            ),
            parse_mode="HTML",
            reply_markup=get_sphere_selection_keyboard()
        )

        bot.register_next_step_handler(
            message,
            process_expedition_spheres
        )

        return

    # =====================================================
    # ПОВТОРНА ПЕРЕВІРКА АКТИВНОЇ ЕКСПЕДИЦІЇ
    # =====================================================

    player = get_player(
        user_id
    )

    active_expedition = get_active_expedition(
        player
    )

    if active_expedition:

        bot.send_message(
            message.chat.id,
            (
                "🐜 <b>Генерал Мураха:</b>\n\n"

                "Стоп!\n\n"

                "Загін уже вирушив у експедицію. "
                "Новий наказ більше не потрібен."
            ),
            parse_mode="HTML",
            reply_markup=get_expedition_menu(
                active_expedition
            )
        )

        return

    # =====================================================
    # СТВОРЕННЯ ЕКСПЕДИЦІЇ
    # =====================================================

    now = datetime.now(
        timezone.utc
    )

    started_at = now.isoformat()

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
            parse_mode="HTML",
            reply_markup=get_quests_menu()
        )

        return

    # =====================================================
    # НАЗВИ СФЕР
    # =====================================================

    spheres_text = "\n".join(
        f"• {SPHERE_NAMES[sphere]}"
        for sphere in selected_spheres
    )

    # =====================================================
    # ДОПОВІДЬ ПРО СТАРТ
    # =====================================================

    text = (
        "🐜 <b>Генерал Мураха доповідає! 🐜</b>\n\n"

        "🧭 <b>Експедицію розпочато.</b>\n\n"

        "Рюкзаки споряджено. Компаси перевірено. "
        "Один солдат знову забув шкарпетки, "
        "але це вже не моя компетенція.\n\n"

        "<b>Сфери експедиції:</b>\n"
        f"{spheres_text}\n\n"

        "⏱️ Таймер уже працює. "
        "Коли загін повернеться, "
        "його час, досвід і знахідки "
        "будуть записані до журналу."
    )

    bot.send_message(
        message.chat.id,
        text,
        parse_mode="HTML",
        reply_markup=get_expedition_menu(
            expedition
        )
    )
