import traceback
from services.config import supabase

def clean_skin_tones(text_to_clean):
    """Очищає емодзі від відтінків шкіри, зводячи до стандартного жовтого."""
    if not text_to_clean:
        return ""
    
    replacements = {
        "💪🏻": "💪", "💪🏼": "💪", "💪🏽": "💪", "💪🏾": "💪", "💪🏿": "💪",
        "🤝🏻": "🤝", "🤝🏼": "🤝", "🤝🏽": "🤝", "🤝🏾": "🤝", "🤝🏿": "🤝"
    }
    
    for tone, base in replacements.items():
        text_to_clean = text_to_clean.replace(tone, base)
        
    return text_to_clean

def update_player(user_id, player_data):
    """Оновлює дані гравця в базі Supabase."""
    try:
        user_id = str(user_id)
        # Видаляємо id з оновлення, якщо воно там є, щоб Supabase не лаявся
        data_to_update = {k: v for k, v in player_data.items() if k != 'id'}
        supabase.table("players").update(data_to_update).eq("user_id", user_id).execute()
        print(f"✅ Дані гравця {user_id} оновлено в Supabase.")
    except Exception as e:
        print(f"❌ ПОМИЛКА під час update_player:")
        print(traceback.format_exc())

def get_player(user_id):
    """Отримує дані гравця з Supabase. Якщо гравця немає — створює його."""
    try:
        user_id = str(user_id)
        print(f"🔍 Запит до Supabase для user_id: {user_id}")
        response = supabase.table("players").select("*").eq("user_id", user_id).execute()
        
        default_quests = {
            "scrolls": [],    # Одноразові та накопичувальні сувої
            "rituals": [],    # Щоденні ритуали
            "plants": []      # Магічне насіння в Теплиці = цілі
        }
        
        # 🟢 1. ІСНУЮЧИЙ ГРАВЕЦЬ
        if response.data and len(response.data) > 0:
            player = response.data[0]
            print(f"📖 Знайдено існуючого гравця {user_id}")
            
            updated = False
            if "quests" not in player or player["quests"] is None:
                player["quests"] = default_quests
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
            "spheres": {
                "health": {"name": "💪 Здоров'я", "emoji": "💪", "lvl": 1, "xp": 0.0, "max_xp": 10.0},
                "wisdom": {"name": "🧠 Мудрість", "emoji": "🧠", "lvl": 1, "xp": 0.0, "max_xp": 10.0},
                "art": {"name": "🎨 Творчість", "emoji": "🎨", "lvl": 1, "xp": 0.0, "max_xp": 10.0},
                "finance": {"name": "💵 Фінанси", "emoji": "💵", "lvl": 1, "xp": 0.0, "max_xp": 10.0},
                "relations": {"name": "🤝 Зв'язки", "emoji": "🤝", "lvl": 1, "xp": 0.0, "max_xp": 10.0}
            },
            "quests": default_quests
        }
        
        insert_res = supabase.table("players").insert(new_player).execute()
        print(f"✨ Запис нового гравця створено в Supabase: {insert_res}")
        return new_player

    except Exception as e:
        print("❌ ПОМИЛКА ВСЕРЕДИНІ GET_PLAYER:")
        print(traceback.format_exc())
        # Повертаємо хоча б дефолтного гравця в пам'яті, щоб бот не падав
        return new_player
