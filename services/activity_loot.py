import random

from services.database import update_player


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
    Перевіряє, чи випаде випадковий лут.

    Повертає назву предмета, якщо лут випав.
    Якщо не випав — повертає None.
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


# =========================================================
# ЗБЕРЕЖЕННЯ ЛУТУ
# =========================================================

def save_loot(user_id, player):
    """
    Зберігає інвентар гравця в Supabase.
    """

    update_player(
        str(user_id),
        {
            "inventory": player.get("inventory") or []
        }
    )
