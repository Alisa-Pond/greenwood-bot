import copy
import traceback

from services.config import supabase


# =========================================================
# СФЕРИ
# =========================================================

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


# =========================================================
# МОЇ КВЕСТИ
# =========================================================

# Старий загальний контейнер.
# Поки залишаємо для сумісності з таблицею.
DEFAULT_QUESTS = {
    "scrolls": [],
    "rituals": [],
    "plants": [],
    "expeditions": []
}


# =========================================================
# ОСНОВНИЙ КВЕСТ
# =========================================================

DEFAULT_MAIN_QUEST = {
    "chapter": 1,
    "current_task": None,
    "completed": []
}


# =========================================================
# СТАТИСТИКА
# =========================================================

DEFAULT_STATISTICS = {
    "completed_scrolls": 0,
    "completed_rituals": 0,
    "plants_harvested": 0,
    "expeditions_completed": 0
}


# =========================================================
# ШАБЛОН НОВОГО ГРАВЦЯ
# =========================================================

def default_player(user_id):

    return {
        "user_id": str(user_id),

        # Загальний прогрес
        "level": 1,
        "xp_total": 0.0,

        # Рюкзак
        "inventory": [],

        # П'ять сфер персонажа
        "spheres": copy.deepcopy(DEFAULT_SPHERES),

        # Окремі розділи "Моїх квестів"
        "scrolls": [],
        "rituals": [],
        "plants": [],
        "expeditions": [],

        # Основний квест
        "main_quest": copy.deepcopy(DEFAULT_MAIN_QUEST),

        # Поки залишаємо для сумісності
        "quests": copy.deepcopy(DEFAULT_QUESTS),

        # Статистика
        "statistics": copy.deepcopy(DEFAULT_STATISTICS)
    }


# =========================================================
# ОНОВИТИ ГРАВЦЯ
# =========================================================

def update_player(user_id, player):

    try:

        data = dict(player)

        # Ці поля не потрібно передавати в UPDATE
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

    except Exception:

        print("❌ ПОМИЛКА update_player:")

        print(traceback.format_exc())


# =========================================================
# ОТРИМАТИ ГРАВЦЯ
# =========================================================

def get_player(user_id):

    user_id = str(user_id)

    try:

        print(f"🔍 Шукаю гравця {user_id} у Supabase...")

        response = (
            supabase
            .table("players")
            .select("*")
            .eq("user_id", user_id)
            .execute()
        )

        # =================================================
        # ГРАВЕЦЬ ВЖЕ ІСНУЄ
        # =================================================

        if response.data:

            player = response.data[0]

            print(f"📖 Гравця {user_id} знайдено.")

            changed = False

            # -------------------------------------------------
            # Рюкзак
            # -------------------------------------------------

            if player.get("inventory") is None:

                player["inventory"] = []

                changed = True

            # -------------------------------------------------
            # Сфери
            # -------------------------------------------------

            if not player.get("spheres"):

                player["spheres"] = copy.deepcopy(
                    DEFAULT_SPHERES
                )

                changed = True

            # -------------------------------------------------
            # Сувої
            # -------------------------------------------------

            if player.get("scrolls") is None:

                player["scrolls"] = []

                changed = True

            # -------------------------------------------------
            # Ритуали
            # -------------------------------------------------

            if player.get("rituals") is None:

                player["rituals"] = []

                changed = True

            # -------------------------------------------------
            # Рослини
            # -------------------------------------------------

            if player.get("plants") is None:

                player["plants"] = []

                changed = True

            # -------------------------------------------------
            # Експедиції
            # -------------------------------------------------

            if player.get("expeditions") is None:

                player["expeditions"] = []

                changed = True

            # -------------------------------------------------
            # Основний квест
            # -------------------------------------------------

            if not player.get("main_quest"):

                player["main_quest"] = copy.deepcopy(
                    DEFAULT_MAIN_QUEST
                )

                changed = True

            # -------------------------------------------------
            # Старий контейнер quests
            # -------------------------------------------------

            if not player.get("quests"):

                player["quests"] = copy.deepcopy(
                    DEFAULT_QUESTS
                )

                changed = True

            # -------------------------------------------------
            # Статистика
            # -------------------------------------------------

            if not player.get("statistics"):

                player["statistics"] = copy.deepcopy(
                    DEFAULT_STATISTICS
                )

                changed = True

            # -------------------------------------------------
            # Якщо щось було відсутнє, оновлюємо базу
            # -------------------------------------------------

            if changed:

                update_player(
                    user_id,
                    player
                )

            return player

        # =================================================
        # ГРАВЦЯ НЕМАЄ
        # =================================================

        print(
            f"🆕 Гравця {user_id} не знайдено. "
            f"Створюю нового..."
        )

        player = default_player(user_id)

        response = (
            supabase
            .table("players")
            .insert(player)
            .execute()
        )

        print(
            f"✨ Нового гравця {user_id} "
            f"успішно створено в Supabase!"
        )

        return player

    except Exception:

        print("❌ ПОМИЛКА GET_PLAYER:")

        print(traceback.format_exc())

        # Навіть якщо Supabase тимчасово недоступний,
        # бот отримає правильну структуру персонажа.
        return default_player(user_id)


# =========================================================
# ЗБЕРЕГТИ СУВІЙ
# =========================================================

def save_scroll(user_id, scroll):

    player = get_player(user_id)

    scrolls = player.get("scrolls") or []

    scrolls.append(scroll)

    update_player(
        user_id,
        {
            "scrolls": scrolls
        }
    )

    print(
        f"📜 Новий сувій збережено "
        f"для гравця {user_id}."
    )

    return len(scrolls)
