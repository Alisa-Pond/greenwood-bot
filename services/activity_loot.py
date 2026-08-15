import random


# =========================================================
# НАЛАШТУВАННЯ ЛУТУ
# =========================================================

LOOT_CHANCE = 0.003

POSSIBLE_LOOT = [
    "🧪 Настій Бадьорості",
    "📜 Стародавній Сувій",
    "💎 Кристал Натхнення",
    "🔑 Мідний Ключ"
]


# =========================================================
# ВИПАДАННЯ ЛУТУ
# =========================================================

def try_get_loot(player):
    """
    Перевіряє шанс випадіння луту.

    Якщо лут випав:
        додає його до інвентарю
        повертає назву предмета.

    Якщо не випав:
        повертає None.
    """

    if random.random() > LOOT_CHANCE:
        return None

    if not POSSIBLE_LOOT:
        return None

    loot = random.choice(POSSIBLE_LOOT)

    inventory = player.get("inventory") or []

    if not isinstance(inventory, list):
        inventory = []

    inventory.append(loot)

    player["inventory"] = inventory

    return loot
