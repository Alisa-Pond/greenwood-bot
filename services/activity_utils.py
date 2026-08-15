from datetime import datetime

SPHERE_NAMES = {
    "health": "💪",
    "wisdom": "🧠",
    "art": "🎨",
    "finance": "💵",
    "relations": "🤝",
}


def get_sphere_emoji(sphere):
    if sphere in SPHERE_NAMES:
        return SPHERE_NAMES[sphere]
    if sphere in SPHERE_NAMES.values():
        return sphere
    return sphere


def get_spheres(item):
    spheres = item.get("spheres") or item.get("sphere")
    if not spheres:
        return []

    if isinstance(spheres, str):
        result = []
        for sphere_key, emoji in SPHERE_NAMES.items():
            if sphere_key == spheres or emoji in spheres:
                result.append(emoji)
        return result or [spheres]

    if isinstance(spheres, list):
        result = []
        for sphere in spheres:
            if isinstance(sphere, dict):
                emoji = sphere.get("emoji")
                if emoji:
                    result.append(emoji)
                elif sphere.get("name"):
                    result.append(sphere["name"])
            else:
                result.append(get_sphere_emoji(sphere))
        return list(dict.fromkeys(result))

    return []


def get_title(item):
    return item.get("title") or item.get("name") or item.get("task") or "Без назви"


def get_xp(item):
    try:
        return float(item.get("xp") or item.get("points") or item.get("reward_xp") or 0)
    except (TypeError, ValueError):
        return 0.0


def get_today():
    return datetime.now().strftime("%d.%m.%Y")


def parse_deadline(deadline):
    if not deadline:
        return None
    value = str(deadline).strip()
    for fmt in ("%d.%m.%y", "%d.%m.%Y"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def is_overdue(item):
    deadline = parse_deadline(item.get("deadline"))
    if not deadline:
        return False
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    return today > deadline


def get_penalty_xp(item):
    for field in ("penalty", "penalty_xp", "overdue_penalty"):
        value = item.get(field)
        if value is not None:
            try:
                return abs(float(value))
            except (TypeError, ValueError):
                pass
    return 0.0


def add_xp_to_spheres(player, spheres, total_xp):
    if not spheres or total_xp <= 0:
        return

    player_spheres = player.get("spheres") or {}
    share = total_xp / len(spheres)

    for sphere in spheres:
        sphere_key = None
        for key, emoji in SPHERE_NAMES.items():
            if sphere == key or sphere == emoji:
                sphere_key = key
                break

        if sphere in player_spheres:
            sphere_key = sphere

        if not sphere_key or sphere_key not in player_spheres:
            continue

        data = player_spheres[sphere_key]
        data["xp"] = float(data.get("xp", 0)) + share

        while data["xp"] >= float(data.get("max_xp", 10)):
            max_xp = float(data.get("max_xp", 10))
            data["xp"] -= max_xp
            data["lvl"] = int(data.get("lvl", 1)) + 1
            data["max_xp"] = max_xp * 1.5


def add_total_xp(player, xp):
    player["xp_total"] = float(player.get("xp_total", 0)) + xp


def update_statistics(player, completed_scrolls=0, completed_rituals=0, plants_harvested=0, expeditions_completed=0):
    statistics = player.get("statistics") or {}
    if not isinstance(statistics, dict):
        statistics = {}

    for key, amount in {
        "completed_scrolls": completed_scrolls,
        "completed_rituals": completed_rituals,
        "plants_harvested": plants_harvested,
        "expeditions_completed": expeditions_completed,
    }.items():
        statistics[key] = int(statistics.get(key, 0)) + amount

    statistics.setdefault("last_summary_date", None)
    player["statistics"] = statistics


def build_back_button():
    from telebot import types
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(types.KeyboardButton("🔙 Назад"))
    return markup

