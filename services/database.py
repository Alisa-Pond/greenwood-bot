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
#
# ВАЖЛИВО:
# completed_history НЕ зберігаємо тут.
# Він є окремою колонкою Supabase.
# ==================================================

DEFAULT_STATISTICS = {
    "completed_scrolls": 0,
    "completed_rituals": 0,
    "plants_harvested": 0,
    "expeditions_completed": 0,
    "last_summary_date": None
}


# ==================================================
# ОСНОВНИЙ ШАБЛОН НОВОГО ГРАВЦЯ
# ==================================================

def default_player(user_id):

    return {

        "user_id": str(user_id),

        # ------------------------------------------
        # РІВЕНЬ
        # ------------------------------------------

        "level": 1,
        "xp_total": 0.0,

        # ------------------------------------------
        # ІНВЕНТАР
        # ------------------------------------------

        "inventory": [],

        # ------------------------------------------
        # СФЕРИ
        # ------------------------------------------

        "spheres": copy.deepcopy(
            DEFAULT_SPHERES
        ),

        # ------------------------------------------
        # АКТИВНІ КВЕСТИ
        # ------------------------------------------

        "scrolls": [],
        "rituals": [],
        "plants": [],
        "expeditions": [],

        # ------------------------------------------
        # АРХІВИ
        # ------------------------------------------

        "scroll_archive": [],
        "ritual_archive": [],
        "plant_archive": [],

        # ------------------------------------------
        # ЗАГАЛЬНА ІСТОРІЯ ВИКОНАНИХ СПРАВ
        # ОКРЕМА КОЛОНКА
        # ------------------------------------------

        "completed_history": [],

        # ------------------------------------------
        # СТАРИЙ ОБ'ЄКТ QUESTS
        # ЗАЛИШАЄМО ДЛЯ СУМІСНОСТІ
        # ------------------------------------------

        "quests": copy.deepcopy(
            DEFAULT_QUESTS
        ),

        # ------------------------------------------
        # ОСНОВНИЙ КВЕСТ
        # ------------------------------------------

        "main_quest": copy.deepcopy(
            DEFAULT_MAIN_QUEST
        ),

        # ------------------------------------------
        # СТАТИСТИКА
        # ------------------------------------------

        "statistics": copy.deepcopy(
            DEFAULT_STATISTICS
        )
    }


# ==================================================
# ОНОВИТИ ГРАВЦЯ
# ==================================================

def update_player(user_id, player_data):

    try:

        data = dict(player_data)

        # Ці поля не оновлюємо через UPDATE
        data.pop("user_id", None)
        data.pop("id", None)

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


# ==================================================
# ОТРИМАТИ ГРАВЦЯ
# ==================================================

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

        # ==================================================
        # ГРАВЕЦЬ ВЖЕ ІСНУЄ
        # ==================================================

        if response.data:

            player = response.data[0]

            changed = False

            # ------------------------------------------
            # ОСНОВНІ ПОЛЯ
            # ------------------------------------------

            if player.get("inventory") is None:

                player["inventory"] = []

                changed = True


            if player.get("spheres") is None:

                player["spheres"] = copy.deepcopy(
                    DEFAULT_SPHERES
                )

                changed = True


            # ------------------------------------------
            # КВЕСТИ
            # ------------------------------------------

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


            # ------------------------------------------
            # АРХІВИ
            # ------------------------------------------

            archive_columns = [
                "scroll_archive",
                "ritual_archive",
                "plant_archive"
            ]

            for column in archive_columns:

                if player.get(column) is None:

                    player[column] = []

                    changed = True


            # ------------------------------------------
            # COMPLETED HISTORY
            #
            # ОКРЕМА КОЛОНКА
            # ------------------------------------------

            if player.get(
                "completed_history"
            ) is None:

                player[
                    "completed_history"
                ] = []

                changed = True


            # ------------------------------------------
            # СТАРИЙ QUESTS
            # ------------------------------------------

            if player.get("quests") is None:

                player["quests"] = copy.deepcopy(
                    DEFAULT_QUESTS
                )

                changed = True


            # ------------------------------------------
            # ОСНОВНИЙ КВЕСТ
            # ------------------------------------------

            if player.get("main_quest") is None:

                player["main_quest"] = copy.deepcopy(
                    DEFAULT_MAIN_QUEST
                )

                changed = True


            # ------------------------------------------
            # СТАТИСТИКА
            # ------------------------------------------

            if player.get("statistics") is None:

                player["statistics"] = copy.deepcopy(
                    DEFAULT_STATISTICS
                )

                changed = True


            # ------------------------------------------
            # ЗБЕРІГАЄМО НОВІ ПОЛЯ
            # ------------------------------------------

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

                        "scroll_archive":
                            player["scroll_archive"],

                        "ritual_archive":
                            player["ritual_archive"],

                        "plant_archive":
                            player["plant_archive"],

                        "completed_history":
                            player["completed_history"],

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


        # ==================================================
        # НОВИЙ ГРАВЕЦЬ
        # ==================================================

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

        # Навіть при тимчасовій проблемі
        # Supabase бот не падає.

        return default_player(user_id)


# ==================================================
# ЗБЕРЕГТИ СУВІЙ
# ==================================================

def save_scroll(user_id, scroll):

    """
    Додає новий сувій у scrolls.

    Не дозволяє створити два активні сувої
    з однаковою назвою.
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

        normalized_new_title = (
            new_title.casefold()
        )

        # ------------------------------------------
        # ДУБЛЬ
        # ------------------------------------------

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


        # ------------------------------------------
        # ДОДАВАННЯ
        # ------------------------------------------

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


# ==================================================
# ЗБЕРЕГТИ РИТУАЛ
# ==================================================

def save_ritual(user_id, ritual):

    try:

        player = get_player(user_id)

        rituals = (
            player.get("rituals")
            or []
        )

        rituals.append(ritual)

        success = update_player(
            user_id,
            {
                "rituals": rituals
            }
        )

        if not success:

            return False

        print(
            f"🔄 Ритуал збережено для {user_id}."
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
