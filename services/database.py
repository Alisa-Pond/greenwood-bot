import traceback
from services.config import supabase

# Шаблон за замовчуванням для створення нового гравця
DEFAULT_QUESTS = {
    "scrolls": [],    # Одноразові та накопичувальні сувої
    "rituals": [],    # Щоденні ритуали
    "plants": []      # Магічне насіння в Теплиці
}

DEFAULT_SPHERES = {
    "health": {"name": "💪 Здоров'я", "emoji": "💪", "lvl": 1, "xp": 0.0, "max_xp": 10.0},
    "wisdom": {"name": "🧠 Мудрість", "emoji": "🧠", "lvl": 1, "xp": 0.0, "max_xp": 10.0},
    "art": {"name": "🎨 Творчість", "emoji": "🎨", "lvl": 1, "xp": 0.0, "max_xp": 10.0},
    "finance": {"name": "💵 Фінанси", "emoji": "💵", "lvl": 1, "xp": 0.0, "max_xp": 10.0},
    "relations": {"name": "🤝 Зв'язки", "emoji": "🤝", "lvl": 1, "xp": 0.0, "max_xp": 10.0}
}


def update_player(user_id, player_data):
    """Оновлює дані гравця в базі Supabase."""
    try:
        user_id = str(user_id)
        # Видаляємо id з оновлення, якщо воно там є, щоб Supabase не повертав помилку
        data_to_update = {k: v for k, v in player_data.items() if k != 'id'}
        supabase.table("players").update(data_to_update).eq("user_id", user_id).execute()
        print(f"✅ Дані гравця {user_id} оновлено в Supabase.")
    except Exception:
        print(f"❌ ПОМИЛКА під час update_player:")
        print(traceback.format_exc())


def get_player(user_id):
    """Отримує дані гравця з Supabase. Якщо гравця немає — створює його."""
    user_id = str(user_id)
    
    # Створюємо резервну копію даних на випадок аварії Supabase
    fallback_player = {
        "user_id": user_id,
        "level": 1,
        "xp_total": 0.0,
        "inventory": [],
        "spheres": DEFAULT_SPHERES,
        "quests": DEFAULT_QUESTS
    }

    try:
        print(f"🔍 Запит до Supabase для user_id: {user_id}")
        response = supabase.table("players").select("*").eq("user_id", user_id).execute()
        
        # 🟢 1. ІСНУЮЧИЙ ГРАВЕЦЬ
        if response.data and len(response.data) > 0:
            player = response.data[0]
            print(f"📖 Знайдено існуючого гравця {user_id}")
            
            updated = False
            if "quests" not in player or player["quests"] is None:
                player["quests"] = DEFAULT_QUESTS
                updated = True
            elif isinstance(player["quests"], dict):
                for key in ["scrolls", "rituals", "plants"]:
                    if key not in player["quests"]:
                        player["quests"][key] = []
                        updated = True
            
            if updated:
                update_player(user_id, player)
            return player
        
        # 🟡 2. НОВИЙ ГРАВЕЦЬ (Створення запису)
        print(f"🆕 Створюємо нового гравця для user_id: {user_id}...")
        new_player = {
            "user_id": user_id,
            "level": 1,
            "xp_total": 0.0,
            "inventory": [],
            "spheres": DEFAULT_SPHERES,
            "quests": DEFAULT_QUESTS
        }
        
        supabase.table("players").insert(new_player).execute()
        print(f"✨ Нового гравця успішно створено в Supabase!")
        return new_player

    except Exception:
        print("❌ ПОМИЛКА ВСЕРЕДИНІ GET_PLAYER:")
        print(traceback.format_exc())
        # Повертаємо безпечний дефолтний об'єкт, щоб бот не впав
        return fallback_player
