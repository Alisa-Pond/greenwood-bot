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
# КВЕСТИ
# =========================================================

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
#
# completed_history тут НЕ зберігаємо.
# У Supabase такої окремої колонки немає.
# Виконані справи знаходяться в архівах.
# =========================================================

DEFAULT_STATISTICS = {
    "completed_scrolls": 0,
    "completed_rituals": 0,
    "plants_harvested": 0,
    "expeditions_completed": 0,
    "last_summary_date": None
}


# =========================================================
# СТВОРЕННЯ НОВОГО ГРАВЦЯ
# =========================================================

def default_player(user_id):

    return {

        # -------------------------------------------------
        # ІД КОРИСТУВАЧА
        # -------------------------------------------------

        "user_id": str(user_id),

        # -------------------------------------------------
        # РІВЕНЬ
        # -------------------------------------------------

        "level": 1,
        "xp_total": 0.0,

        # -------------------------------------------------
        # ІНВЕНТАР
        # -------------------------------------------------

        "inventory": [],

        # -------------------------------------------------
        # СФЕРИ
        # -------------------------------------------------

        "spheres": copy.deepcopy(
            DEFAULT_SPHERES
        ),

        # -------------------------------------------------
        # АКТИВНІ КВЕСТИ
        # -------------------------------------------------

        "scrolls": [],
        "rituals": [],
        "plants": [],
        "expeditions": [],

        # -------------------------------------------------
        # АРХІВИ
        # -------------------------------------------------

        "plant_archive": [],
        "scroll_archive": [],
        "ritual_archive": [],

        # -------------------------------------------------
        # СТАРА СИСТЕМА QUESTS
        # ЗАЛИШАЄМО ДЛЯ СУМІСНОСТІ
        # -------------------------------------------------

        "quests": copy.deepcopy(
            DEFAULT_QUESTS
        ),

        # -------------------------------------------------
        # ОСНОВНИЙ КВЕСТ
        # -------------------------------------------------

        "main_quest": copy.deepcopy(
            DEFAULT_MAIN_QUEST
        ),

        # -------------------------------------------------
        # СТАТИСТИКА
        # -------------------------------------------------

        "statistics": copy.deepcopy(
            DEFAULT_STATISTICS
        )
    }


# =========================================================
# ОНОВЛЕННЯ ДАНИХ КОРИСТУВАЧА
# =========================================================

def update_player(user_id, player_data):

    """
    Оновлює дані ТІЛЬКИ конкретного користувача.

    user_id використовується як головний ключ:
        .eq("user_id", str(user_id))

    Ніколи не оновлює дані іншого користувача.
    """

    try:

        user_id = str(user_id)

        data = dict(player_data)

        # Не дозволяємо випадково змінити ID.
        data.pop("user_id", None)
        data.pop("id", None)

        response = (
            supabase
            .table("players")
            .update(data)
            .eq("user_id", user_id)
            .execute()
        )

        print(
            f"✅ Дані користувача {user_id} оновлено."
        )

        return True

    except Exception:

        print(
            "❌ ПОМИЛКА update_player:"
        )

        print(
            traceback.format_exc()
        )

        return False


# =========================================================
# ОТРИМАННЯ ГРАВЦЯ
# =========================================================

