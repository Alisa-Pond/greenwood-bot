from config import supabase

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
    user_id = str(user_id)
    supabase.table("players").update(player_data).eq("user_id", user_id).execute()

def get_player(user_id):
    """Отримує дані гравця з Supabase. Якщо гравця немає — створює його."""
    user_id = str(user_id)
    response = supabase.table("players").select("*").eq("user_id", user_id).execute()
    
    default_quests = {
        "scrolls": [],    # Одноразові та накопичувальні сувої
        "rituals": [],    # Щоденні ритуали
        "plants": []      # Магічне насіння в Теплиці = цілі
    }
    
    if response.data and len(response.data) > 0:
        player = response.data[0]
        updated = False
        if "quests" not in player:
            player["quests"] = default_quests
            updated = True
        else:
            for key in ["scrolls", "rituals", "plants"]:
                if key not in player["quests"]:
                    player["quests"][key] = []
                    updated = True
        if updated:
            update_player(user_id, player)
        return player
    
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
    
    supabase.table("players").insert(new_player).execute()
    return new_player
