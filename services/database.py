import copy
import traceback

from services.config import supabase


# ==================================================
# СФЕРИ
# ==================================================

DEFAULT_SPHERES = {

    "health": {
        "name": "💪 Здоров'я",
        "emoji": "💪",
        "lvl": 1,
        "xp": 0.0,
        "max_xp": 10.0
    },

    "wisdom": {
        "name": "🧠 Мудрість",
        "emoji": "🧠",
        "lvl": 1,
        "xp": 0.0,
        "max_xp": 10.0
    },

    "art": {
        "name": "🎨 Творчість",
        "emoji": "🎨",
        "lvl": 1,
        "xp": 0.0,
        "max_xp": 10.0
    },

    "finance": {
        "name": "💵 Фінанси",
        "emoji": "💵",
        "lvl": 1,
        "xp": 0.0,
        "max_xp": 10.0
    },

    "relations": {
        "name": "🤝 Зв'язки",
        "emoji": "🤝",
        "lvl": 1,
        "xp": 0.0,
        "max_xp": 10.0
    }

}


# ==================================================
# МОЇ КВЕСТИ
# ==================================================

DEFAULT_QUESTS = {

    "scrolls": [],

    "rituals": [],

    "plants": [],

    "expeditions": []

}


# ==================================================
# ОСНОВНИЙ КВЕСТ
# ==================================================

DEFAULT_MAIN_QUEST = {

    "chapter": 1,

    "current_task": None,

    "completed": []

}


# ==================================================
# СТАТИСТИКА
# ==================================================

DEFAULT_STATISTICS = {

    "completed_scrolls": 0,

    "completed_rituals": 0,

    "plants_harvested": 0,

    "expeditions_completed": 0

}


# ==================================================
# ШАБЛОН НОВОГО ГРАВЦЯ
# ==================================================

def default_player(user_id):

    return {

        "user_id": str(user_id),

        "level": 1,

        "xp_total": 0.0,

        "inventory": [],

        "spheres": copy.deepcopy(DEFAULT_SPHERES),

        "quests": copy.deepcopy(DEFAULT_QUESTS),

        "main_quest": copy.deepcopy(DEFAULT_MAIN_QUEST),

        "statistics": copy.deepcopy(DEFAULT_STATISTICS)

    }


# ==================================================
# ОНОВИТИ ГРАВЦЯ
# ==================================================

def update_player(user_id, player):

    try:

        data = dict(player)

        data.pop("user_id", None)

        data.pop("id", None)

        (
            supabase
            .table("players")
            .update(data)
            .eq("user_id", str(user_id))
            .execute()
        )

    except Exception:

        print(traceback.format_exc())


# ==================================================
# ОТРИМАТИ ГРАВЦЯ
# ==================================================

def get_player(user_id):

    user_id = str(user_id)

    try:

        response = (

            supabase

            .table("players")

            .select("*")

            .eq("user_id", user_id)

            .execute()

        )

        # -------------------------
        # Уже існує
        # -------------------------

        if response.data:

            player = response.data[0]

            changed = False

            if "inventory" not in player:

                player["inventory"] = []
                changed = True

            if "spheres" not in player:

                player["spheres"] = copy.deepcopy(DEFAULT_SPHERES)
                changed = True

            if "quests" not in player:

                player["quests"] = copy.deepcopy(DEFAULT_QUESTS)
                changed = True

            if "main_quest" not in player:

                player["main_quest"] = copy.deepcopy(DEFAULT_MAIN_QUEST)
                changed = True

            if "statistics" not in player:

                player["statistics"] = copy.deepcopy(DEFAULT_STATISTICS)
                changed = True

            if changed:

                update_player(user_id, player)

            return player

        # -------------------------
        # Новий гравець
        # -------------------------

        player = default_player(user_id)

        (

            supabase

            .table("players")

            .insert(player)

            .execute()

        )

        print(f"✨ Створено нового гравця {user_id}")

        return player

    except Exception:

        print(traceback.format_exc())

        return default_player(user_id)