def get_player(user_id):

    """
    Отримує ТІЛЬКИ запис конкретного користувача.

    Важливо:
        user_id -> str
        Supabase -> .eq("user_id", user_id)

    Отже кожен користувач має власні:
        scrolls
        rituals
        plants
        expeditions
        scroll_archive
        ritual_archive
        plant_archive
        statistics
        spheres
        inventory
    """

    user_id = str(user_id)

    try:

        print(
            f"🔍 Шукаю гравця за ID: {user_id}"
        )

        response = (
            supabase
            .table("players")
            .select("*")
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )

        # =================================================
        # ГРАВЕЦЬ ІСНУЄ
        # =================================================

        if response.data:

            player = response.data[0]

            changed = False


            # -------------------------------------------------
            # ОСНОВНІ ПОЛЯ
            # -------------------------------------------------

            if player.get("inventory") is None:

                player["inventory"] = []

                changed = True


            if player.get("spheres") is None:

                player["spheres"] = copy.deepcopy(
                    DEFAULT_SPHERES
                )

                changed = True


            # -------------------------------------------------
            # АКТИВНІ КВЕСТИ
            # -------------------------------------------------

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


            # -------------------------------------------------
            # АРХІВИ
            # -------------------------------------------------

            archive_columns = [
                "plant_archive",
                "scroll_archive",
                "ritual_archive"
            ]

            for column in archive_columns:

                if player.get(column) is None:

                    player[column] = []

                    changed = True


            # -------------------------------------------------
            # QUESTS
            # -------------------------------------------------

            if player.get("quests") is None:

                player["quests"] = copy.deepcopy(
                    DEFAULT_QUESTS
                )

                changed = True


            # -------------------------------------------------
            # MAIN QUEST
            # -------------------------------------------------

            if player.get("main_quest") is None:

                player["main_quest"] = copy.deepcopy(
                    DEFAULT_MAIN_QUEST
                )

                changed = True


            # -------------------------------------------------
            # STATISTICS
            # -------------------------------------------------

            if player.get("statistics") is None:

                player["statistics"] = copy.deepcopy(
                    DEFAULT_STATISTICS
                )

                changed = True


            # -------------------------------------------------
            # LEVEL / XP
            # -------------------------------------------------

            if player.get("level") is None:

                player["level"] = 1

                changed = True


            if player.get("xp_total") is None:

                player["xp_total"] = 0.0

                changed = True


            # -------------------------------------------------
            # ЯКЩО ДОДАЛИ ВІДСУТНІ ПОЛЯ
            # -------------------------------------------------

            if changed:

                update_player(
                    user_id,
                    {

                        "level":
                            player["level"],

                        "xp_total":
                            player["xp_total"],

                        "inventory":
                            player["inventory"],

                        "spheres":
                            player["spheres"],

                        "quests":
                            player["quests"],

                        "main_quest":
                            player["main_quest"],

                        "statistics":
                            player["statistics"],

                        "scrolls":
                            player["scrolls"],

                        "rituals":
                            player["rituals"],

                        "plants":
                            player["plants"],

                        "expeditions":
                            player["expeditions"],

                        "plant_archive":
                            player["plant_archive"],

                        "scroll_archive":
                            player["scroll_archive"],

                        "ritual_archive":
                            player["ritual_archive"]
                    }
                )


            print(
                f"📖 Гравця {user_id} знайдено."
            )

            return player


        # =================================================
        # НОВИЙ ГРАВЕЦЬ
        # =================================================

        print(
            f"🆕 Гравця {user_id} не знайдено."
        )

        print(
            f"🌱 Створюю нового гравця {user_id}..."
        )

        player = default_player(user_id)

        response = (
            supabase
            .table("players")
            .insert(player)
            .execute()
        )

        print(
            f"✨ Гравця {user_id} успішно створено!"
        )

        if response.data:

            return response.data[0]

        return player


    except Exception:

        print(
            "❌ ПОМИЛКА get_player:"
        )

        print(
            traceback.format_exc()
        )

        # Якщо Supabase тимчасово недоступний,
        # повертаємо локальний шаблон.
        #
        # ВАЖЛИВО:
        # тут також передаємо саме user_id.

        return default_player(user_id)


# =========================================================
# ЗБЕРЕГТИ СУВІЙ
# =========================================================

def save_scroll(user_id, scroll):

    """
    Зберігає сувій конкретного користувача.

    Сувої одного користувача ніколи не змішуються
    із сувоями іншого користувача.
    """

    try:

        user_id = str(user_id)

        player = get_player(user_id)

        scrolls = (
            player.get("scrolls")
            or []
        )

        new_title = str(
            scroll.get("title", "")
        ).strip()

        # -------------------------------------------------
        # ПЕРЕВІРКА ДУБЛЯ
        # -------------------------------------------------

        normalized_new_title = (
            new_title.casefold()
        )

        for existing_scroll in scrolls:

            existing_title = str(
                existing_scroll.get(
                    "title",
                    ""
                )
            ).strip()

            if (
                existing_title.casefold()
                == normalized_new_title
            ):

                print(
                    f"⚠️ Дубль сувою "
                    f"для користувача {user_id}: "
                    f"{new_title}"
                )

                return {
                    "success": False,
                    "duplicate": True,
                    "count": len(scrolls)
                }


        # -------------------------------------------------
        # ДОДАЄМО СУВІЙ
        # -------------------------------------------------

        scrolls.append(
            scroll
        )

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

        print(
            "❌ ПОМИЛКА save_scroll:"
        )

        print(
            traceback.format_exc()
        )

        return {
            "success": False,
            "duplicate": False,
            "count": 0
        }


# =========================================================
# ЗБЕРЕГТИ РИТУАЛ
# =========================================================

