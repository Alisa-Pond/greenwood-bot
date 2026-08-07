import traceback
import copy

from services.config import supabase


# =========================
# Дані нового гравця
# =========================

DEFAULT_QUESTS = {
    "scrolls": [],        # 📜 Сувої
    "rituals": [],        # 🕯 Ритуали
    "plants": [],     # 🌱 Теплиця
    "expeditions": []     # 🧭 Експедиції
}


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


DEFAULT_STATISTICS = {
    "completed_tasks": 0,
    "completed_rituals": 0,
    "plants_harvested": 0,
    "expeditions_completed": 0
}


# =========================
# Оновлення гравця
# =========================

def update_player(user_id, player_data):

    try:
        user_id = str(user_id)

        data_to_update = {
            key: value
            for key, value in player_data.items()
            if key != "id"
        }

        supabase.table("players")\
            .update(data_to_update)\
            .eq("user_id", user_id)\
            .execute()

        print(f"✅ Дані гравця {user_id} оновлено.")

    except Exception:

        print("❌ ПОМИЛКА update_player:")
        print(traceback.format_exc())



# =========================
# Отримати гравця
# =========================

def get_player(user_id):

    user_id = str(user_id)


    fallback_player = {

        "user_id": user_id,

        "level": 1,
        "xp_total": 0.0,

        "inventory": [],

        "spheres": copy.deepcopy(DEFAULT_SPHERES),

        "quests": copy.deepcopy(DEFAULT_QUESTS),

        "statistics": copy.deepcopy(DEFAULT_STATISTICS)

    }


    try:

        print(f"🔍 Шукаю гравця {user_id}")

        response = (
            supabase
            .table("players")
            .select("*")
            .eq("user_id", user_id)
            .execute()
        )


        # =========================
        # Існуючий гравець
        # =========================

        if response.data:

            player = response.data[0]

            updated = False


            if not player.get("quests"):

                player["quests"] = copy.deepcopy(DEFAULT_QUESTS)
                updated = True

            else:

                for key in DEFAULT_QUESTS:

                    if key not in player["quests"]:

                        player["quests"][key] = []

                        updated = True



            if not player.get("statistics"):

                player["statistics"] = copy.deepcopy(DEFAULT_STATISTICS)

                updated = True



            if updated:

                update_player(user_id, player)


            return player



        # =========================
        # Новий гравець
        # =========================

        print(f"🆕 Створюю нового гравця {user_id}")


        new_player = {

            "user_id": user_id,

            "level": 1,

            "xp_total": 0.0,

            "inventory": [],

            "spheres": copy.deepcopy(DEFAULT_SPHERES),

            "quests": copy.deepcopy(DEFAULT_QUESTS),

            "statistics": copy.deepcopy(DEFAULT_STATISTICS)

        }


        supabase.table("players")\
            .insert(new_player)\
            .execute()


        print("✨ Гравця створено!")

        return new_player



    except Exception:

        print("❌ ПОМИЛКА GET_PLAYER:")
        print(traceback.format_exc())

        return fallback_player
