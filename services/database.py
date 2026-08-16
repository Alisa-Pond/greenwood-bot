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

        # -------------------------------------------------
        # РІВЕНЬ ПЕРСОНАЖА
        # -------------------------------------------------
        #
        # Поточний рівень:
        "level": 1,

        # XP, накопичений у поточному рівні:
        "level_xp": 0.0,

        # XP, необхідний для наступного рівня:
        "level_max_xp": 10.0,

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

        "scroll_archive": [],
        "ritual_archive": [],
        "plant_archive": [],

        # -------------------------------------------------
        # СТАРЕ ПОЛЕ QUESTS
        # -------------------------------------------------
        #
        # Залишаємо для сумісності зі старим кодом.
        #

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
# ОНОВЛЕННЯ ГРАВЦЯ
# =========================================================

def update_player(user_id, player_data):

    try:

        data = dict(player_data)

        # Не оновлюємо ідентифікатори
        data.pop("user_id", None)
        data.pop("id", None)

        # Старе поле загального XP більше не використовується.
        # Якщо якийсь старий handler випадково передасть його,
        # не дозволяємо йому потрапити в Supabase.
        data.pop("xp_total", None)

        (
            supabase
            .table("players")
            .update(data)
            .eq("user_id", str(user_id))
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
# ОТРИМАТИ ГРАВЦЯ
# =========================================================

def get_player(user_id):

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
            .execute()
        )

        # =====================================================
        # ГРАВЕЦЬ ІСНУЄ
        # =====================================================

        if response.data:

            player = response.data[0]

            changed = False

            # -------------------------------------------------
            # РІВЕНЬ ПЕРСОНАЖА
            # -------------------------------------------------

            if player.get("level") is None:

                player["level"] = 1
                changed = True

            if player.get("level_xp") is None:

                player["level_xp"] = 0.0
                changed = True

            if player.get("level_max_xp") is None:

                player["level_max_xp"] = 10.0
                changed = True

            # -------------------------------------------------
            # ІНВЕНТАР
            # -------------------------------------------------

            if player.get("inventory") is None:

                player["inventory"] = []

                changed = True

            # -------------------------------------------------
            # СФЕРИ
            # -------------------------------------------------

            if player.get("spheres") is None:

                player["spheres"] = copy.deepcopy(
                    DEFAULT_SPHERES
                )

                changed = True

            # -------------------------------------------------
            # АКТИВНІ КВЕСТИ
            # -------------------------------------------------

            for column in (
                "scrolls",
                "rituals",
                "plants",
                "expeditions"
            ):

                if player.get(column) is None:

                    player[column] = []

                    changed = True

            # -------------------------------------------------
            # АРХІВИ
            # -------------------------------------------------

            for column in (
                "scroll_archive",
                "ritual_archive",
                "plant_archive"
            ):

                if player.get(column) is None:

                    player[column] = []

                    changed = True

            # -------------------------------------------------
            # СТАРИЙ QUESTS
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

            else:

                statistics = player["statistics"]

                if not isinstance(
                    statistics,
                    dict
                ):

                    statistics = {}

                statistics_changed = False

                for key, default_value in (
                    DEFAULT_STATISTICS.items()
                ):

                    if key not in statistics:

                        statistics[key] = copy.deepcopy(
                            default_value
                        )

                        statistics_changed = True

                if statistics_changed:

                    player["statistics"] = statistics

                    changed = True

            # -------------------------------------------------
            # ЗБЕРІГАЄМО ДОДАНІ ПОЛЯ
            # -------------------------------------------------

            if changed:

                update_player(
                    user_id,
                    {
                        "level": player["level"],
                        "level_xp": player["level_xp"],
                        "level_max_xp": player["level_max_xp"],

                        "inventory": player["inventory"],

                        "spheres": player["spheres"],

                        "scrolls": player["scrolls"],
                        "rituals": player["rituals"],
                        "plants": player["plants"],
                        "expeditions": player["expeditions"],

                        "scroll_archive": player[
                            "scroll_archive"
                        ],

                        "ritual_archive": player[
                            "ritual_archive"
                        ],

                        "plant_archive": player[
                            "plant_archive"
                        ],

                        "quests": player["quests"],

                        "main_quest": player[
                            "main_quest"
                        ],

                        "statistics": player[
                            "statistics"
                        ]
                    }
                )

            print(
                f"📖 Гравця {user_id} знайдено."
            )

            return player

        # =====================================================
        # НОВИЙ ГРАВЕЦЬ
        # =====================================================

        print(
            f"🆕 Створюю нового гравця {user_id}"
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
            "❌ ПОМИЛКА GET_PLAYER:"
        )

        print(
            traceback.format_exc()
        )

        return default_player(user_id)


# =========================================================
# ОТРИМАТИ ВСІХ ГРАВЦІВ
# =========================================================

def get_all_players():

    try:

        response = (
            supabase
            .table("players")
            .select("*")
            .execute()
        )

        return response.data or []

    except Exception:

        print(
            "❌ ПОМИЛКА get_all_players:"
        )

        print(
            traceback.format_exc()
        )

        return []


# =========================================================
# ЗБЕРЕГТИ СУВІЙ
# =========================================================

def save_scroll(user_id, scroll):

    try:

        user_id = str(user_id)

        player = get_player(user_id)

        scrolls = player.get(
            "scrolls"
        ) or []

        new_title = str(
            scroll.get("title", "")
        ).strip()

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
                    f"⚠️ Дубль сувою для "
                    f"{user_id}: {new_title}"
                )

                return {
                    "success": False,
                    "duplicate": True,
                    "count": len(scrolls)
                }

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

    try:

        user_id = str(user_id)

        player = get_player(user_id)

        rituals = player.get(
            "rituals"
        ) or []

        rituals.append(ritual)

        success = update_player(
            user_id,
            {
                "rituals": rituals
            }
        )

        if not success:

            return 0

        return len(rituals)

    except Exception:

        print(
            "❌ ПОМИЛКА save_ritual:"
        )

        print(
            traceback.format_exc()
        )

        return 0