def save_ritual(user_id, ritual):

    """
    Додає ритуал конкретному користувачу.
    """

    try:

        user_id = str(user_id)

        player = get_player(user_id)

        rituals = (
            player.get("rituals")
            or []
        )

        rituals.append(
            ritual
        )

        success = update_player(
            user_id,
            {
                "rituals": rituals
            }
        )

        if not success:

            return False

        print(
            f"🔄 Ритуал збережено "
            f"для {user_id}."
        )

        return len(rituals)

    except Exception:

        print(
            "❌ ПОМИЛКА save_ritual:"
        )

        print(
            traceback.format_exc()
        )

        return False


# =========================================================
# ЗБЕРЕГТИ РОСЛИНУ
# =========================================================

def save_plant(user_id, plant):

    """
    Додає рослину конкретному користувачу.
    """

    try:

        user_id = str(user_id)

        player = get_player(user_id)

        plants = (
            player.get("plants")
            or []
        )

        plants.append(
            plant
        )

        success = update_player(
            user_id,
            {
                "plants": plants
            }
        )

        if not success:

            return False

        print(
            f"🌱 Рослину збережено "
            f"для {user_id}."
        )

        return len(plants)

    except Exception:

        print(
            "❌ ПОМИЛКА save_plant:"
        )

        print(
            traceback.format_exc()
        )

        return False


# =========================================================
# ЗБЕРЕГТИ ЕКСПЕДИЦІЮ
# =========================================================

def save_expedition(user_id, expedition):

    """
    Додає експедицію конкретному користувачу.
    """

    try:

        user_id = str(user_id)

        player = get_player(user_id)

        expeditions = (
            player.get("expeditions")
            or []
        )

        expeditions.append(
            expedition
        )

        success = update_player(
            user_id,
            {
                "expeditions": expeditions
            }
        )

        if not success:

            return False

        print(
            f"🧭 Експедицію збережено "
            f"для {user_id}."
        )

        return len(expeditions)

    except Exception:

        print(
            "❌ ПОМИЛКА save_expedition:"
        )

        print(
            traceback.format_exc()
        )

        return False


# =========================================================
# ЗБЕРЕГТИ АРХІВ
# =========================================================

def save_scroll_archive(
    user_id,
    scroll_archive
):

    """
    Повністю зберігає архів сувоїв
    конкретного користувача.
    """

    return update_player(
        str(user_id),
        {
            "scroll_archive":
                scroll_archive
        }
    )


def save_ritual_archive(
    user_id,
    ritual_archive
):

    """
    Повністю зберігає архів ритуалів
    конкретного користувача.
    """

    return update_player(
        str(user_id),
        {
            "ritual_archive":
                ritual_archive
        }
    )


def save_plant_archive(
    user_id,
    plant_archive
):

    """
    Повністю зберігає архів рослин
    конкретного користувача.
    """

    return update_player(
        str(user_id),
        {
            "plant_archive":
                plant_archive
        }
    )


# =========================================================
# ОНОВЛЕННЯ СТАТИСТИКИ
# =========================================================

def update_statistics(
    user_id,
    statistics
):

    """
    Оновлює statistics тільки конкретного користувача.
    """

    return update_player(
        str(user_id),
        {
            "statistics":
                statistics
        }
    )


# =========================================================
# ЗБЕРЕГТИ СТАН ГРАВЦЯ
# =========================================================

def save_player_state(
    user_id,
    player
):

    """
    Зберігає основний стан конкретного користувача.

    Використовуємо, коли потрібно одним UPDATE
    записати кілька змінених колонок.
    """

    user_id = str(user_id)

    return update_player(
        user_id,
        {

            "level":
                player.get(
                    "level",
                    1
                ),

            "xp_total":
                player.get(
                    "xp_total",
                    0.0
                ),

            "inventory":
                player.get(
                    "inventory",
                    []
                ),

            "spheres":
                player.get(
                    "spheres",
                    {}
                ),

            "quests":
                player.get(
                    "quests",
                    DEFAULT_QUESTS
                ),

            "main_quest":
                player.get(
                    "main_quest",
                    DEFAULT_MAIN_QUEST
                ),

            "statistics":
                player.get(
                    "statistics",
                    DEFAULT_STATISTICS
                ),

            "scrolls":
                player.get(
                    "scrolls",
                    []
                ),

            "rituals":
                player.get(
                    "rituals",
                    []
                ),

            "plants":
                player.get(
                    "plants",
                    []
                ),

            "expeditions":
                player.get(
                    "expeditions",
                    []
                ),

            "plant_archive":
                player.get(
                    "plant_archive",
                    []
                ),

            "scroll_archive":
                player.get(
                    "scroll_archive",
                    []
                ),

            "ritual_archive":
                player.get(
                    "ritual_archive",
                    []
                )
        }
    )
