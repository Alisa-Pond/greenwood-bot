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
# =========================================================

DEFAULT_STATISTICS = {
    "completed_scrolls": 0,
    "completed_rituals": 0,
    "plants_harvested": 0,
    "expeditions_completed": 0,
    "last_summary_date": None
}


# =========================================================
# НОВИЙ ГРАВЕЦЬ
# =========================================================

def default_player(user_id):

    return {

        "user_id": str(user_id),

        "level": 1,

        "xp_total": 0.0,

        "inventory": [],

        "spheres": copy.deepcopy(
            DEFAULT_SPHERES
        ),

        # -------------------------------------------------
        # Активні квести
        # -------------------------------------------------

        "scrolls": [],

        "rituals": [],

        "plants": [],

        "expeditions": [],

        # -------------------------------------------------
        # Архіви
        # -------------------------------------------------

        "plant_archive": [],

        "scroll_archive": [],

        "ritual_archive": [],

        # -------------------------------------------------
        # Старий об'єкт quests
        # -------------------------------------------------

        "quests": copy.deepcopy(
            DEFAULT_QUESTS
        ),

        # -------------------------------------------------
        # Основний квест
        # -------------------------------------------------

        "main_quest": copy.deepcopy(
            DEFAULT_MAIN_QUEST
        ),

        # -------------------------------------------------
        # Статистика
        # -------------------------------------------------

        "statistics": copy.deepcopy(
            DEFAULT_STATISTICS
        )
    }


# =========================================================
# ОНОВЛЕННЯ ГРАВЦЯ
# =========================================================

