from .calculations import (
    calculate_penalty,
    get_spheres,
    get_title,
    subtract_xp,
)
from .config import SPHERE_NAMES, parse_date
from .rituals import ritual_is_for_date, ritual_was_completed


def process_missed_scrolls(player, current_date, penalties_by_sphere):
    scrolls = player.get("scrolls") or []
    remaining_scrolls = []
    missed = []

    for scroll in scrolls:
        deadline = parse_date(scroll.get("deadline"))

        if deadline is None or deadline >= current_date:
            remaining_scrolls.append(scroll)
            continue

        penalty = calculate_penalty(scroll)
        spheres = get_spheres(scroll)

        subtract_xp(player, penalty, spheres)
        _add_penalty_to_spheres(
            penalties_by_sphere,
            penalty,
            spheres,
        )

        missed.append({
            "type": "scroll",
            "item": scroll,
            "penalty": penalty,
        })

    player["scrolls"] = remaining_scrolls

    return missed


def process_missed_plants(player, current_date, penalties_by_sphere):
    plants = player.get("plants") or []
    remaining_plants = []
    missed = []

    for plant in plants:
        deadline = parse_date(plant.get("deadline"))

        if deadline is None or deadline >= current_date:
            remaining_plants.append(plant)
            continue

        penalty = calculate_penalty(plant)
        spheres = get_spheres(plant)

        subtract_xp(player, penalty, spheres)
        _add_penalty_to_spheres(
            penalties_by_sphere,
            penalty,
            spheres,
        )

        missed.append({
            "type": "plant",
            "item": plant,
            "penalty": penalty,
        })

    player["plants"] = remaining_plants

    return missed


def process_missed_rituals(player, previous_date, penalties_by_sphere):
    rituals = player.get("rituals") or []
    missed = []

    for ritual in rituals:
        if not ritual_is_for_date(ritual, previous_date):
            continue

        if ritual_was_completed(ritual, previous_date):
            continue

        penalty = calculate_penalty(ritual)
        spheres = get_spheres(ritual)

        subtract_xp(player, penalty, spheres)
        _add_penalty_to_spheres(
            penalties_by_sphere,
            penalty,
            spheres,
        )

        missed.append({
            "type": "ritual",
            "item": ritual,
            "penalty": penalty,
        })

    return missed


def _add_penalty_to_spheres(
    penalties_by_sphere,
    penalty,
    spheres,
):
    if not spheres:
        return

    share = penalty / len(spheres)

    for sphere in spheres:
        if sphere in penalties_by_sphere:
            penalties_by_sphere[sphere] += share


def empty_penalties():
    return {
        key: 0.0
        for key in SPHERE_NAMES
    }

