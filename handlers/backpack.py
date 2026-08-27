from services.config import bot
from services.database import get_player
from services.loot import (
    LOOT_ITEMS,
    RARITY_NAMES,
)


print("⚙️ Реєструємо хендлер рюкзака...")


# =========================================================
# ПОШУК ПРЕДМЕТА ЗА НАЗВОЮ
# =========================================================

def find_item_by_name(item_name):

    if not item_name:
        return None

    item_name = str(
        item_name
    ).strip()

    for item_id, item_data in LOOT_ITEMS.items():

        if item_data.get(
            "name"
        ) == item_name:

            return item_data

    return None


# =========================================================
# РОЗБІР ПРЕДМЕТА З РЮКЗАКА
# =========================================================
#
# Підтримує:
#
# "🌿 Срібляста водорість × 3"
#
# та старий формат:
#
# "🌿 Срібляста водорість"
#
# =========================================================

def parse_inventory_item(raw_item):

    if not raw_item:
        return None, 0

    raw_item = str(
        raw_item
    ).strip()

    # -----------------------------------------------------
    # НОВИЙ ФОРМАТ
    #
    # "🌿 Срібляста водорість × 3"
    # -----------------------------------------------------

    if " × " in raw_item:

        name, quantity = (
            raw_item.rsplit(
                " × ",
                1
            )
        )

        name = name.strip()

        try:

            quantity = int(
                quantity
            )

        except (
            TypeError,
            ValueError
        ):

            quantity = 1

        return name, quantity

    # -----------------------------------------------------
    # СТАРИЙ ФОРМАТ
    #
    # "🌿 Срібляста водорість"
    # -----------------------------------------------------

    return raw_item, 1


# =========================================================
# НОРМАЛІЗАЦІЯ ІНВЕНТАРЮ
# =========================================================
#
# На виході завжди:
#
# {
#     "🌿 Срібляста водорість": 3,
#     "🐚 Райдужна мушля": 2
# }
#
# =========================================================

def normalize_inventory(inventory):

    counts = {}

    # -----------------------------------------------------
    # НОВИЙ ФОРМАТ
    #
    # {
    #     "rainbow_shell": 3
    # }
    #
    # Теоретично підтримуємо його теж.
    # -----------------------------------------------------

    if isinstance(
        inventory,
        dict
    ):

        for item, quantity in inventory.items():

            try:

                quantity = int(
                    quantity
                )

            except (
                TypeError,
                ValueError
            ):

                quantity = 1

            # -------------------------------------------------
            # Якщо ключ є ID предмета
            # -------------------------------------------------

            item_data = LOOT_ITEMS.get(
                str(item)
            )

            if item_data:

                name = item_data.get(
                    "name"
                )

            else:

                # ---------------------------------------------
                # Якщо ключ уже є назвою
                # ---------------------------------------------

                name = str(
                    item
                ).strip()

            if not name or quantity <= 0:
                continue

            counts[name] = (
                counts.get(
                    name,
                    0
                )
                + quantity
            )

        return counts

    # -----------------------------------------------------
    # СПИСОК
    # -----------------------------------------------------

    if isinstance(
        inventory,
        list
    ):

        for raw_item in inventory:

            name, quantity = (
                parse_inventory_item(
                    raw_item
                )
            )

            if not name:
                continue

            if quantity <= 0:
                continue

            counts[name] = (
                counts.get(
                    name,
                    0
                )
                + quantity
            )

        return counts

    return {}


# =========================================================
# ФОРМАТУВАННЯ РІДКІСНОСТІ
# =========================================================

def get_rarity_name(item_data):

    rarity = item_data.get(
        "rarity",
        "common"
    )

    return RARITY_NAMES.get(
        rarity,
        rarity
    )


# =========================================================
# РЮКЗАК
# =========================================================

@bot.message_handler(
    func=lambda message:
        message.text == "🎒 Рюкзак"
)
def show_inventory(message):

    user_id = str(
        message.from_user.id
    )

    current_player = get_player(
        user_id
    )

    if not current_player:

        bot.send_message(
            message.chat.id,
            (
                "🎒 Не вдалося відкрити "
                "твій рюкзак."
            ),
            parse_mode="HTML"
        )

        return

    inventory = current_player.get(
        "inventory",
        []
    )

    # =====================================================
    # НОРМАЛІЗУЄМО ІНВЕНТАР
    # =====================================================

    items_counts = normalize_inventory(
        inventory
    )

    # =====================================================
    # ПОРОЖНІЙ РЮКЗАК
    # =====================================================

    if not items_counts:

        bot.send_message(
            message.chat.id,
            (
                "🎒 <b>Твій рюкзак порожній.</b>\n\n"
                "Можливо, час вирушити на пошуки "
                "чогось цікавого? 🐜"
            ),
            parse_mode="HTML"
        )

        return

    # =====================================================
    # ФОРМУЄМО РЮКЗАК
    # =====================================================

    lines = [
        "🎒 <b>Вміст твого рюкзака:</b>"
    ]

    for item_name, quantity in (
        items_counts.items()
    ):

        # -------------------------------------------------
        # ЗНАХОДИМО ПРЕДМЕТ У КАТАЛОЗІ
        # -------------------------------------------------

        item_data = find_item_by_name(
            item_name
        )

        # -------------------------------------------------
        # ЯКЩО ПРЕДМЕТ Є В КАТАЛОЗІ
        # -------------------------------------------------

        if item_data:

            description = item_data.get(
                "description",
                "Опис відсутній."
            )

            rarity_name = get_rarity_name(
                item_data
            )

        # -------------------------------------------------
        # ЯКЩО ПРЕДМЕТА НЕМАЄ В КАТАЛОЗІ
        # -------------------------------------------------

        else:

            description = (
                "Інформація про цей предмет "
                "відсутня в каталозі."
            )

            rarity_name = (
                "невідома"
            )

        # -------------------------------------------------
        # КІЛЬКІСТЬ
        # -------------------------------------------------

        lines.append(
            ""
        )

        lines.append(
            f"<b>{item_name}</b> × {quantity}"
        )

        lines.append(
            f"- {description}"
        )

        lines.append(
            f"- Рідкісність: {rarity_name}"
        )

    # =====================================================
    # НАДСИЛАЄМО
    # =====================================================

    bot.send_message(
        message.chat.id,
        "\n".join(
            lines
        ),
        parse_mode="HTML"
    )