def update_player(user_id, player_data):

    """
    Оновлює дані ТІЛЬКИ конкретного гравця.

    user_id є головним ідентифікатором.
    """

    try:

        user_id = str(user_id)

        data = dict(player_data)

        # -------------------------------------------------
        # Захист службових полів
        # -------------------------------------------------

        data.pop("user_id", None)
        data.pop("id", None)

        if not data:
            return True

        response = (
            supabase
            .table("players")
            .update(data)
            .eq("user_id", user_id)
            .execute()
        )

        print(
            f"✅ Дані гравця {user_id} оновлено."
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
    Отримує РІВНО одного гравця за user_id.

    Якщо гравця немає:
        створює новий рядок.

    Всі дані гравця зберігаються
    в одному рядку Supabase.
    """

    user_id = str(user_id)

    try:

        print(
            f"🔍 Шукаю гравця {user_id}"
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
            # Основні поля
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
            # Активні квести
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
            # Архіви
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
            # Старий quests
            # -------------------------------------------------

            if player.get("quests") is None:

                player["quests"] = copy.deepcopy(
                    DEFAULT_QUESTS
                )

                changed = True


            # -------------------------------------------------
            # Основний квест
            # -------------------------------------------------

            if player.get("main_quest") is None:

                player["main_quest"] = copy.deepcopy(
                    DEFAULT_MAIN_QUEST
                )

                changed = True


            # -------------------------------------------------
            # Статистика
            # -------------------------------------------------

            if player.get("statistics") is None:

                player["statistics"] = copy.deepcopy(
                    DEFAULT_STATISTICS
                )

                changed = True


            # =================================================
            # Якщо якихось даних не було
            # =================================================

            if changed:

                update_player(
                    user_id,
                    {

                        "inventory":
                            player["inventory"],

                        "spheres":
                            player["spheres"],

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
                            player["ritual_archive"],

                        "quests":
                            player["quests"],

                        "main_quest":
                            player["main_quest"],

                        "statistics":
                            player["statistics"]
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
            f"🆕 Створюю нового гравця {user_id}"
        )

        player = default_player(
            user_id
        )

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
            "❌ ПОМИЛКА GET_PLAYER:"
        )

        print(
            traceback.format_exc()
        )

        # -------------------------------------------------
        # Безпечний fallback
        # -------------------------------------------------

        return default_player(
            user_id
        )


# =========================================================
# ЗБЕРЕГТИ СУВІЙ
# =========================================================

def save_scroll(user_id, scroll):

    """
    Додає сувій конкретному користувачу.

    Перевіряє дублікати за назвою.
    """

    try:

        user_id = str(user_id)

        player = get_player(
            user_id
        )

        scrolls = (
            player.get("scrolls")
            or []
        )

        new_title = str(
            scroll.get("title", "")
        ).strip()

        normalized_title = (
            new_title.casefold()
        )

        # -------------------------------------------------
        # Перевірка дубля
        # -------------------------------------------------

        for existing_scroll in scrolls:

            existing_title = str(
                existing_scroll.get(
                    "title",
                    ""
                )
            ).strip()

            if (
                existing_title.casefold()
                == normalized_title
            ):

                print(
                    f"⚠️ Дубль сувою для "
                    f"{user_id}: {new_title}"
                )

                return {

                    "success": False,

                    "duplicate": True,

                    "count": len(scrolls)
                }


        # -------------------------------------------------
        # Додаємо сувій
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

        player = get_player(
            user_id
        )

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

        if success:

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

        return 0


# =========================================================
# ЗБЕРЕГТИ РОСЛИНУ
# =========================================================

def save_plant(user_id, plant):

    """
    Додає рослину конкретному користувачу.
    """

    try:

        user_id = str(user_id)

        player = get_player(
            user_id
        )

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

        if success:

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

        return 0


# =========================================================
# ЗБЕРЕГТИ ЕКСПЕДИЦІЮ
# =========================================================

def save_expedition(
    user_id,
    expedition
):

    """
    Додає експедицію конкретному користувачу.
    """

    try:

        user_id = str(user_id)

        player = get_player(
            user_id
        )

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
                "expeditions":
                    expeditions
            }
        )

        if success:

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

        return 0


# =========================================================
# ДОДАТИ ДО АРХІВУ
# =========================================================

def add_to_archive(
    user_id,
    archive_name,
    item
):

    """
    Універсальне додавання запису
    до архіву конкретного користувача.

    Дозволені архіви:

        scroll_archive
        ritual_archive
        plant_archive
    """

    allowed_archives = {

        "scroll_archive",

        "ritual_archive",

        "plant_archive"
    }

    if archive_name not in allowed_archives:

        raise ValueError(
            f"Недозволений архів: "
            f"{archive_name}"
        )

    try:

        user_id = str(user_id)

        player = get_player(
            user_id
        )

        archive = (
            player.get(
                archive_name
            )
            or []
        )

        archive.append(
            item
        )

        success = update_player(
            user_id,
            {
                archive_name: archive
            }
        )

        return success


    except Exception:

        print(
            "❌ ПОМИЛКА add_to_archive:"
        )

        print(
            traceback.format_exc()
        )

        return False


# =========================================================
# ОНОВИТИ СТАТИСТИКУ
# =========================================================

def update_statistics(
    user_id,
    statistics_updates
):

    """
    Оновлює statistics конкретного користувача,
    не стираючи вже існуючі значення.
    """

    try:

        user_id = str(user_id)

        player = get_player(
            user_id
        )

        statistics = (
            player.get("statistics")
            or {}
        )

        statistics.update(
            statistics_updates
        )

        return update_player(
            user_id,
            {
                "statistics":
                    statistics
            }
        )


    except Exception:

        print(
            "❌ ПОМИЛКА update_statistics:"
        )

        print(
            traceback.format_exc()
        )

        return False


# =========================================================
# ОНОВИТИ ОКРЕМЕ ПОЛЕ
# =========================================================

def update_player_field(
    user_id,
    field,
    value
):

    """
    Безпечне оновлення одного поля
    конкретного користувача.
    """

    allowed_fields = {

        "level",
        "xp_total",
        "inventory",
        "spheres",

        "quests",
        "main_quest",

        "statistics",

        "scrolls",
        "rituals",
        "plants",
        "expeditions",

        "plant_archive",
        "scroll_archive",
        "ritual_archive"
    }

    if field not in allowed_fields:

        raise ValueError(
            f"Недозволене поле: {field}"
        )

    return update_player(
        user_id,
        {
            field: value
        }
    )
