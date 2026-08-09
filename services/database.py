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

DEFAULT_PLANT_ARCHIVE = []
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
    "expeditions_completed": 0,
    "completed_history": [],
    "last_summary_date": None
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

        # Окремі колонки Supabase
        "scrolls": [],
        "rituals": [],
        "plants": [],
        "expeditions": [],

        "scroll_archive": [],
        "ritual_archive": [],
        "plant_archive": [],


        "quests": copy.deepcopy(DEFAULT_QUESTS),

        "main_quest": copy.deepcopy(DEFAULT_MAIN_QUEST),

        "statistics": copy.deepcopy(DEFAULT_STATISTICS)
    }


# ==================================================
# ОНОВИТИ ГРАВЦЯ
# ==================================================

def update_player(user_id, player_data):

    try:

        data = dict(player_data)

        # Ці поля не повинні оновлюватися через UPDATE
        data.pop("user_id", None)
        data.pop("id", None)

        (
            supabase
            .table("players")
            .update(data)
            .eq("user_id", str(user_id))
            .execute()
        )

        print(f"✅ Дані гравця {user_id} оновлено.")

        return True

    except Exception:

        print("❌ ПОМИЛКА update_player:")
        print(traceback.format_exc())

        return False


# ==================================================
# ОТРИМАТИ ГРАВЦЯ
# ==================================================

def get_player(user_id):

    user_id = str(user_id)

    try:

        print(f"🔍 Шукаю гравця {user_id}")

        response = (
            supabase
            .table("players")
            .select("*")
            .eq("user_id", user_id)
            .execute()
        )

        # ==================================================
        # ГРАВЕЦЬ ВЖЕ ІСНУЄ
        # ==================================================

        if response.data:

            player = response.data[0]

            changed = False


            # -------------------------
            # Основні поля
            # -------------------------

            if player.get("inventory") is None:
                player["inventory"] = []
                changed = True

            if player.get("spheres") is None:
                player["spheres"] = copy.deepcopy(DEFAULT_SPHERES)
                changed = True


            # -------------------------
            # Окремі колонки квестів
            # -------------------------

            quest_columns = [
                "scrolls",
                "rituals",
                "plants",
                "expeditions"
            ]

            for column in quest_columns:

                if player.get(column) is None:

                    player[column] = []

                    changed = True


            # -------------------------
            # Старий об'єкт quests
            # Залишаємо для сумісності
            # -------------------------

            if player.get("quests") is None:

                player["quests"] = copy.deepcopy(DEFAULT_QUESTS)

                changed = True


            # -------------------------
            # Основний квест
            # -------------------------

            if player.get("main_quest") is None:

                player["main_quest"] = copy.deepcopy(
                    DEFAULT_MAIN_QUEST
                )

                changed = True


            # -------------------------
            # Статистика
            # -------------------------

            if player.get("statistics") is None:

                player["statistics"] = copy.deepcopy(
                    DEFAULT_STATISTICS
                )

                changed = True


            # -------------------------
            # Якщо щось додали
            # -------------------------

            if changed:

                update_player(
                    user_id,
                    {
                        "inventory": player["inventory"],
                        "spheres": player["spheres"],
                        "scrolls": player["scrolls"],
                        "rituals": player["rituals"],
                        "plants": player["plants"],
                        "expeditions": player["expeditions"],
                        "quests": player["quests"],
                        "main_quest": player["main_quest"],
                        "statistics": player["statistics"]
                    }
                )


            print(f"📖 Гравця {user_id} знайдено.")

            return player


        # ==================================================
        # НОВИЙ ГРАВЕЦЬ
        # ==================================================

        print(f"🆕 Створюю нового гравця {user_id}")

        player = default_player(user_id)

        response = (
            supabase
            .table("players")
            .insert(player)
            .execute()
        )

        print(f"✨ Гравця {user_id} успішно створено!")

        # Якщо Supabase повернув створений запис,
        # використовуємо саме його
        if response.data:

            return response.data[0]

        return player


    except Exception:

        print("❌ ПОМИЛКА GET_PLAYER:")
        print(traceback.format_exc())

        # Навіть якщо Supabase тимчасово недоступний,
        # бот не повинен падати
        return default_player(user_id)


# ==================================================
# ЗБЕРЕГТИ СУВІЙ
# ==================================================

def save_scroll(user_id, scroll):

    """
    Додає новий сувій у колонку scrolls.

    Перевіряє, чи немає активного сувою
    з такою самою назвою.

    Повертає словник:

    {
        "success": True / False,
        "duplicate": True / False,
        "count": кількість активних сувоїв
    }
    """

    try:

        user_id = str(user_id)

        player = get_player(user_id)

        scrolls = player.get("scrolls") or []

        new_title = str(
            scroll.get("title", "")
        ).strip()

        # ==================================================
        # ПЕРЕВІРКА НА ДУБЛЬ
        # ==================================================

        normalized_new_title = new_title.casefold()

        for existing_scroll in scrolls:

            existing_title = str(
                existing_scroll.get("title", "")
            ).strip()

            if existing_title.casefold() == normalized_new_title:

                print(
                    f"⚠️ Дубль сувою для {user_id}: "
                    f"{new_title}"
                )

                return {
                    "success": False,
                    "duplicate": True,
                    "count": len(scrolls)
                }


        # ==================================================
        # ДОДАВАННЯ СУВОЮ
        # ==================================================

        scrolls.append(scroll)

        success = update_player(
            user_id,
            {
                "scrolls": scrolls
            }
        )


        if not success:

            return {
                "success": False,
                "duplicate": False,
                "count": len(scrolls) - 1
            }


        print(
            f"📜 Сувій '{new_title}' "
            f"збережено для {user_id}."
        )

        return {
            "success": True,
            "duplicate": False,
            "count": len(scrolls)
        }


    except Exception:

        print("❌ ПОМИЛКА save_scroll:")
        print(traceback.format_exc())

        return {
            "success": False,
            "duplicate": False,
            "count": 0
        }

def save_ritual(user_id, ritual):

    player = get_player(user_id)

    rituals = player.get("rituals") or []

    rituals.append(ritual)

    update_player(
        user_id,
        {
            "rituals": rituals
        }
    )

    return len(rituals)
