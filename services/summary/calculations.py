from .config import SPHERE_NAMES


def get_spheres(item):
    spheres = item.get("spheres")

    if not spheres:
        spheres = item.get("sphere")

    if not spheres:
        return []

    result = []

    if isinstance(spheres, str):
        for key, emoji in SPHERE_NAMES.items():
            if spheres == key or emoji in spheres:
                result.append(key)
        return result

    if isinstance(spheres, list):
        for sphere in spheres:
            if isinstance(sphere, dict):
                key = sphere.get("key")
                emoji = sphere.get("emoji")

                if key and key in SPHERE_NAMES:
                    result.append(key)
                elif emoji:
                    for sphere_key, sphere_emoji in SPHERE_NAMES.items():
                        if emoji == sphere_emoji:
                            result.append(sphere_key)
                            break

            elif sphere in SPHERE_NAMES:
                result.append(sphere)

            elif sphere in SPHERE_NAMES.values():
                for key, emoji in SPHERE_NAMES.items():
                    if sphere == emoji:
                        result.append(key)
                        break

    return list(dict.fromkeys(result))


def get_title(item):
    return (
        item.get("title")
        or item.get("name")
        or item.get("task")
        or "Без назви"
    )


def get_xp(item):
    try:
        return float(
            item.get("xp")
            or item.get("points")
            or item.get("reward_xp")
            or 0
        )
    except (TypeError, ValueError):
        return 0.0


def calculate_penalty(item):
    """
    Штраф за пропущену справу.
    За замовчуванням: 2/3 від XP.
    """

    try:
        penalty_value = item.get("penalty")

        if penalty_value is None:
            penalty_value = item.get("penalty_xp")

        if penalty_value is None:
            penalty_value = item.get("penalty_points")

        if penalty_value is not None:
            return max(0.0, float(penalty_value))

    except (TypeError, ValueError):
        pass

    return get_xp(item) * (2 / 3)


def subtract_xp(player, total_xp, spheres):
    if total_xp <= 0:
        return

    player["xp_total"] = max(
        0.0,
        float(player.get("xp_total", 0)) - total_xp,
    )

    player_spheres = player.get("spheres") or {}

    if not spheres:
        return

    share = total_xp / len(spheres)

    for sphere in spheres:
        if sphere not in player_spheres:
            continue

        sphere_data = player_spheres[sphere]

        current_xp = float(
            sphere_data.get("xp", 0)
        )

        sphere_data["xp"] = max(
            0.0,
            current_xp - share,
        )


def update_statistics(player, key, amount=1):
    statistics = player.get("statistics") or {}

    if not isinstance(statistics, dict):
        statistics = {}

    statistics[key] = (
        int(statistics.get(key, 0)) + amount
    )

    player["statistics"] = statistics

